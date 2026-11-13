"""End-to-end run on the real sample PRD from the committed LLM cache (the --replay mechanism, SPEC §15).

No API key is set (conftest clears them) and no network is used: every LLM response comes from .cache/llm/.
The run takes the same path as the committed sample run: at each G1 it is offered the reviewer's recorded answer
(out/sample-v1/gate_answers.json) and accepts it with Enter. It must produce exactly the committed plan.
"""

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from main import ExitCode, app

ROOT = Path(__file__).resolve().parent.parent
SAMPLE_OUT = ROOT / "out" / "sample-v1"
ACCEPT_RECORDED = "\n" * 10  # Enter at every G1: accept the recorded answer


@pytest.mark.skipif(not (SAMPLE_OUT / "plan.json").exists(), reason="no committed sample run")
def test_replay_reproduces_the_committed_sample_run(sample_prd, tmp_path, monkeypatch):
    monkeypatch.chdir(ROOT)  # the cache lives in .cache/llm relative to the project root
    out = tmp_path / "out"
    result = CliRunner().invoke(app, ["run", str(sample_prd), "--out", str(out), "--replay", "--gate-answers",
                                      str(SAMPLE_OUT / "gate_answers.json")], input=ACCEPT_RECORDED)
    assert result.exit_code == ExitCode.OK, result.output[-2000:]
    stats = json.loads((out / "run_stats.json").read_text(encoding="utf-8"))
    assert stats["status"] == "PASS" and stats["api_calls"] == 0 and stats["cost_usd"] == 0
    assert stats["cache_hits"] > 0
    assert (out / "plan.json").read_text(encoding="utf-8") == (SAMPLE_OUT / "plan.json").read_text(encoding="utf-8")
    for name in ("plan.md", "requirements.md", "validation_report.md"):
        assert (out / name).read_text(encoding="utf-8") == (SAMPLE_OUT / name).read_text(encoding="utf-8"), name
