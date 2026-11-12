"""Milestone 3: S3 / S6 / S7 loops, critic, repair_plan, G1 gate, plan.md headings, validation report."""

import re

import pytest
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command
from rich.console import Console

from agent import apply_dependencies, build_graph, should_repair
from llm import CostTracker
from schemas import (
    DependencyEdgeDraft,
    DependencyPlanDraft,
    ReviewFinding,
    ReviewReport,
    Severity,
    Status,
    Verdict,
)
from tests.fake_llm import FakeLLM
from tests.test_pipeline import GENERIC_PRD


@pytest.fixture
def prd_file(tmp_path):
    f = tmp_path / "prd.md"
    f.write_text(GENERIC_PRD, encoding="utf-8")
    return f


def _graph(llm, checkpointer=None, **kw):
    return build_graph(llm, console=Console(quiet=True), checkpointer=checkpointer, **kw)


def _run_to_gate(prd_file, out, llm, **initial):
    graph = _graph(llm, MemorySaver())
    config = {"configurable": {"thread_id": "t"}}
    result = graph.invoke({"prd_path": str(prd_file), "out_dir": str(out), **initial}, config)
    return graph, config, result


def _blocking(check_id, item_key, message="problem"):
    return ReviewFinding(check_id=check_id, severity=Severity.blocking, item_key=item_key, message=message)


# --------------------------------------------------------------------------- loop control


def test_should_repair_stop_conditions():
    failing = ReviewReport(stage="s", round=1, verdict=Verdict.fail, findings=[_blocking("P1", None)])
    passing = ReviewReport(stage="s", round=1, verdict=Verdict.pass_, findings=[])
    assert should_repair(passing, 0, [0], 3) == (False, None)
    assert should_repair(failing, 0, [1], 3) == (True, None)
    assert should_repair(failing, 3, [3, 2, 1, 1], 3)[1].startswith("stopped after 3")
    assert "did not decrease" in should_repair(failing, 1, [2, 2], 3)[1]


# --------------------------------------------------------------------------- S3


def test_s3_repairs_missing_units(prd_file, tmp_path):
    llm = FakeLLM(drop_units={"u2"})
    _, _, state = _run_to_gate(prd_file, tmp_path / "out", llm)
    req_reports = [r for r in state["reports"] if r.stage == "check_requirements"]
    assert req_reports[0].blocking_count > 0 and {f.check_id for f in req_reports[0].findings} == {"R2"}
    assert req_reports[-1].blocking_count == 0 and state["req_rounds"] == 1
    repair_calls = [u for n, u in llm.calls if n == "RequirementDraftList" and "had these problems" in u]
    assert repair_calls and all(re.search(r"\bu\d+\b", u) for u in repair_calls)  # unit IDs shown as local refs
    covered = {uid for r in state["requirements"] for uid in r.unit_ids}
    assert covered == {u.id for u in state["parsed"].units}


# --------------------------------------------------------------------------- S6


def test_s6_verifies_proposed_edges(prd_file, tmp_path):
    _, _, state = _run_to_gate(prd_file, tmp_path / "out", FakeLLM())
    plan = state["plan"]
    be = {t.key for t in plan.tasks if t.track.value == "backend"}
    fe = [t for t in plan.tasks if t.track.value == "frontend"]
    assert fe and all(set(t.blocked_by) <= be and t.blocked_by for t in fe)
    assert any(f.check_id == "REF-DEP" and "BE-unknown-task" in f.message for f in state["reference_findings"])


def test_apply_dependencies_skips_cycles_and_dangling_edges(prd_file, tmp_path):
    _, _, state = _run_to_gate(prd_file, tmp_path / "out", FakeLLM())
    plan = state["plan"]
    a, b = plan.tasks[0].key, plan.tasks[1].key
    plan = plan.model_copy(update={"tasks": [plan.tasks[0].model_copy(update={"blocked_by": ["BE-gone"]}), *plan.tasks[1:]]})
    findings = []
    draft = DependencyPlanDraft(edges=[DependencyEdgeDraft(task_key=a, blocked_by=[b]),
                                       DependencyEdgeDraft(task_key=b, blocked_by=[a])])
    out = apply_dependencies(plan, draft, findings)
    edges = {t.key: t.blocked_by for t in out.tasks}
    assert edges[a] == [b] and edges[b] == []
    assert {"REF-CYCLE", "REF-DEP"} <= {f.check_id for f in findings}


# --------------------------------------------------------------------------- S7 critic + repair_plan


def test_critic_runs_once_on_whole_plan_when_clean(prd_file, tmp_path):
    llm = FakeLLM()
    _, _, state = _run_to_gate(prd_file, tmp_path / "out", llm)
    critic_calls = [u for (n, u), role in zip(llm.calls, llm.roles) if role == "critic"]
    assert len(critic_calls) == 1
    assert "<prd>" in critic_calls[0] and "<plan>" in critic_calls[0] and "Review the whole plan" in critic_calls[0]
    assert state["status"] is Status.PASS and state["plan_rounds"] == 0


def test_critic_overlap_triggers_repair_of_that_story_only(prd_file, tmp_path):
    first = FakeLLM()
    _, _, clean = _run_to_gate(prd_file, tmp_path / "clean", first)
    target = clean["plan"].tasks[-1]  # a task of the last story
    other_story = clean["plan"].stories[0].key
    overlap = _blocking("CRIT-OVERLAP", target.key, "Duplicates the migration of another story.")
    noise = ReviewFinding(check_id="crit-overlap", severity=Severity.warning, item_key=other_story, message="x")
    llm = FakeLLM(critic_findings=[[overlap], [noise]])  # round 2 reports on a non-repaired item -> filtered out
    _, _, state = _run_to_gate(prd_file, tmp_path / "out", llm)

    detail_users = [u for n, u in llm.calls if n == "StoryDetailDraft"]
    repairs = [u for u in detail_users if "Review findings to fix" in u]
    assert len(repairs) == 1 and f"Story key: {target.story_key}" in repairs[0]
    assert "Tasks that other stories already contain" in repairs[0] and "Current version of this story" in repairs[0]
    critic_users = [u for (n, u), role in zip(llm.calls, llm.roles) if role == "critic"]
    assert len(critic_users) == 2 and "Review ONLY these repaired items" in critic_users[1]
    assert target.story_key in critic_users[1].split("repaired items")[1]
    final = state["plan_report"]
    assert final.round == 2 and final.blocking_count == 0
    assert not any(f.item_key == other_story for f in final.findings)  # focus filter
    assert state["status"] is Status.PASS


def test_unresolved_findings_end_in_needs_review_with_explanation(prd_file, tmp_path):
    story_finding = lambda: _blocking("CRIT-MISREPRESENTED", None, "Epic-level issue the repair cannot route.")  # noqa: E731
    llm = FakeLLM(critic_findings=[[story_finding()]])
    out = tmp_path / "out"
    _, _, state = _run_to_gate(prd_file, out, llm)
    assert state["status"] is Status.NEEDS_REVIEW
    report = (out / "validation_report.md").read_text(encoding="utf-8")
    assert "## Remaining findings" in report and "Needs a human decision at G1" in report
    assert "**Final status:** NEEDS_REVIEW" in report


# --------------------------------------------------------------------------- G1


def test_g1_interrupts_and_approve_finishes(prd_file, tmp_path):
    graph, config, result = _run_to_gate(prd_file, tmp_path / "out", FakeLLM())
    assert result["__interrupt__"][0].value["status"] == "PASS"
    final = graph.invoke(Command(resume={"action": "approve"}), config)
    assert final["approval"] == "approve" and final["status"] is Status.PASS


def test_g1_abort(prd_file, tmp_path):
    graph, config, _ = _run_to_gate(prd_file, tmp_path / "out", FakeLLM())
    final = graph.invoke(Command(resume={"action": "abort"}), config)
    assert final["status"] is Status.ABORTED


def test_g1_feedback_goes_to_repair_plan(prd_file, tmp_path):
    llm = FakeLLM()
    graph, config, result = _run_to_gate(prd_file, tmp_path / "out", llm)
    story = result["plan"].stories[-1].key
    second = graph.invoke(Command(resume={"action": "feedback", "text": f"{story}: split the API task."}), config)
    repairs = [u for n, u in llm.calls if n == "StoryDetailDraft" and "G1-FEEDBACK" in u]
    assert len(repairs) == 1 and f"Story key: {story}" in repairs[0]
    assert second["__interrupt__"]  # back at the gate after re-checking
    final = graph.invoke(Command(resume={"action": "approve"}), config)
    assert final["status"] is Status.PASS


def test_yes_auto_approves_only_pass(prd_file, tmp_path):
    _, _, ok = _run_to_gate(prd_file, tmp_path / "a", FakeLLM(), auto_yes=True)
    assert "__interrupt__" not in ok and ok["approval"] == "approve"
    bad = FakeLLM(critic_findings=[[_blocking("CRIT-MISSING", None, "Unroutable.")]])
    _, _, needs = _run_to_gate(prd_file, tmp_path / "b", bad, auto_yes=True)
    assert needs["__interrupt__"]  # NEEDS_REVIEW still asks


# --------------------------------------------------------------------------- outputs


def test_plan_md_story_titles_are_one_level_above_their_sections(prd_file, tmp_path):
    out = tmp_path / "out"
    _, _, state = _run_to_gate(prd_file, out, FakeLLM())
    md = (out / "plan.md").read_text(encoding="utf-8")
    story = state["plan"].stories[0]
    assert f"\n## {story.title}\n" in md
    after = md.split(f"\n## {story.title}\n", 1)[1].split("\n---\n", 1)[0]
    levels = re.findall(r"^(#+) ", after, flags=re.MULTILINE)
    assert levels and min(len(x) for x in levels) == 3  # sections and task titles under the story
    assert "\n### Task: " in after and "\n#### " in after


def test_cost_is_tracked_per_stage_and_role():
    tracker = CostTracker(1.0)
    tracker.stage = "check_plan"
    tracker.record("claude-sonnet-5-5", {"input_tokens": 1000, "output_tokens": 100}, role="critic")
    tracker.stage = "detail_stories"
    tracker.record("claude-haiku-5-5", {"input_tokens": 1000, "output_tokens": 100}, role="generation")
    assert tracker.by_role["critic"]["calls"] == 1 and tracker.by_role["critic"]["models"] == ["claude-sonnet-5-5"]
    assert tracker.by_stage["check_plan"]["cost_usd"] == pytest.approx((1000 * 2 + 100 * 10) / 1e6)
    assert set(tracker.by_stage) == {"check_plan", "detail_stories"}


def test_overlap_named_in_message_repairs_the_duplicating_story(prd_file, tmp_path):
    from agent import resolve_repair_targets

    _, _, state = _run_to_gate(prd_file, tmp_path / "out", FakeLLM())
    plan = state["plan"]
    a, b = plan.tasks[0], next(t for t in plan.tasks if t.story_key != plan.tasks[0].story_key)
    f = _blocking("CRIT-OVERLAP", a.key, f"{b.key} adds the same columns again.")
    targets, _, _ = resolve_repair_targets([f], plan, state["skeletons"])
    assert set(targets) == {a.story_key, b.story_key}


def test_repeated_gwt_keywords_are_stripped():
    from agent import normalize_acceptance_criteria
    from schemas import AcceptanceCriterion

    acs, n = normalize_acceptance_criteria([AcceptanceCriterion(given="Given a member", when="When: they borrow",
                                                                then="**Then** the loan is saved")])
    assert n == 3 and (acs[0].given, acs[0].when, acs[0].then) == ("A member", "they borrow", "the loan is saved")


def test_cli_checkpoint_serde_allows_schema_types():
    from main import _checkpoint_serde
    from schemas import Requirement, ReqKind, TicketPlan

    serde = _checkpoint_serde()
    allowed = {name for _, name in serde._allowed_msgpack_modules} if hasattr(serde, "_allowed_msgpack_modules") else None
    assert allowed is None or {"TicketPlan", "Requirement", "ReqKind"} <= allowed
    req = Requirement(id="R-0123abcd", unit_ids=["U-abcdef-12345678"], source_quote="q", section_path=["S"],
                      kind=ReqKind.functional, statement="s")
    assert serde.loads_typed(serde.dumps_typed(req)) == req
    assert TicketPlan  # imported for the allow-list check above


def test_loop_keeps_best_round_when_it_regresses(prd_file, tmp_path):
    clean = _run_to_gate(prd_file, tmp_path / "clean", FakeLLM())[2]
    s1, s2 = clean["plan"].stories[0].key, clean["plan"].stories[1].key
    rounds = [[_blocking("CRIT-OVERLAP", s1), _blocking("CRIT-OVERLAP", s2)],  # round 1: 2 blocking
              [_blocking("CRIT-MISSING", s1)],                                 # round 2: 1 blocking (best)
              [_blocking("CRIT-MISSING", s1), _blocking("CRIT-UNTESTABLE-AC", s1)]]  # round 3: 2 -> not improving
    out = tmp_path / "out"
    state = _run_to_gate(prd_file, out, FakeLLM(critic_findings=rounds))[2]
    assert state["plan_blocking_history"] == [2, 1, 2]
    assert state["plan_report"].round == 2 and state["plan_report"].blocking_count == 1
    assert "kept the plan of round 2" in state["plan_stop_reason"]
    assert "kept the plan of round 2" in (out / "validation_report.md").read_text(encoding="utf-8")


def test_critic_request_caches_only_the_prd_prefix(tmp_path):
    from langchain_core.messages import HumanMessage, SystemMessage

    from agent import critic_user_message, system_prompt
    from config import Settings
    from llm import LLM
    from tools.file_reader import load_prd

    f = tmp_path / "prd.md"
    f.write_text(GENERIC_PRD, encoding="utf-8")
    plan = _run_to_gate(f, tmp_path / "out", FakeLLM())[2]["plan"]
    blocks = critic_user_message(plan, load_prd(f), None)
    model = LLM(Settings(), replay=True, cache_dir=tmp_path / "c").chat_model("critic")
    assert model.model == "claude-sonnet-5-5"
    payload = model._get_request_payload([SystemMessage(content=system_prompt("critic")), HumanMessage(content=blocks)])
    assert "cache_control" not in payload  # no automatic breakpoint at the end (the plan)
    content = payload["messages"][0]["content"]
    assert content[0]["cache_control"] == {"type": "ephemeral"} and "<prd>" in content[0]["text"]
    assert "cache_control" not in content[1] and "<plan>" in content[1]["text"]
    assert payload["system"][-1]["cache_control"] == {"type": "ephemeral"}
