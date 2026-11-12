import pytest

from config import DEFAULT_CRITIC_MODEL, DEFAULT_GENERATION_MODEL, ConfigError, load_settings

FAKE_KEY = "sk-test-not-a-real-key-123"


def test_defaults_without_env():
    s = load_settings(env_file=None)
    assert s.generation_model == DEFAULT_GENERATION_MODEL
    assert s.critic_model == DEFAULT_CRITIC_MODEL
    assert s.max_repair_rounds == 3
    assert s.anthropic_api_key is None


def test_empty_values_mean_defaults(monkeypatch):
    monkeypatch.setenv("GENERATION_MODEL", "")
    monkeypatch.setenv("MAX_REPAIR_ROUNDS", "  ")
    s = load_settings(env_file=None)
    assert s.generation_model == DEFAULT_GENERATION_MODEL
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
