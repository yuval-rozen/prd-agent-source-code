"""Milestone 5: requirement diff, key reconcile, incremental update, persisted reviewer decisions, anchor from
issues, and the close -> reopen cycle on GitHub (never a duplicate)."""

import pytest
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command
from rich.console import Console

from agent import build_graph, reconcile_story_keys, requirement_diff
from schemas import ReqKind, Requirement, StorySkeleton, SyncActionType, TicketPlan, requirement_id_base
from tests.fake_github import FakeGitHub
from tests.fake_llm import FakeLLM
from tests.test_pipeline import GENERIC_PRD
from tools.github_tool import publish, read_sub_issues, sync_diff
from tools.state_store import load_plan

V2_PRD = GENERIC_PRD.replace("- Cancel a reservation.", "- Cancel an open reservation.")  # a rephrase


def _req(text, kind=ReqKind.functional):
    return Requirement(id=requirement_id_base(text), unit_ids=["U-abcdef-12345678"], source_quote=text,
                       section_path=["S"], kind=kind, statement=text)


def _run(prd_text, tmp_path, out, llm=None, **initial):
    prd = tmp_path / "prd.md"
    prd.write_text(prd_text, encoding="utf-8")
    llm = llm or FakeLLM()
    graph = build_graph(llm, console=Console(quiet=True))
    return graph.invoke({"prd_path": str(prd), "out_dir": str(out), "auto_yes": True, **initial}), llm


# --------------------------------------------------------------------------- requirement diff


def test_rephrase_is_reported_as_changed():
    old = [_req("Members can borrow a book."), _req("Each loan stores a due date."), _req("Fines are charged daily.")]
    new = [_req("Members can borrow a book."), _req("Each loan stores the due date."), _req("Members can renew a loan.")]
    diff = requirement_diff(old, new)
    assert diff.changed == [(old[1].id, new[1].id)]
    assert diff.added == [new[2].id] and diff.removed == [old[2].id]


def test_unrelated_requirements_are_not_paired():
    diff = requirement_diff([_req("Fines are charged daily.")], [_req("Members can renew a loan.")])
    assert diff.changed == [] and len(diff.added) == len(diff.removed) == 1


def test_identical_requirement_lists_have_an_empty_diff():
    reqs = [_req("A."), _req("B.")]
    diff = requirement_diff(reqs, list(reversed(reqs)))
    assert diff.added == diff.changed == diff.removed == []


# --------------------------------------------------------------------------- reconcile


def test_new_key_is_reconciled_to_the_old_key():
    a, b = _req("Reserve a book."), _req("Cancel a reservation.")
    old = [StorySkeleton(key="US-reservations", title="Manage reservations", requirement_ids=[a.id, b.id])]
    new = [StorySkeleton(key="US-book-reservations", title="Manage book reservations", requirement_ids=[a.id, b.id])]
    findings = []
    out = reconcile_story_keys(new, old, None, findings)
    assert out[0].key == "US-reservations" and findings[0].check_id == "REF-KEY"


def test_unrelated_new_story_keeps_its_key():
    old = [StorySkeleton(key="US-reservations", title="Manage reservations", requirement_ids=[_req("Reserve.").id])]
    new = [StorySkeleton(key="US-fines", title="Pay fines", requirement_ids=[_req("Pay a fine.").id])]
    assert reconcile_story_keys(new, old, None, [])[0].key == "US-fines"


# --------------------------------------------------------------------------- incremental update


def test_unchanged_stories_are_carried_over_without_calling_the_llm(tmp_path):
    out = tmp_path / "out"
    first, _ = _run(GENERIC_PRD, tmp_path, out)
    v1 = first["plan"]
    second, llm = _run(V2_PRD, tmp_path, out)
    v2 = second["plan"]
    diff = second["requirement_diff"]
    assert len(diff.changed) == 1 and diff.added == diff.removed == []
    affected = {s.key for s in v2.stories if any(new in s.requirement_ids for _, new in diff.changed)}
    assert affected and set(second["carried"]) == {s.key for s in v2.stories} - affected
    detailed = [u for n, u in llm.calls if n == "StoryDetailDraft"]
    assert len(detailed) == len(affected)  # S5 ran only for the affected story
    assert all(f"Story key: {k}" in detailed[0] for k in affected)
    assert "keep the key_slug of every task" in detailed[0] and "Current version of this story" in detailed[0]
    for key in second["carried"]:  # carried stories and their tasks are copied unchanged
        assert next(s for s in v2.stories if s.key == key) == next(s for s in v1.stories if s.key == key)
        assert [t for t in v2.tasks if t.story_key == key] == [t for t in v1.tasks if t.story_key == key]
    assert v2.project == v1.project  # same epic: no noisy update
    assert "## Requirement diff (update run)" in (out / "requirements.md").read_text(encoding="utf-8")


def test_carried_task_edges_to_removed_keys_are_dropped(tmp_path):
    out = tmp_path / "out"
    first, _ = _run(GENERIC_PRD, tmp_path, out)
    v1 = first["plan"]
    carried_task = next(t for t in v1.tasks if t.story_key != v1.stories[-1].key)
    stale = v1.model_copy(update={"tasks": [t.model_copy(update={"blocked_by": [*t.blocked_by, "BE-removed-task"]})
                                            if t.key == carried_task.key else t for t in v1.tasks]})
    (out / "plan.json").write_text(stale.model_dump_json(indent=2), encoding="utf-8")
    second, _ = _run(V2_PRD, tmp_path, out)
    task = next(t for t in second["plan"].tasks if t.key == carried_task.key)
    assert "BE-removed-task" not in task.blocked_by
    assert any(f.check_id == "REF-DEP" and "BE-removed-task" in f.message for f in second["reference_findings"])


def test_identical_prd_reruns_make_no_detail_calls(tmp_path):
    out = tmp_path / "out"
    first, _ = _run(GENERIC_PRD, tmp_path, out)
    second, llm = _run(GENERIC_PRD, tmp_path, out)
    assert not [n for n, _ in llm.calls if n == "StoryDetailDraft"]
    assert second["plan"].stories == first["plan"].stories and second["plan"].tasks == first["plan"].tasks


# --------------------------------------------------------------------------- reviewer decisions persist


def test_reviewer_decisions_are_saved_and_reused_by_the_next_run(tmp_path):
    out = tmp_path / "out"
    prd = tmp_path / "prd.md"
    prd.write_text(GENERIC_PRD, encoding="utf-8")
    graph = build_graph(FakeLLM(), console=Console(quiet=True), checkpointer=MemorySaver())
    config = {"configurable": {"thread_id": "d"}}
    first = graph.invoke({"prd_path": str(prd), "out_dir": str(out)}, config)
    story = first["plan"].stories[-1].key
    graph.invoke(Command(resume={"action": "feedback", "text": f"{story}: holds expire after 3 days."}), config)
    graph.invoke(Command(resume={"action": "approve"}), config)
    saved = load_plan(out)
    assert [d.message for d in saved.reviewer_decisions] == [f"{story}: holds expire after 3 days."]
    second, llm = _run(V2_PRD, tmp_path, out)
    critic = [u for (n, u), role in zip(llm.calls, llm.roles) if role == "critic"]
    assert critic and "holds expire after 3 days" in critic[0]
    assert load_plan(out).reviewer_decisions == saved.reviewer_decisions


# --------------------------------------------------------------------------- anchor from issues


def test_anchor_is_rebuilt_from_issues_when_plan_json_is_missing(tmp_path):
    gh = FakeGitHub()
    first, _ = _run(GENERIC_PRD, tmp_path, tmp_path / "a", github_publish=None)
    plan = first["plan"]
    tool = gh.tool()
    listing = tool.list_marked_issues()
    publish(plan, sync_diff(plan, listing, read_sub_issues(tool, plan, listing)), tool)
    prd = tmp_path / "prd.md"
    llm = FakeLLM()
    graph = build_graph(llm, console=Console(quiet=True), github=gh.tool())
    state = graph.invoke({"prd_path": str(prd), "out_dir": str(tmp_path / "fresh"), "publish": True, "auto_yes": True})
    s4 = next(u for n, u in llm.calls if n == "StoryPlanDraft")
    assert "already exist as issues" in s4 and all(s.key in s4 for s in plan.stories)
    assert state["plan"].project.key == plan.project.key
    assert all(a.action is SyncActionType.unchanged for a in state["sync_actions"])  # matched, nothing duplicated


# --------------------------------------------------------------------------- close -> reopen, never duplicate


def _sync_and_publish(plan, gh):
    tool = gh.tool()
    listing = tool.list_marked_issues()
    actions = sync_diff(plan, listing, read_sub_issues(tool, plan, listing))
    return actions, publish(plan, actions, tool)


def test_removed_ticket_that_comes_back_is_reopened_not_duplicated(tmp_path):
    first, _ = _run(GENERIC_PRD, tmp_path, tmp_path / "a")
    v1: TicketPlan = first["plan"]
    gh = FakeGitHub()
    _, published = _sync_and_publish(v1, gh)
    numbers = dict(published.numbers)
    gone_story = v1.stories[-1]
    gone_keys = {gone_story.key, *(t.key for t in v1.tasks if t.story_key == gone_story.key)}
    v2 = v1.model_copy(update={"stories": v1.stories[:-1], "tasks": [t for t in v1.tasks if t.key not in gone_keys],
                               "project": v1.project.model_copy(update={"story_keys": [s.key for s in v1.stories[:-1]]})})
    v2 = TicketPlan.model_validate(v2.model_dump())
    actions, _ = _sync_and_publish(v2, gh)
    assert {a.key for a in actions if a.action is SyncActionType.close} == gone_keys
    assert all(gh.issues[numbers[k]]["state"] == "closed" for k in gone_keys)
    total = len(gh.issues)
    actions, back = _sync_and_publish(v1, gh)  # the tickets come back
    by_key = {a.key: a for a in actions if a.action is not SyncActionType.link}
    assert all(by_key[k].action is SyncActionType.update for k in gone_keys)  # update = reopen, never create
    assert len(gh.issues) == total  # no duplicate issues
    assert all(gh.issues[numbers[k]]["state"] == "open" for k in gone_keys)
    assert all(back.numbers[k] == numbers[k] for k in gone_keys)  # same issue numbers as before
    again, _ = _sync_and_publish(v1, gh)
    assert all(a.action is SyncActionType.unchanged for a in again)


def test_llm_regrouping_of_unchanged_content_does_not_change_the_plan(tmp_path):
    """S4 variance on unchanged content (re-scoping a constraint, moving an unchanged requirement) is ignored."""
    from agent import stabilize_update

    out = tmp_path / "out"
    v1 = _run(GENERIC_PRD, tmp_path, out)[0]["plan"]
    constraint = next(r for r in v1.requirements if r.kind is ReqKind.constraint)
    scoped = [r.model_copy(update={"applies_to_requirement_ids": [v1.stories[0].requirement_ids[0]]})
              if r.id == constraint.id else r for r in v1.requirements]
    previous = v1.model_copy(update={"requirements": scoped})
    moved = previous.stories[0].requirement_ids[0]
    llm_skeletons = [StorySkeleton(key=s.key, title=s.title + " (rephrased)",
                                   requirement_ids=[r for r in s.requirement_ids if r != moved]) for s in previous.stories]
    llm_skeletons[-1].requirement_ids.append(moved)  # the LLM moved an unchanged requirement to another story
    llm_reqs = [r.model_copy(update={"applies_to_requirement_ids": []}) if r.id == constraint.id else r
                for r in previous.requirements]  # ... and re-scoped the constraint to global
    diff = requirement_diff(previous.requirements, llm_reqs)
    skeletons, reqs = stabilize_update(llm_skeletons, llm_reqs, previous, diff, [])
    assert [(s.key, s.title, s.requirement_ids) for s in skeletons] == \
        [(s.key, s.title, s.requirement_ids) for s in previous.stories]
    assert next(r for r in reqs if r.id == constraint.id).applies_to_requirement_ids == [moved]


def test_added_requirement_goes_where_s4_put_it(tmp_path):
    from agent import stabilize_update

    v1 = _run(GENERIC_PRD, tmp_path, tmp_path / "out")[0]["plan"]
    new = _req("Members can renew a loan.")
    llm_skeletons = [StorySkeleton(key=s.key, title=s.title, requirement_ids=list(s.requirement_ids)) for s in v1.stories]
    llm_skeletons[0].requirement_ids.append(new.id)
    llm_skeletons.append(StorySkeleton(key="US-brand-new", title="Unrelated new story", requirement_ids=[v1.requirements[-1].id]))
    reqs = [*v1.requirements, new]
    diff = requirement_diff(v1.requirements, reqs)
    skeletons, _ = stabilize_update(llm_skeletons, reqs, v1, diff, [])
    assert new.id in skeletons[0].requirement_ids
    assert "US-brand-new" not in {s.key for s in skeletons}  # it only held an unchanged requirement


def test_update_run_critic_reviews_only_changed_items(tmp_path):
    out = tmp_path / "out"
    _run(GENERIC_PRD, tmp_path, out)
    second, llm = _run(V2_PRD, tmp_path, out)
    critic = [u for (n, u), role in zip(llm.calls, llm.roles) if role == "critic"]
    assert len(critic) == 1 and "Review ONLY these new or changed items" in critic[0]
    affected = [s.key for s in second["plan"].stories if s.key not in second["carried"]]
    focus = critic[0].split("new or changed items")[1]
    assert all(k in focus for k in affected) and not any(k in focus for k in second["carried"])
    third, llm3 = _run(V2_PRD, tmp_path, out)  # nothing changed since the last run
    assert not [r for r in llm3.roles if r == "critic"]


def test_affected_story_takes_the_new_title(tmp_path):
    from agent import stabilize_update

    v1 = _run(GENERIC_PRD, tmp_path, tmp_path / "out")[0]["plan"]
    story = v1.stories[-1]
    dropped = story.requirement_ids[-1]
    reqs = [r for r in v1.requirements if r.id != dropped]
    llm = [StorySkeleton(key=s.key, title=s.title + " NEW", requirement_ids=[r for r in s.requirement_ids if r != dropped])
           for s in v1.stories]
    skeletons, _ = stabilize_update(llm, reqs, v1, requirement_diff(v1.requirements, reqs), [])
    titles = {s.key: s.title for s in skeletons}
    assert titles[story.key] == story.title + " NEW"  # scope changed -> new title
    assert all(titles[s.key] == s.title for s in v1.stories[:-1])  # unchanged -> old title kept
