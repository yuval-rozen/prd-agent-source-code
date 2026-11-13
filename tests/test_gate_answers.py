"""Replay gate answers: every run records its human gate answers; --replay offers the recorded G1 answers
(Enter accepts, or type another), and G2 is never answered from a recording."""

import builtins
import json
from pathlib import Path

from typer.testing import CliRunner

import main
from main import GATE_ANSWERS_FILE, _ask_approval, _ask_publish, app, load_gate_answers, save_gate_answers

G1_PAYLOAD = {"status": "NEEDS_REVIEW", "stories": 1, "tasks": 2, "blocking": [], "warnings": 0, "out_dir": "out"}
G2_PAYLOAD = {"gate": "G2", "repo": "o/r", "changes": [], "churn": None,
              "counts": {"create": 0, "update": 1, "close": 0, "unchanged": 0}}
FEEDBACK = {"action": "feedback", "text": "US-a: the backend sets the dates."}


def _inputs(monkeypatch, *answers):
    queue = list(answers)

    def fake_input(prompt=""):
        if not queue:
            raise EOFError
        return queue.pop(0)

    monkeypatch.setattr(builtins, "input", fake_input)
    return queue


def test_answers_round_trip_and_only_for_the_same_prd(tmp_path):
    path = tmp_path / GATE_ANSWERS_FILE
    save_gate_answers(path, "abc", {"g1": [FEEDBACK, {"action": "approve"}], "g2": [{"action": "confirm"}]})
    data = load_gate_answers(path, "abc")
    assert data["g1"] == [FEEDBACK, {"action": "approve"}] and data["g2"] == [{"action": "confirm"}]
    assert load_gate_answers(path, "other-prd") is None
    assert load_gate_answers(tmp_path / "missing.json", "abc") is None


def test_g1_offers_the_recorded_answer_and_enter_accepts_it(monkeypatch):
    _inputs(monkeypatch, "")
    assert _ask_approval(G1_PAYLOAD, FEEDBACK) == FEEDBACK


def test_g1_recorded_answer_can_be_replaced(monkeypatch):
    _inputs(monkeypatch, "feedback", "US-a: something else.")
    assert _ask_approval(G1_PAYLOAD, FEEDBACK) == {"action": "feedback", "text": "US-a: something else."}
    _inputs(monkeypatch, "abort")
    assert _ask_approval(G1_PAYLOAD, FEEDBACK) == {"action": "abort"}
    _inputs(monkeypatch)  # EOF never accepts the recording silently
    assert _ask_approval(G1_PAYLOAD, FEEDBACK) == {"action": "abort"}


def test_g1_without_a_recording_behaves_as_before(monkeypatch):
    _inputs(monkeypatch, "")
    assert _ask_approval(G1_PAYLOAD) == {"action": "abort"}


def test_g2_is_never_answered_from_a_recording(monkeypatch):
    _inputs(monkeypatch, "")  # Enter at G2 is abort, whatever was recorded
    assert _ask_publish(G2_PAYLOAD) == {"action": "abort"}


def test_cli_records_answers_and_replay_offers_them_at_g1(sample_prd, tmp_path, monkeypatch):
    """The CLI loop: the run writes gate_answers.json; a replay offers the i-th recorded G1 answer at the i-th G1."""
    monkeypatch.chdir(tmp_path)
    out = tmp_path / "out"
    offered: list = []

    class FakeGraph:
        def __init__(self):
            self.n = 0

        def invoke(self, value, config):
            self.n += 1
            if self.n <= 2:  # two G1 gates (feedback, then approve)
                return {"__interrupt__": [type("I", (), {"value": dict(G1_PAYLOAD)})()]}
            return {"status": None}

    monkeypatch.setattr(main, "build_graph", lambda *a, **k: FakeGraph())
    monkeypatch.setattr(main, "load_settings", lambda: type("S", (), {
        "max_repair_rounds": 1, "grounding_threshold": 90, "duplicate_title_threshold": 90})())
    monkeypatch.setattr(main, "LLM", lambda settings, replay=False: type("L", (), {
        "cache": type("C", (), {"hits": 0, "misses": 0})()})())
    monkeypatch.setattr(main, "_write_run_stats", lambda *a, **k: None)
    real_ask = main._ask_approval
    monkeypatch.setattr(main, "_ask_approval", lambda p, o=None: (offered.append(o), real_ask(p, o))[1])

    first = CliRunner().invoke(app, ["run", str(sample_prd), "--out", str(out)],
                               input="feedback\nUS-a: the backend sets the dates.\napprove\n")
    assert first.exit_code == 0, first.output
    recorded = json.loads((out / GATE_ANSWERS_FILE).read_text(encoding="utf-8"))
    assert recorded["g1"] == [FEEDBACK, {"action": "approve"}] and recorded["g2"] == []
    assert offered == [None, None]  # not a replay: nothing offered

    offered.clear()
    replay = CliRunner().invoke(app, ["run", str(sample_prd), "--out", str(out), "--replay"], input="\n\n")
    assert replay.exit_code == 0, replay.output
    assert offered == [FEEDBACK, {"action": "approve"}]
    assert "Recorded answer: " in replay.output
    assert json.loads((out / GATE_ANSWERS_FILE).read_text(encoding="utf-8"))["g1"] == recorded["g1"]

    other = tmp_path / "answers.json"  # --gate-answers points a replay elsewhere at a recording
    Path(other).write_text((out / GATE_ANSWERS_FILE).read_text(encoding="utf-8"), encoding="utf-8")
    offered.clear()
    CliRunner().invoke(app, ["run", str(sample_prd), "--out", str(tmp_path / "o2"), "--replay",
                             "--gate-answers", str(other)], input="\n\n")
    assert offered == [FEEDBACK, {"action": "approve"}]
