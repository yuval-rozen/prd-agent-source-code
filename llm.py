"""Model factory (Anthropic or Google), response cache, cost control, retry, structured output (SPEC §4, §11).

Response cache: the key is the SHA-256 of {provider, exact request} (Anthropic: the Messages API payload;
Google: the GenerateContentRequest). It covers single structured calls and every tool-calling step of the
critic agent alike, and contains no secrets. `--replay` serves every call from .cache/llm/ and fails
loudly on a cache miss instead of calling the API.

No sampling parameters are sent (Anthropic rejects them; for Google the library's temperature default is
removed). Structured output always uses the provider's native JSON-schema mode, never tool calls.

Cost control: every live call's usage is priced (config.PRICING; free-tier Gemini = $0) and added to a
per-run CostTracker. No call starts once the run has spent MAX_RUN_COST_USD, and the run aborts as soon
as a response pushes the total over it. Paid responses are cached before the abort.

Anthropic only: prompt caching (system-prompt breakpoint + automatic top-level caching) and reasoning
effort. Google: neither is sent (no clear equivalent is enabled; context caching is not used).
Google free tier: one call at a time by default, and 429s are retried after the delay the API returns.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import threading
import time
from pathlib import Path
from typing import Any, TypeVar

from langchain_anthropic import ChatAnthropic
from langchain_core.exceptions import OutputParserException
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, message_to_dict, messages_from_dict
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, PrivateAttr, SecretStr, ValidationError
from tenacity import RetryError, retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from config import PRICING, Provider, Role, Settings

log = logging.getLogger("prd_agent.llm")

DEFAULT_CACHE_DIR = Path(".cache/llm")
MAX_TOKENS = 16000
EPHEMERAL = {"type": "ephemeral"}
_REPLAY_PLACEHOLDER_KEY = SecretStr("replay-mode-no-key")
RATE_LIMIT_RETRIES = 5
RATE_LIMIT_MAX_WAIT_S = 120.0
REQUEST_TIMEOUT_S = 180.0  # per request; a hung call is cut off and retried instead of blocking for 10 min
SERVER_ERROR_RETRIES = 2  # HTTP 503 / 504 / timeout
SERVER_ERROR_BACKOFF_S = (15.0, 45.0)

T = TypeVar("T", bound=BaseModel)


class LLMError(Exception):
    """An LLM call failed (API error, refusal, unparseable output, or a replay cache miss)."""


class CacheMiss(LLMError):
    pass


class BudgetExceeded(LLMError):
    pass


class QuotaExhausted(LLMError):
    pass


# --------------------------------------------------------------------------- cost


def usage_cost(model: str, usage: dict) -> float:
    """USD cost of one response, from a normalized usage block (Anthropic field names)."""
    price = PRICING[model]
    uncached = usage.get("input_tokens") or 0
    read = usage.get("cache_read_input_tokens") or 0
    write = usage.get("cache_creation_input_tokens") or 0
    output = usage.get("output_tokens") or 0
    inp, out, read_p, write_p = price.input, price.output, price.cache_read, price.cache_write
    if price.long_prompt_threshold and uncached + read + write > price.long_prompt_threshold:
        scale = (price.long_input or inp) / inp
        inp, out = price.long_input or inp, price.long_output or out
        read_p, write_p = read_p * scale, write_p * scale
    return (uncached * inp + read * read_p + write * write_p + output * out) / 1_000_000


class CostTracker:
    """Thread-safe running total of what this run has spent on live API calls."""

    def __init__(self, limit_usd: float):
        self.limit_usd = limit_usd
        self.spent_usd = 0.0
        self.live_calls = 0
        self.rate_limit_waits = 0
        self.server_retries = 0
        self.tokens = {"input": 0, "cache_read": 0, "cache_write": 0, "output": 0}
        self.stage: str = "unknown"  # set by the graph before each stage runs (stages run one at a time)
        self.by_stage: dict[str, dict] = {}
        self.by_role: dict[str, dict] = {}
        self._lock = threading.Lock()

    def check_before_call(self) -> None:
        with self._lock:
            if self.spent_usd >= self.limit_usd and self.live_calls:
                raise BudgetExceeded(self._message())
            if self.limit_usd == 0 and self.spent_usd > 0:
                raise BudgetExceeded(self._message())

    def record(self, model: str, usage: dict, role: str | None = None) -> float:
        cost = usage_cost(model, usage)
        with self._lock:
            self.spent_usd += cost
            self.live_calls += 1
            for bucket, name in ((self.by_stage, self.stage), (self.by_role, role or "unknown")):
                entry = bucket.setdefault(name, {"cost_usd": 0.0, "calls": 0, "models": []})
                entry["cost_usd"] += cost
                entry["calls"] += 1
                if model not in entry["models"]:
                    entry["models"].append(model)
            self.tokens["input"] += usage.get("input_tokens") or 0
            self.tokens["cache_read"] += usage.get("cache_read_input_tokens") or 0
            self.tokens["cache_write"] += usage.get("cache_creation_input_tokens") or 0
            self.tokens["output"] += usage.get("output_tokens") or 0
            exceeded = self.spent_usd > self.limit_usd
        if exceeded:
            raise BudgetExceeded(self._message())
        return cost

    def _message(self) -> str:
        return (
            f"Run cost ${self.spent_usd:.4f} reached MAX_RUN_COST_USD=${self.limit_usd:.2f} after "
            f"{self.live_calls} API calls; aborting. Responses paid for so far are cached, so re-running "
            "(with a higher MAX_RUN_COST_USD if needed) does not pay for them again."
        )

    def summary(self) -> str:
        t = self.tokens
        waits = f" · {self.rate_limit_waits} rate-limit waits" if self.rate_limit_waits else ""
        waits += f" · {self.server_retries} 503/504/timeout retries" if self.server_retries else ""
        return (
            f"${self.spent_usd:.4f} of ${self.limit_usd:.2f} budget · {self.live_calls} API calls{waits} · tokens: "
            f"{t['input']} in, {t['cache_read']} cache read, {t['cache_write']} cache write, {t['output']} out"
        )


# --------------------------------------------------------------------------- response cache


def _canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"), default=str)


class ResponseCache:
    """One JSON file per request hash. Thread-safe for parallel stage calls."""

    def __init__(self, directory: Path = DEFAULT_CACHE_DIR):
        self.directory = Path(directory)
        self._lock = threading.Lock()
        self.hits = 0
        self.misses = 0

    @staticmethod
    def key(payload: dict) -> str:
        return hashlib.sha256(_canonical(payload).encode("utf-8")).hexdigest()

    def _path(self, key: str) -> Path:
        return self.directory / f"{key}.json"

    def get(self, key: str) -> ChatResult | None:
        path = self._path(key)
        if not path.is_file():
            with self._lock:
                self.misses += 1
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        with self._lock:
            self.hits += 1
        messages = messages_from_dict(data["messages"])
        return ChatResult(
            generations=[ChatGeneration(message=m) for m in messages], llm_output=data.get("llm_output") or {}
        )

    def put(self, key: str, payload: dict, result: ChatResult) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)
        data = {
            "provider": payload.get("provider"),
            "model": payload.get("model"),
            "messages": [message_to_dict(g.message) for g in result.generations],
            "llm_output": json.loads(_canonical(result.llm_output or {})),
        }
        tmp = self._path(key).with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=1, ensure_ascii=False, sort_keys=True), encoding="utf-8")
        tmp.replace(self._path(key))


def _stop_reason(result: ChatResult) -> str | None:
    llm_output = result.llm_output or {}
    if llm_output.get("stop_reason"):
        return llm_output["stop_reason"]
    for gen in result.generations:
        meta = {**(gen.generation_info or {}), **gen.message.response_metadata}
        if meta.get("finish_reason"):
            return str(meta["finish_reason"])
    return None


def _with_stop_reason(result: ChatResult) -> ChatResult:
    """Expose a normalized stop_reason on the message so refusals / truncation are detected uniformly."""
    reason = _stop_reason(result)
    if reason:
        for gen in result.generations:
            gen.message.response_metadata.setdefault("stop_reason", reason)
    return result


class _CachingMixin:
    """Shared by both providers: response cache, replay, cost tracking. Subclasses provide the hooks."""

    provider: Provider

    def configure_cache(self, cache: ResponseCache, replay: bool, costs: CostTracker | None = None,
                        role: str | None = None):
        self._cache = cache
        self._replay = replay
        self._costs = costs
        self._role = role
        return self

    # hooks -------------------------------------------------------------------
    def _cache_payload(self, messages: list[BaseMessage], stop, **kwargs: Any) -> dict:  # pragma: no cover
        raise NotImplementedError

    def _normalized_usage(self, result: ChatResult) -> dict:  # pragma: no cover
        raise NotImplementedError

    def _live_generate(self, messages, stop, run_manager, **kwargs: Any) -> ChatResult:
        return super()._generate(messages, stop=stop, run_manager=run_manager, **kwargs)  # type: ignore[misc]

    # shared ------------------------------------------------------------------
    def _generate(self, messages: list[BaseMessage], stop=None, run_manager=None, **kwargs: Any) -> ChatResult:
        payload = self._cache_payload(messages, stop, **kwargs)
        key = ResponseCache.key(payload)
        cached = self._cache.get(key)
        if cached is not None:
            log.debug("cache hit %s", key[:12])
            return _with_stop_reason(cached)
        if self._replay:
            raise CacheMiss(
                f"--replay: no cached response for this request (key {key[:12]}). "
                "The PRD, prompts, schemas, provider or model changed since the cache was recorded."
            )
        if self._costs is not None:
            self._costs.check_before_call()
        log.debug("cache miss %s -> calling %s/%s", key[:12], self.provider, self.model)
        result = self._live_generate(messages, stop, run_manager, **kwargs)
        self._cache.put(key, payload, result)  # cache first: a paid response is never lost
        if self._costs is not None:
            cost = self._costs.record(self.model.removeprefix("models/"), self._normalized_usage(result), self._role)
            log.debug("call cost $%.5f (%s)", cost, self.model)
        return _with_stop_reason(result)

    async def _agenerate(self, *args: Any, **kwargs: Any) -> ChatResult:  # pragma: no cover - sync only
        raise NotImplementedError("The pipeline uses synchronous calls only (cached path).")


def _has_block_breakpoint(messages: Any) -> bool:
    for message in messages if isinstance(messages, list) else []:
        content = getattr(message, "content", None)
        if isinstance(content, list) and any(isinstance(b, dict) and "cache_control" in b for b in content):
            return True
    return False


class CachedChatAnthropic(_CachingMixin, ChatAnthropic):
    """ChatAnthropic with prompt-caching breakpoints, response cache, replay and cost tracking."""

    provider: Provider = "anthropic"
    _cache: ResponseCache = PrivateAttr()
    _replay: bool = PrivateAttr(default=False)
    _costs: CostTracker | None = PrivateAttr(default=None)
    _role: str | None = PrivateAttr(default=None)

    def _get_request_payload(self, input_, *, stop=None, **kwargs: Any) -> dict:
        """Add prompt-caching breakpoints to every request: the system prompt, plus automatic top-level caching.
        A request whose user content already carries its own breakpoint (the critic marks the end of the stable
        PRD part) skips the automatic one, so the volatile tail (the plan) is not written to the cache."""
        if not _has_block_breakpoint(input_):
            kwargs.setdefault("cache_control", EPHEMERAL)
        payload = super()._get_request_payload(input_, stop=stop, **kwargs)
        system = payload.get("system")
        if isinstance(system, str) and system:
            payload["system"] = [{"type": "text", "text": system, "cache_control": EPHEMERAL}]
        elif isinstance(system, list) and system and not any(isinstance(b, dict) and "cache_control" in b for b in system):
            if isinstance(system[-1], dict):
                system[-1] = {**system[-1], "cache_control": EPHEMERAL}
        return payload

    def _cache_payload(self, messages, stop, **kwargs: Any) -> dict:
        return {"provider": "anthropic", "model": self.model, "request": self._get_request_payload(messages, stop=stop, **kwargs)}

    def _normalized_usage(self, result: ChatResult) -> dict:
        return (result.llm_output or {}).get("usage") or {}


def _retry_delay_seconds(exc: BaseException) -> float | None:
    """The delay a 429 asks for: google.rpc.RetryInfo in the error details, or 'retry in Ns' in the text."""
    for detail in getattr(exc, "details", None) or []:
        delay = getattr(detail, "retry_delay", None)
        if delay is not None:
            seconds = getattr(delay, "seconds", None)
            if seconds is not None:
                return float(seconds) + float(getattr(delay, "nanos", 0) or 0) / 1e9
            if hasattr(delay, "total_seconds"):
                return float(delay.total_seconds())
    match = re.search(r"retry(?:Delay)?[^0-9]{0,20}([0-9]+(?:\.[0-9]+)?)\s*s", str(exc), re.IGNORECASE)
    return float(match.group(1)) if match else None


def _is_daily_quota(exc: BaseException) -> bool:
    return bool(re.search(r"per\s*day|PerDay|RequestsPerDay", str(exc)))


def _unwrap(exc: BaseException) -> BaseException:
    if isinstance(exc, RetryError) and exc.last_attempt is not None and exc.last_attempt.exception() is not None:
        return exc.last_attempt.exception()
    return exc


def _status_code(exc: BaseException) -> int | None:
    for candidate in (exc, getattr(exc, "__cause__", None)):
        code = getattr(candidate, "code", None)
        if isinstance(code, int):
            return code
    return None


def _is_rate_limit(exc: BaseException) -> bool:
    name = type(exc).__name__
    return (
        _status_code(exc) == 429
        or name in {"ResourceExhausted", "TooManyRequests", "GoogleRateLimitError"}
        or "429" in str(exc)[:200]
    )


def _is_server_timeout(exc: BaseException) -> bool:
    """HTTP 503 / 504, or the client-side request timeout (httpx / google-api-core deadline)."""
    name = type(exc).__name__
    head = str(exc)[:200]
    return (
        _status_code(exc) in (503, 504)
        or name in {"DeadlineExceeded", "ServiceUnavailable", "GatewayTimeout", "ReadTimeout", "ConnectTimeout",
                    "WriteTimeout", "PoolTimeout", "TimeoutException"}
        or head.startswith(("503", "504"))
    )


def _jsonable(obj: Any) -> Any:
    """Turn a google-genai request (pydantic types, enums, bytes) into plain JSON data for the cache key."""
    if isinstance(obj, BaseModel):
        return _jsonable(obj.model_dump(mode="json", exclude_none=True))
    if isinstance(obj, dict):
        return {str(k): _jsonable(v) for k, v in obj.items() if v is not None}
    if isinstance(obj, (list, tuple)):
        return [_jsonable(v) for v in obj]
    if isinstance(obj, bytes):
        return hashlib.sha256(obj).hexdigest()
    if hasattr(obj, "value") and not isinstance(obj, (str, int, float, bool)):
        return obj.value
    return obj


class CachedChatGoogle(_CachingMixin, ChatGoogleGenerativeAI):
    """ChatGoogleGenerativeAI with response cache, replay, cost tracking and RetryInfo-aware 429 handling."""

    provider: Provider = "google"
    temperature: float | None = None  # do not send the library's 0.7 default: no sampling parameters
    _cache: ResponseCache = PrivateAttr()
    _replay: bool = PrivateAttr(default=False)
    _costs: CostTracker | None = PrivateAttr(default=None)
    _role: str | None = PrivateAttr(default=None)

    def _cache_payload(self, messages, stop, **kwargs: Any) -> dict:
        kwargs = {k: v for k, v in kwargs.items() if not k.startswith("ls_")}  # LangChain tracing metadata
        request = self._prepare_request(messages, stop=stop, **kwargs)
        request = {k: v for k, v in request.items() if k != "config" or v is not None}
        if request.get("config") is not None:  # http_options (timeout / retries) do not change the response
            request["config"] = request["config"].model_copy(update={"http_options": None})
        return {"provider": "google", "model": self.model, "request": _jsonable(request)}

    def _normalized_usage(self, result: ChatResult) -> dict:
        usage = getattr(result.generations[0].message, "usage_metadata", None) or {}
        cache_read = ((usage.get("input_token_details") or {}).get("cache_read")) or 0
        return {
            "input_tokens": max((usage.get("input_tokens") or 0) - cache_read, 0),
            "cache_read_input_tokens": cache_read,
            "output_tokens": usage.get("output_tokens") or 0,
        }

    def _live_generate(self, messages, stop, run_manager, **kwargs: Any) -> ChatResult:
        server_retries = 0
        for attempt in range(RATE_LIMIT_RETRIES + 1):
            try:
                return super()._live_generate(messages, stop, run_manager, **kwargs)
            except Exception as raw:  # noqa: BLE001 - classified below
                exc = _unwrap(raw)
                if _is_server_timeout(exc):
                    if server_retries >= SERVER_ERROR_RETRIES:
                        raise LLMError(
                            f"Gemini {self.model}: {type(exc).__name__} (HTTP {_status_code(exc) or 'timeout'}; "
                            f"503/504 or {REQUEST_TIMEOUT_S:.0f} s timeout) persisted after {server_retries} retries."
                        ) from None
                    wait = SERVER_ERROR_BACKOFF_S[server_retries]
                    server_retries += 1
                    log.warning("%s (HTTP %s) from %s; retrying in %.0fs (%d/%d)", type(exc).__name__,
                                _status_code(exc) or "timeout", self.model, wait, server_retries, SERVER_ERROR_RETRIES)
                    if self._costs is not None:
                        self._costs.server_retries += 1
                    time.sleep(wait)
                    continue
                if not _is_rate_limit(exc):
                    raise exc from raw
                if _is_daily_quota(exc):
                    raise QuotaExhausted(
                        f"Gemini free-tier daily quota for {self.model} is used up (HTTP 429, per-day limit). "
                        "Quotas reset at midnight Pacific time; responses obtained so far are cached."
                    ) from None
                if attempt == RATE_LIMIT_RETRIES:
                    raise LLMError(f"Gemini rate limit (HTTP 429) for {self.model} persisted after {attempt} retries.") from None
                delay = _retry_delay_seconds(exc)
                wait = min(delay if delay is not None else 10.0 * (attempt + 1), RATE_LIMIT_MAX_WAIT_S)
                log.warning("429 from %s; waiting %.1fs as the API asked (retry %d/%d)", self.model, wait, attempt + 1, RATE_LIMIT_RETRIES)
                if self._costs is not None:
                    self._costs.rate_limit_waits += 1
                time.sleep(wait)
        raise AssertionError("unreachable")  # pragma: no cover


# --------------------------------------------------------------------------- facade


class LLM:
    """Factory and helpers shared by all LLM stages."""

    def __init__(self, settings: Settings, *, replay: bool = False, cache_dir: Path = DEFAULT_CACHE_DIR):
        settings.require_models()
        self.settings = settings
        self.provider: Provider = settings.llm_provider
        self.replay = replay
        self.max_parallel = settings.parallel_calls
        self.cache = ResponseCache(cache_dir)
        self.cost = CostTracker(settings.max_run_cost_usd)
        self._api_key = _REPLAY_PLACEHOLDER_KEY if replay else settings.require_llm_key()

    def chat_model(self, role: Role = "generation") -> BaseChatModel:
        model = self.settings.model_for(role)
        if self.provider == "google":
            thinking = self.settings.google_thinking_level if role in ("generation", "critic") else None
            chat = CachedChatGoogle(
                model=model,
                temperature=None,  # explicit: otherwise the library forces 1.0 on Gemini 3 models
                google_api_key=self._api_key,
                max_output_tokens=MAX_TOKENS,
                thinking_level=thinking,  # None = the model's default
                max_retries=1,  # the library's own backoff is disabled; _live_generate handles 429 / 503 / 504
                timeout=REQUEST_TIMEOUT_S,
            )
        else:
            chat = CachedChatAnthropic(
                model=model,
                api_key=self._api_key,
                max_tokens=MAX_TOKENS,
                reasoning_effort=self.settings.effort_for(role),
                max_retries=4,  # the Anthropic SDK retries 408/409/429/5xx (incl. 503/504) and timeouts itself
                default_request_timeout=REQUEST_TIMEOUT_S,
            )
        return chat.configure_cache(self.cache, self.replay, self.cost, role)

    def structured(self, schema: type[T], system: str, user: str | list[dict], *, role: Role = "generation") -> T:
        """One structured call. Retries once with the validation error attached if the output is invalid.
        `user` may be a list of text blocks; a block with "cache_control" marks the end of a stable prefix
        (Anthropic only; for Google the blocks are joined into plain text)."""
        if isinstance(user, list) and self.provider != "anthropic":
            user = "".join(block["text"] for block in user)
        runnable = self.chat_model(role).with_structured_output(schema, method="json_schema", include_raw=True)
        messages: list[BaseMessage] = [SystemMessage(content=system), HumanMessage(content=user)]
        out = _invoke(runnable, messages)
        if out["parsed"] is not None:
            return out["parsed"]
        raw = out["raw"]
        _raise_if_refusal(raw)
        log.info("structured output for %s failed validation, retrying once with feedback", schema.__name__)
        messages += [
            raw if isinstance(raw, AIMessage) else AIMessage(content=str(raw)),
            HumanMessage(
                content="Your previous output did not validate against the schema:\n"
                f"{_short_error(out['parsing_error'])}\nReturn the complete corrected output."
            ),
        ]
        out = _invoke(runnable, messages)
        if out["parsed"] is not None:
            return out["parsed"]
        _raise_if_refusal(out["raw"])
        raise LLMError(f"{schema.__name__}: model output failed validation twice: {_short_error(out['parsing_error'])}")


def _short_error(error: BaseException | None) -> str:
    if error is None:
        return "unknown error"
    cause = error.__cause__ if isinstance(error, OutputParserException) and error.__cause__ else error
    if isinstance(cause, ValidationError):
        return "; ".join(f"{'.'.join(map(str, e['loc']))}: {e['msg']}" for e in cause.errors()[:20])
    return str(error).splitlines()[0][:500]


_REFUSALS = {"refusal", "SAFETY", "PROHIBITED_CONTENT", "BLOCKLIST", "SPII", "RECITATION"}
_TRUNCATED = {"max_tokens", "MAX_TOKENS"}


def _raise_if_refusal(raw: Any) -> None:
    meta = getattr(raw, "response_metadata", {}) or {}
    reason = str(meta.get("stop_reason") or meta.get("finish_reason") or "")
    if reason in _REFUSALS:
        raise LLMError(f"The model declined the request (stop reason {reason}).")
    if reason in _TRUNCATED:
        raise LLMError(f"The model output hit the output limit ({MAX_TOKENS} tokens); the response was truncated.")


@retry(
    retry=retry_if_exception_type(OSError),  # network hiccups below the SDKs' own retries
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, max=30),
    reraise=True,
)
def _invoke(runnable, messages: list[BaseMessage]) -> dict:
    try:
        return runnable.invoke(messages)
    except (LLMError, OSError):
        raise
    except Exception as exc:  # provider API errors; messages never contain the key
        raise LLMError(f"LLM call failed: {type(exc).__name__}: {str(exc).splitlines()[0][:300]}") from exc
