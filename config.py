"""Configuration loaded from the environment / .env (SPEC §11).

Secrets are held as pydantic SecretStr so they never appear in repr(), logs, or error messages.
Keys are only *required* at the point where a stage needs them (see require_* helpers).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field, SecretStr

Provider = Literal["anthropic", "google"]
Role = Literal["extract", "generation", "critic"]
Effort = Literal["low", "medium", "high", "xhigh", "max"]

DEFAULT_MAX_RUN_COST_USD = 0.50

# Per-provider, per-stage default models. EXTRACT_MODEL / GENERATION_MODEL / CRITIC_MODEL override them.
# Anthropic IDs verified against the Anthropic model table (2026-11-03). Google IDs verified against
# Google's model list and pricing page (2026-11-12): all three defaults are on the Gemini free tier.
DEFAULT_MODELS: dict[Provider, dict[Role, str]] = {
    "anthropic": {"extract": "claude-haiku-5-5", "generation": "claude-sonnet-5-5", "critic": "claude-sonnet-5-5"},
    "google": {"extract": "gemini-3.5-flash-lite", "generation": "gemini-3.8-flash", "critic": "gemini-3.8-flash"},
}
MODEL_PREFIX: dict[Provider, str] = {"anthropic": "claude-", "google": "gemini-"}

# Free-tier quotas are per Google Cloud project and are small (Google publishes the exact numbers only in
# AI Studio; third-party reports put gemini-3.8-flash at ~5 RPM / 20 RPD and Flash-Lite at ~10 RPM / 500 RPD).
DEFAULT_MAX_PARALLEL: dict[Provider, int] = {"anthropic": 4, "google": 1}


class ModelPrice(BaseModel):
    """USD per 1M tokens. cache_write is the 5-minute ephemeral write price (1.25x input)."""

    input: float
    output: float
    cache_read: float
    cache_write: float
    long_prompt_threshold: int | None = None  # prompts above this many tokens use the long_* prices
    long_input: float | None = None
    long_output: float | None = None
    free_tier: bool = False


_FREE = ModelPrice(input=0.0, output=0.0, cache_read=0.0, cache_write=0.0, free_tier=True)

# A model without an entry here is refused, because the run budget cannot be enforced for it.
PRICING: dict[str, ModelPrice] = {
    # Anthropic first-party prices (cached model table, 2026-11-03).
    "claude-haiku-5-5": ModelPrice(
        input=0.10, output=0.50, cache_read=0.01, cache_write=0.125,
        long_prompt_threshold=100_000, long_input=0.50, long_output=2.50,
    ),
    "claude-sonnet-5-5": ModelPrice(input=2.00, output=10.00, cache_read=0.10, cache_write=2.50),
    "claude-opus-5-5": ModelPrice(input=4.00, output=20.00, cache_read=0.20, cache_write=5.00),
    # Gemini models with a free tier (Google pricing page, 2026-11-12), priced at $0. Models without a free
    # tier (gemini-4-*, gemini-3.1-pro-preview) are deliberately absent, so they are refused.
    "gemini-3.8-flash": _FREE,
    "gemini-3.6-flash": _FREE,
    "gemini-3.5-flash-lite": _FREE,
    "gemini-3.1-flash-lite": _FREE,
}


class ConfigError(Exception):
    """Raised when required configuration is missing or invalid. Never contains secret values."""


class Settings(BaseModel):
    model_config = ConfigDict(frozen=True)

    llm_provider: Provider = "anthropic"
    anthropic_api_key: SecretStr | None = None
    google_api_key: SecretStr | None = None
    github_token: SecretStr | None = None
    github_repo: str | None = None

    # None = the provider's default for that stage (DEFAULT_MODELS).
    extract_model: str | None = None
    generation_model: str | None = None
    critic_model: str | None = None

    # Reasoning effort per role (Anthropic output_config.effort; not sent to Google). Thinking tokens are
    # billed as output, so these are the main cost lever after model choice.
    extract_effort: Effort = "low"
    generation_effort: Effort = "medium"
    critic_effort: Effort = "medium"

    # Gemini thinking level for the generation and critic stages (low | high; None = the model's default).
    # Not applied to extraction. Gemini only.
    google_thinking_level: Literal["minimal", "low", "medium", "high"] | None = None

    max_run_cost_usd: float = Field(default=DEFAULT_MAX_RUN_COST_USD, ge=0)
    max_parallel_calls: int | None = Field(default=None, ge=1)

    max_repair_rounds: int = Field(default=3, ge=1)
    grounding_threshold: float = Field(default=90.0, ge=0, le=100)
    duplicate_title_threshold: float = Field(default=90.0, ge=0, le=100)
    req_diff_threshold: float = Field(default=85.0, ge=0, le=100)

    def model_for(self, role: Role) -> str:
        explicit = {"extract": self.extract_model, "generation": self.generation_model, "critic": self.critic_model}[role]
        return explicit or DEFAULT_MODELS[self.llm_provider][role]

    def effort_for(self, role: Role) -> Effort:
        return {"extract": self.extract_effort, "generation": self.generation_effort, "critic": self.critic_effort}[role]

    @property
    def parallel_calls(self) -> int:
        return self.max_parallel_calls or DEFAULT_MAX_PARALLEL[self.llm_provider]

    def models(self) -> list[str]:
        return [self.model_for(r) for r in ("extract", "generation", "critic")]

    def require_models(self) -> None:
        """Every configured model must belong to the provider and have a price (or the cap is unenforceable)."""
        prefix = MODEL_PREFIX[self.llm_provider]
        wrong = sorted({m for m in self.models() if not m.startswith(prefix)})
        if wrong:
            raise ConfigError(
                f"LLM_PROVIDER={self.llm_provider} but model(s) {', '.join(wrong)} belong to another provider. "
                f"Set EXTRACT_MODEL / GENERATION_MODEL / CRITIC_MODEL to {prefix}* models, or leave them empty."
            )
        missing = sorted({m for m in self.models() if m not in PRICING})
        if missing:
            raise ConfigError(
                f"No pricing known for model(s) {', '.join(missing)}, so the run budget cannot be enforced. "
                f"Use one of: {', '.join(sorted(m for m in PRICING if m.startswith(prefix)))}, "
                "or add the model to PRICING in config.py."
            )

    require_pricing = require_models  # backwards-compatible name

    def require_llm_key(self) -> SecretStr:
        if self.llm_provider == "google":
            if self.google_api_key is None:
                raise ConfigError(
                    "GOOGLE_API_KEY is not set (LLM_PROVIDER=google). Add it to .env, "
                    "or run with --replay to use the committed LLM cache."
                )
            return self.google_api_key
        return self.require_anthropic()

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
    "llm_provider": "LLM_PROVIDER",
    "anthropic_api_key": "ANTHROPIC_API_KEY",
    "google_api_key": "GOOGLE_API_KEY",
    "github_token": "GITHUB_TOKEN",
    "github_repo": "GITHUB_REPO",
    "extract_model": "EXTRACT_MODEL",
    "generation_model": "GENERATION_MODEL",
    "critic_model": "CRITIC_MODEL",
    "extract_effort": "EXTRACT_EFFORT",
    "generation_effort": "GENERATION_EFFORT",
    "critic_effort": "CRITIC_EFFORT",
    "google_thinking_level": "GOOGLE_THINKING_LEVEL",
    "max_run_cost_usd": "MAX_RUN_COST_USD",
    "max_parallel_calls": "MAX_PARALLEL_CALLS",
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
    if "llm_provider" in values:
        values["llm_provider"] = values["llm_provider"].lower()
    try:
        return Settings(**values)
    except ValueError as exc:
        # Report which variables are bad without echoing their values.
        bad = sorted({_FIELDS.get(str(e["loc"][0]), str(e["loc"][0])) for e in exc.errors()})
        raise ConfigError(f"Invalid configuration value(s) for: {', '.join(bad)}") from None
