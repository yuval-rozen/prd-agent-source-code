"""LLM cache and request shape, without network: no sampling params, native structured output, replay."""

import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from pydantic import SecretStr

from config import Settings
from llm import LLM, CacheMiss, CachedChatAnthropic, ResponseCache
from schemas import RequirementDraftList


def _model(cache: ResponseCache, replay: bool) -> CachedChatAnthropic:
    return CachedChatAnthropic(model="claude-sonnet-5-5", api_key=SecretStr("sk-test"), max_tokens=100).configure_cache(cache, replay)


def _payload(model, messages, **kw):
    return model._get_request_payload(messages, **kw)


MESSAGES = [SystemMessage(content="sys"), HumanMessage(content="hello")]


def test_structured_request_uses_native_output_and_no_sampling(tmp_path):
    model = _model(ResponseCache(tmp_path), replay=True)
    bound = model.with_structured_output(RequirementDraftList, method="json_schema")
    binding = bound.first  # RunnableBinding carrying the request kwargs
    payload = _payload(model, MESSAGES, **binding.kwargs)
    assert payload["output_config"]["format"]["type"] == "json_schema"
    assert "tool_choice" not in payload and "tools" not in payload
    for param in ("temperature", "top_p", "top_k"):
        assert param not in payload


def test_cache_key_ignores_message_ids(tmp_path):
    model = _model(ResponseCache(tmp_path), replay=True)
    a = model._cache_payload([SystemMessage(content="sys"), HumanMessage(content="hello", id="uuid-1")], None)
    b = model._cache_payload([SystemMessage(content="sys"), HumanMessage(content="hello", id="uuid-2")], None)
    assert ResponseCache.key(a) == ResponseCache.key(b)
    c = model._cache_payload([SystemMessage(content="sys"), HumanMessage(content="hello!")], None)
    assert ResponseCache.key(a) != ResponseCache.key(c)


def test_replay_miss_raises(tmp_path):
    model = _model(ResponseCache(tmp_path), replay=True)
    with pytest.raises(CacheMiss, match="--replay"):
        model.invoke(MESSAGES)


def test_cache_hit_served_without_network(tmp_path):
    cache = ResponseCache(tmp_path)
    model = _model(cache, replay=True)
    payload = model._cache_payload(MESSAGES, None)
    key = ResponseCache.key(payload)
    stored = ChatResult(generations=[ChatGeneration(message=AIMessage(content="cached answer"))], llm_output={"model": "x"})
    cache.put(key, payload, stored)
    assert model.invoke(MESSAGES).content == "cached answer"
    assert cache.hits == 1
    assert "sk-test" not in (tmp_path / f"{key}.json").read_text(encoding="utf-8")


def test_live_call_populates_cache(tmp_path, monkeypatch):
    cache = ResponseCache(tmp_path)
    model = _model(cache, replay=False)
    calls = []

    def fake_generate(self, messages, stop=None, run_manager=None, **kw):
        calls.append(1)
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content="live"))])

    monkeypatch.setattr("langchain_anthropic.ChatAnthropic._generate", fake_generate)
    assert model.invoke(MESSAGES).content == "live"
    assert model.invoke(MESSAGES).content == "live"
    assert len(calls) == 1 and cache.hits == 1


def test_llm_requires_key_unless_replay():
    from config import ConfigError

    with pytest.raises(ConfigError, match="ANTHROPIC_API_KEY"):
        LLM(Settings())
    LLM(Settings(), replay=True)  # no key needed


def test_models_from_config():
    llm = LLM(Settings(extract_model="claude-haiku-5-5", generation_model="claude-opus-5-5",
                       critic_model="claude-sonnet-5-5"), replay=True)
    assert llm.chat_model("extract").model == "claude-haiku-5-5"
    assert llm.chat_model().model == "claude-opus-5-5"
    assert llm.chat_model("critic").model == "claude-sonnet-5-5"


# --------------------------------------------------------------------------- prompt caching, effort, cost

from config import PRICING  # noqa: E402
from llm import BudgetExceeded, CostTracker, usage_cost  # noqa: E402


def test_every_request_has_prompt_cache_breakpoints(tmp_path):
    model = _model(ResponseCache(tmp_path), replay=True)
    payload = _payload(model, MESSAGES)
    assert payload["cache_control"] == {"type": "ephemeral"}
    assert payload["system"][-1]["cache_control"] == {"type": "ephemeral"}
    assert payload["system"][-1]["text"] == "sys"


def test_effort_and_native_format_coexist(tmp_path):
    llm = LLM(Settings(), replay=True, cache_dir=tmp_path)
    model = llm.chat_model("extract")
    assert model.model == "claude-haiku-5-5"
    binding = model.with_structured_output(RequirementDraftList, method="json_schema").first
    payload = model._get_request_payload(MESSAGES, **binding.kwargs)
    assert payload["output_config"]["effort"] == "low"
    assert payload["output_config"]["format"]["type"] == "json_schema"


def test_usage_cost_prices_every_token_class():
    usage = {"input_tokens": 1_000_000, "cache_read_input_tokens": 1_000_000,
             "cache_creation_input_tokens": 1_000_000, "output_tokens": 1_000_000}
    p = PRICING["claude-sonnet-5-5"]
    assert usage_cost("claude-sonnet-5-5", usage) == pytest.approx(p.input + p.cache_read + p.cache_write + p.output)


def test_usage_cost_long_prompt_tier():
    small = usage_cost("claude-haiku-5-5", {"input_tokens": 50_000, "output_tokens": 1000})
    large = usage_cost("claude-haiku-5-5", {"input_tokens": 150_000, "output_tokens": 1000})
    assert small == pytest.approx((50_000 * 0.10 + 1000 * 0.50) / 1e6)
    assert large == pytest.approx((150_000 * 0.50 + 1000 * 2.50) / 1e6)


def test_budget_aborts_when_exceeded_and_blocks_new_calls():
    tracker = CostTracker(limit_usd=0.01)
    tracker.record("claude-sonnet-5-5", {"input_tokens": 1000, "output_tokens": 100})  # $0.003
    with pytest.raises(BudgetExceeded, match="MAX_RUN_COST_USD"):
        tracker.record("claude-sonnet-5-5", {"input_tokens": 1000, "output_tokens": 1000})  # total $0.015
    with pytest.raises(BudgetExceeded):
        tracker.check_before_call()
    assert tracker.live_calls == 2


def test_live_call_is_cached_before_budget_abort(tmp_path, monkeypatch):
    cache = ResponseCache(tmp_path)
    tracker = CostTracker(limit_usd=0.0001)
    model = _model(cache, replay=False)
    model.configure_cache(cache, False, tracker)

    def fake_generate(self, messages, stop=None, run_manager=None, **kw):
        return ChatResult(
            generations=[ChatGeneration(message=AIMessage(content="paid"))],
            llm_output={"usage": {"input_tokens": 1000, "output_tokens": 1000}},
        )

    monkeypatch.setattr("langchain_anthropic.ChatAnthropic._generate", fake_generate)
    with pytest.raises(BudgetExceeded):
        model.invoke(MESSAGES)
    assert len(list(tmp_path.glob("*.json"))) == 1  # the paid response was kept
    # Re-run with a fresh budget: served from cache, costs nothing.
    fresh = CostTracker(limit_usd=0.0001)
    model.configure_cache(cache, False, fresh)
    assert model.invoke(MESSAGES).content == "paid"
    assert fresh.spent_usd == 0 and fresh.live_calls == 0


def test_unknown_model_price_is_refused():
    from config import ConfigError

    with pytest.raises(ConfigError, match="pricing"):
        LLM(Settings(generation_model="claude-unknown-9"), replay=True)


def test_cost_shown_in_summary(tmp_path):
    tracker = CostTracker(limit_usd=0.5)
    tracker.record("claude-haiku-5-5", {"input_tokens": 10, "output_tokens": 5})
    assert "$0.50 budget" in tracker.summary() and "1 API calls" in tracker.summary()


# --------------------------------------------------------------------------- Google provider

from google.api_core.exceptions import ResourceExhausted  # noqa: E402
from langchain_core.messages import AIMessage as _AI  # noqa: E402

import llm as llm_module  # noqa: E402


def _google(tmp_path, role="generation", **settings):
    return LLM(Settings(llm_provider="google", **settings), replay=False if settings.get("google_api_key") else True,
               cache_dir=tmp_path).chat_model(role)


def test_google_request_is_native_schema_without_sampling(tmp_path):
    m = _google(tmp_path)
    binding = m.with_structured_output(RequirementDraftList, method="json_schema").first
    kwargs = {k: v for k, v in binding.kwargs.items() if not k.startswith("ls_")}
    config = m._prepare_request(MESSAGES, **kwargs)["config"]
    assert config.response_mime_type == "application/json" and config.response_json_schema
    assert config.temperature is None and config.top_p is None and config.top_k is None
    assert not config.tools  # not tool-based


def test_cache_key_includes_provider(tmp_path):
    a = _model(ResponseCache(tmp_path), replay=True)._cache_payload(MESSAGES, None)
    g = _google(tmp_path)._cache_payload(MESSAGES, None)
    assert a["provider"] == "anthropic" and g["provider"] == "google"
    assert ResponseCache.key(a) != ResponseCache.key(g)


def _fake_429(message: str):
    return ResourceExhausted(message)


def test_google_429_waits_for_api_delay_then_succeeds(tmp_path, monkeypatch):
    m = _google(tmp_path, google_api_key=SecretStr("fake"))
    attempts, sleeps = [], []

    def fake_generate(self, messages, stop=None, run_manager=None, **kw):
        attempts.append(1)
        if len(attempts) == 1:
            raise _fake_429('429 Quota exceeded for GenerateRequestsPerMinutePerProjectPerModel. Please retry in 7.5s.')
        msg = _AI(content="ok")
        msg.usage_metadata = {"input_tokens": 100, "output_tokens": 20, "total_tokens": 120}
        return ChatResult(generations=[ChatGeneration(message=msg)])

    monkeypatch.setattr("langchain_google_genai.ChatGoogleGenerativeAI._generate", fake_generate)
    monkeypatch.setattr(llm_module.time, "sleep", lambda s: sleeps.append(s))
    assert m.invoke(MESSAGES).content == "ok"
    assert sleeps == [7.5] and len(attempts) == 2
    assert m._costs.spent_usd == 0.0 and m._costs.live_calls == 1 and m._costs.tokens["input"] == 100


def test_google_daily_quota_fails_fast(tmp_path, monkeypatch):
    m = _google(tmp_path, google_api_key=SecretStr("fake"))
    sleeps = []

    def fake_generate(self, messages, stop=None, run_manager=None, **kw):
        raise _fake_429("429 Quota exceeded for metric GenerateRequestsPerDayPerProjectPerModel-FreeTier")

    monkeypatch.setattr("langchain_google_genai.ChatGoogleGenerativeAI._generate", fake_generate)
    monkeypatch.setattr(llm_module.time, "sleep", lambda s: sleeps.append(s))
    with pytest.raises(llm_module.QuotaExhausted, match="daily quota"):
        m.invoke(MESSAGES)
    assert sleeps == []


def test_retry_delay_parsing():
    assert llm_module._retry_delay_seconds(Exception('"retryDelay": "37s"')) == 37.0
    assert llm_module._retry_delay_seconds(Exception("Please retry in 2.25s.")) == 2.25
    assert llm_module._retry_delay_seconds(Exception("no hint")) is None


def test_free_tier_gemini_costs_nothing():
    assert usage_cost("gemini-3.8-flash", {"input_tokens": 10**6, "output_tokens": 10**6}) == 0.0


def test_google_504_is_retried_with_backoff(tmp_path, monkeypatch):
    from google.api_core.exceptions import DeadlineExceeded

    m = _google(tmp_path, google_api_key=SecretStr("fake"))
    attempts, sleeps = [], []

    def fake_generate(self, messages, stop=None, run_manager=None, **kw):
        attempts.append(1)
        if len(attempts) == 1:
            raise DeadlineExceeded("504 Deadline expired before operation could complete.")
        return ChatResult(generations=[ChatGeneration(message=_AI(content="ok"))])

    monkeypatch.setattr("langchain_google_genai.ChatGoogleGenerativeAI._generate", fake_generate)
    monkeypatch.setattr(llm_module.time, "sleep", lambda s: sleeps.append(s))
    assert m.invoke(MESSAGES).content == "ok"
    assert sleeps == [llm_module.SERVER_ERROR_BACKOFF_S[0]] and m._costs.server_retries == 1


def test_google_503_gives_up_after_retries(tmp_path, monkeypatch):
    from google.api_core.exceptions import ServiceUnavailable

    m = _google(tmp_path, google_api_key=SecretStr("fake"))
    monkeypatch.setattr("langchain_google_genai.ChatGoogleGenerativeAI._generate",
                        lambda self, *a, **k: (_ for _ in ()).throw(ServiceUnavailable("503 overloaded")))
    monkeypatch.setattr(llm_module.time, "sleep", lambda s: None)
    with pytest.raises(llm_module.LLMError, match="persisted after 2 retries"):
        m.invoke(MESSAGES)


def test_google_timeout_and_thinking_level(tmp_path):
    llm = LLM(Settings(llm_provider="google", google_thinking_level="low"), replay=True, cache_dir=tmp_path)
    gen, ext = llm.chat_model("generation"), llm.chat_model("extract")
    assert gen.timeout == llm_module.REQUEST_TIMEOUT_S == 180
    assert gen.thinking_level == "low" and ext.thinking_level is None  # extraction keeps the model default
    config = gen._prepare_request(MESSAGES)["config"]
    assert config.thinking_config.thinking_level.value.lower() == "low"
    assert config.http_options.timeout == 180_000 and config.http_options.retry_options.attempts == 1
    assert ext._prepare_request(MESSAGES)["config"].thinking_config is None


def test_google_sdk_errors_are_classified():
    from google.genai.errors import ClientError, ServerError

    rate = ClientError(429, {"error": {"code": 429, "message": "Quota exceeded. Please retry in 12s.", "status": "RESOURCE_EXHAUSTED"}})
    daily = ClientError(429, {"error": {"code": 429, "message": "Quota exceeded for metric GenerateRequestsPerDayPerProjectPerModel-FreeTier", "status": "RESOURCE_EXHAUSTED"}})
    gateway = ServerError(504, {"error": {"code": 504, "message": "Deadline expired", "status": "DEADLINE_EXCEEDED"}})
    unavailable = ServerError(503, {"error": {"code": 503, "message": "overloaded", "status": "UNAVAILABLE"}})
    assert llm_module._is_rate_limit(rate) and not llm_module._is_daily_quota(rate)
    assert llm_module._retry_delay_seconds(rate) == 12.0
    assert llm_module._is_daily_quota(daily)
    assert llm_module._is_server_timeout(gateway) and llm_module._is_server_timeout(unavailable)
    assert not llm_module._is_server_timeout(rate)
