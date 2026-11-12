import pytest

from config import DEFAULT_MODELS, ConfigError, load_settings

FAKE_KEY = "sk-test-not-a-real-key-123"


def test_defaults_without_env():
    s = load_settings(env_file=None)
    assert s.llm_provider == "anthropic"
    assert s.max_repair_rounds == 3
    assert s.anthropic_api_key is None
    assert s.models() == ["claude-haiku-5-5", "claude-sonnet-5-5", "claude-sonnet-5-5"]
    assert s.max_run_cost_usd == 0.50


def test_budget_and_models_from_env(monkeypatch):
    monkeypatch.setenv("MAX_RUN_COST_USD", "0.10")
    monkeypatch.setenv("EXTRACT_MODEL", "claude-sonnet-5-5")
    monkeypatch.setenv("CRITIC_EFFORT", "high")
    s = load_settings(env_file=None)
    assert s.max_run_cost_usd == 0.10 and s.model_for("extract") == "claude-sonnet-5-5"
    assert s.effort_for("critic") == "high"


def test_invalid_budget_and_effort_are_rejected(monkeypatch):
    monkeypatch.setenv("MAX_RUN_COST_USD", "-1")
    monkeypatch.setenv("GENERATION_EFFORT", "turbo")
    with pytest.raises(ConfigError) as info:
        load_settings(env_file=None)
    assert "MAX_RUN_COST_USD" in str(info.value) and "GENERATION_EFFORT" in str(info.value)


def test_empty_values_mean_defaults(monkeypatch):
    monkeypatch.setenv("GENERATION_MODEL", "")
    monkeypatch.setenv("MAX_REPAIR_ROUNDS", "  ")
    s = load_settings(env_file=None)
    assert s.model_for("generation") == DEFAULT_MODELS["anthropic"]["generation"]
    assert s.max_repair_rounds == 3


def test_env_overrides(monkeypatch):
    monkeypatch.setenv("CRITIC_MODEL", "some-model")
    monkeypatch.setenv("GROUNDING_THRESHOLD", "95")
    s = load_settings(env_file=None)
    assert s.critic_model == "some-model" and s.grounding_threshold == 95


def test_dotenv_file_is_read_and_does_not_override_env(monkeypatch, tmp_path):
    env = tmp_path / ".env"
    env.write_text("GITHUB_REPO=from/file\nCRITIC_MODEL=file-model\n", encoding="utf-8")
    monkeypatch.setenv("CRITIC_MODEL", "env-model")
    s = load_settings(env_file=env)
    assert s.github_repo == "from/file"
    assert s.critic_model == "env-model"
    monkeypatch.delenv("GITHUB_REPO")


def test_missing_anthropic_key():
    with pytest.raises(ConfigError, match="ANTHROPIC_API_KEY.*--replay"):
        load_settings(env_file=None).require_anthropic()


def test_missing_github_token():
    with pytest.raises(ConfigError, match="GITHUB_TOKEN"):
        load_settings(env_file=None).require_github("o/r")


def test_github_repo_required_and_validated(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", FAKE_KEY)
    s = load_settings(env_file=None)
    with pytest.raises(ConfigError, match="--repo"):
        s.require_github()
    with pytest.raises(ConfigError, match="owner/name"):
        s.require_github("not-a-repo")
    _, repo = s.require_github("owner/name")
    assert repo == "owner/name"


def test_secrets_never_in_repr_or_errors(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", FAKE_KEY)
    monkeypatch.setenv("GITHUB_TOKEN", FAKE_KEY)
    s = load_settings(env_file=None)
    assert FAKE_KEY not in repr(s) and FAKE_KEY not in str(s) and FAKE_KEY not in s.model_dump_json()
    assert s.require_anthropic().get_secret_value() == FAKE_KEY


def test_invalid_threshold_names_variable_not_value(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", FAKE_KEY)
    monkeypatch.setenv("GROUNDING_THRESHOLD", "250")
    with pytest.raises(ConfigError) as info:
        load_settings(env_file=None)
    assert "GROUNDING_THRESHOLD" in str(info.value)
    assert FAKE_KEY not in str(info.value) and "250" not in str(info.value)


# --------------------------------------------------------------------------- provider


def test_google_provider_defaults(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "Google")
    s = load_settings(env_file=None)
    assert s.llm_provider == "google"
    assert s.models() == ["gemini-3.5-flash-lite", "gemini-3.8-flash", "gemini-3.8-flash"]
    assert s.parallel_calls == 1
    s.require_models()


def test_unknown_provider_rejected(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    with pytest.raises(ConfigError, match="LLM_PROVIDER"):
        load_settings(env_file=None)


def test_model_of_other_provider_rejected(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "google")
    monkeypatch.setenv("EXTRACT_MODEL", "claude-haiku-5-5")
    with pytest.raises(ConfigError, match="another provider"):
        load_settings(env_file=None).require_models()


def test_billable_gemini_model_refused(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "google")
    monkeypatch.setenv("GENERATION_MODEL", "gemini-4-carbon")  # no free tier -> not in PRICING
    with pytest.raises(ConfigError, match="pricing"):
        load_settings(env_file=None).require_models()


def test_google_key_required_unless_replay(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "google")
    with pytest.raises(ConfigError, match="GOOGLE_API_KEY"):
        load_settings(env_file=None).require_llm_key()


def test_parallel_override(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "google")
    monkeypatch.setenv("MAX_PARALLEL_CALLS", "2")
    assert load_settings(env_file=None).parallel_calls == 2
