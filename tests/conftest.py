from pathlib import Path

import pytest

from tools.file_reader import SUPPORTED_SUFFIXES

ROOT = Path(__file__).resolve().parent.parent

ENV_VARS = (
    "LLM_PROVIDER", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY", "MAX_PARALLEL_CALLS", "GITHUB_TOKEN", "GITHUB_REPO", "EXTRACT_MODEL", "GENERATION_MODEL", "CRITIC_MODEL",
    "EXTRACT_EFFORT", "GENERATION_EFFORT", "CRITIC_EFFORT", "MAX_RUN_COST_USD",
    "MAX_REPAIR_ROUNDS", "GROUNDING_THRESHOLD", "DUPLICATE_TITLE_THRESHOLD", "REQ_DIFF_THRESHOLD",
)


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    """Tests never see the developer's real keys or .env."""
    for var in ENV_VARS:
        monkeypatch.delenv(var, raising=False)


@pytest.fixture(scope="session")
def sample_prd() -> Path:
    """The real sample PRD placed by the user in prd/ (never generated)."""
    files = sorted(p for p in (ROOT / "prd").glob("*") if p.suffix.lower() in SUPPORTED_SUFFIXES)
    if not files:
        pytest.skip("no sample PRD in prd/")
    return files[0]
