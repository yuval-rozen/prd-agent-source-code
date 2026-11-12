"""Configuration loaded from the environment / .env (SPEC §11).

Secrets are held as pydantic SecretStr so they never appear in repr(), logs, or error messages.
Keys are only *required* at the point where a stage needs them (see require_* helpers).
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field, SecretStr

# Defaults verified against the Anthropic model table (2026-11): Sonnet tier for generation,
# the stronger Opus tier for the critic. Both can be overridden via env.
DEFAULT_GENERATION_MODEL = "claude-sonnet-5-5"
DEFAULT_CRITIC_MODEL = "claude-opus-5-5"


class ConfigError(Exception):
    """Raised when required configuration is missing or invalid. Never contains secret values."""


class Settings(BaseModel):
    model_config = ConfigDict(frozen=True)

    anthropic_api_key: SecretStr | None = None
    github_token: SecretStr | None = None
    github_repo: str | None = None

    generation_model: str = DEFAULT_GENERATION_MODEL
    critic_model: str = DEFAULT_CRITIC_MODEL

    max_repair_rounds: int = Field(default=3, ge=1)
    grounding_threshold: float = Field(default=90.0, ge=0, le=100)
    duplicate_title_threshold: float = Field(default=90.0, ge=0, le=100)
    req_diff_threshold: float = Field(default=85.0, ge=0, le=100)

    def require_anthropic(self) -> SecretStr:
        if self.anthropic_api_key is None:
            raise ConfigError(
                "ANTHROPIC_API_KEY is not set. Add it to .env (see .env.example), "
                "or run with --replay to use the committed LLM cache."
            )
        return self.anthropic_api_key

    def require_github(self, repo_override: str | None = None) -> tuple[SecretStr, str]:
        if self.github_token is None:
            raise ConfigError(
                "GITHUB_TOKEN is not set. It is required only with --publish. "
                "Use a fine-grained token limited to the test repo with Issues read/write."
            )
        repo = repo_override or self.github_repo
        if not repo:
            raise ConfigError("No GitHub repo given. Pass --repo owner/name or set GITHUB_REPO.")
        if repo.count("/") != 1 or not all(repo.split("/")):
            raise ConfigError(f"Invalid repo {repo!r}: expected the form owner/name.")
        return self.github_token, repo


def _env(name: str) -> str | None:
    """Return the env value, treating empty / whitespace-only strings as unset."""
    value = os.environ.get(name)
    if value is None or not value.strip():
        return None
    return value.strip()


_FIELDS = {
    "anthropic_api_key": "ANTHROPIC_API_KEY",
    "github_token": "GITHUB_TOKEN",
    "github_repo": "GITHUB_REPO",
    "generation_model": "GENERATION_MODEL",
    "critic_model": "CRITIC_MODEL",
    "max_repair_rounds": "MAX_REPAIR_ROUNDS",
    "grounding_threshold": "GROUNDING_THRESHOLD",
    "duplicate_title_threshold": "DUPLICATE_TITLE_THRESHOLD",
    "req_diff_threshold": "REQ_DIFF_THRESHOLD",
}


def load_settings(env_file: str | Path | None = ".env") -> Settings:
    """Load settings from the process environment, after reading .env (which never overrides)."""
    if env_file is not None and Path(env_file).is_file():
        load_dotenv(env_file, override=False)
    values = {field: v for field, var in _FIELDS.items() if (v := _env(var)) is not None}
    try:
        return Settings(**values)
    except ValueError as exc:
        # Report which variables are bad without echoing their values.
        bad = sorted({_FIELDS.get(str(e["loc"][0]), str(e["loc"][0])) for e in exc.errors()})
        raise ConfigError(f"Invalid configuration value(s) for: {', '.join(bad)}") from None
