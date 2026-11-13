"""Task-level incremental update: code decides keep / revise / close, key reuse and churn; the LLM only places
added requirements. Fixtures use a generic library domain."""

from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command
from rich.console import Console

from agent import (
    build_graph,
    change_causes,
    churn_guard,
    classify_tasks,
    detail_stories,
    match_old_keys,
    requirement_diff,
)
from schemas import (
    AcceptanceCriterion,
    DerivedReason,
    Label,
    ParentProject,
    ReqKind,
    Requirement,
    Size,
    StorySkeleton,
    SyncActionType,
    TechnicalTask,
    TicketPlan,
    Track,
    UserStory,
    requirement_id_base,
)
from tests.fake_github import FakeGitHub
from tests.fake_llm import FakeLLM
from tests.test_pipeline import GENERIC_PRD

TEXTS = ["Members can borrow a book.", "Each loan stores a due date.", "Members can renew a loan once.",
         "Overdue loans are listed."]
CHANGED = "Members can renew a loan twice."


def _req(text):
    return Requirement(id=requirement_id_base(text), unit_ids=["U-abcdef-12345678"], source_quote=text,
                       section_path=["Loans"], kind=ReqKind.functional, statement=text)


def _task(key, track, req_ids, story="US-loans", derived=None, blocked_by=()):
    area = {Track.backend: Label.area_backend, Track.frontend: Label.area_frontend, Track.qa_general: Label.area_qa}[track]
    prefix = {Track.backend: "[BE]", Track.frontend: "[FE]", Track.qa_general: "[QA]"}[track]
    words = key.split("-", 1)[1].replace("-", " ")  # ticket text never contains keys (P12)
    return TechnicalTask(key=key, story_key=story, title=f"{prefix} {words} work", track=track, description=f"Do {words}.",
                         size=Size.S, requirement_ids=list(req_ids), derived_reason=derived, blocked_by=list(blocked_by),
                         definition_of_done=[f"{words} done"], labels=[Label.type_task, area, Label.prd_agent])


def _plan(reqs, tasks, story_reqs):
    story = UserStory(key="US-loans", title="Manage loans", as_a="member", i_want="to borrow", so_that="I read",
                      business_description="d", business_value="v",
                      acceptance_criteria=[AcceptanceCriterion(given="g", when="w", then="t"),
                                           AcceptanceCriterion(given="g2", when="w2", then="t2")],
                      requirement_ids=story_reqs)
    project = ParentProject(key="EPIC-library", title="Library", scope="s", business_goals=["g"], story_keys=["US-loans"])
    return TicketPlan(prd_hash="h", project=project, stories=[story], tasks=tasks, requirements=reqs)


def _four_task_story():
    reqs = [_req(t) for t in TEXTS]
    tasks = [_task("BE-borrow-endpoint", Track.backend, [reqs[0].id]),
             _task("BE-loans-table-migration", Track.backend, [reqs[1].id]),
             _task("BE-renew-endpoint", Track.backend, [reqs[2].id], blocked_by=["BE-loans-table-migration"]),
             _task("FE-overdue-list", Track.frontend, [reqs[3].id])]
    return _plan(reqs, tasks, [r.id for r in reqs])


def _update(previous, new_reqs, llm):
    diff = requirement_diff(previous.requirements, new_reqs)
    changed = dict(diff.changed)
    skeleton = StorySkeleton(key="US-loans", title="Manage loans",
                             requirement_ids=[changed.get(r, r) for r in previous.stories[0].requirement_ids
                                              if r not in diff.removed] + diff.added)
    findings = []
    stories, tasks = detail_stories([skeleton], new_reqs, llm, findings, previous, set(), [], diff)
    plan = TicketPlan(prd_hash="h2", project=previous.project, stories=stories, tasks=tasks, requirements=new_reqs)
    plan = match_old_keys(plan, previous, diff, findings)
    return churn_guard(plan, previous, diff, set(), findings), diff, findings


# --------------------------------------------------------------------------- (a) and (b)


def test_a_one_changed_requirement_leaves_the_other_three_tasks_byte_identical():
    previous = _four_task_story()
    new_reqs = [_req(TEXTS[0]), _req(TEXTS[1]), _req(CHANGED), _req(TEXTS[3])]
    llm = FakeLLM()
    plan, diff, _ = _update(previous, new_reqs, llm)
    assert diff.changed == [(previous.requirements[2].id, new_reqs[2].id)]
    old = {t.key: t for t in previous.tasks}
    new = {t.key: t for t in plan.tasks}
    assert set(new) == set(old)  # nothing created or closed
    for key in ("BE-borrow-endpoint", "BE-loans-table-migration", "FE-overdue-list"):
        assert new[key].model_dump_json() == old[key].model_dump_json()  # byte-identical
    renew = new["BE-renew-endpoint"]
    assert renew != old["BE-renew-endpoint"] and renew.requirement_ids == [new_reqs[2].id]
    assert renew.blocked_by == ["BE-loans-table-migration"]  # a revision keeps its blockers
    user = next(u for n, u in llm.calls if n == "StoryUpdateDraft")
    assert "REVISE BE-renew-endpoint" in user and user.count("KEEP ") == 3


def test_b_a_revise_without_cause_is_restored_by_code():
    previous = _four_task_story()
    new_reqs = [_req(TEXTS[0]), _req(TEXTS[1]), _req(CHANGED), _req(TEXTS[3])]
    plan, _, findings = _update(previous, new_reqs, FakeLLM(rogue_revise=True))  # the model also "revises" KEEP tasks
    old = {t.key: t for t in previous.tasks}
    for t in plan.tasks:
        if t.key != "BE-renew-endpoint":
            assert t.model_dump_json() == old[t.key].model_dump_json()
    assert sum(f.check_id == "REF-RESTORE" for f in findings) == 3


def test_b_guard_restores_a_task_changed_without_cause():
    previous = _four_task_story()
    new_reqs = [_req(TEXTS[0]), _req(TEXTS[1]), _req(CHANGED), _req(TEXTS[3])]
    diff = requirement_diff(previous.requirements, new_reqs)
    tampered = previous.model_copy(update={"tasks": [t.model_copy(update={"title": t.title + " (reworded)"})
                                                     if t.key == "FE-overdue-list" else t for t in previous.tasks]})
    findings = []
    guarded = churn_guard(tampered, previous, diff, set(), findings)
    assert next(t for t in guarded.tasks if t.key == "FE-overdue-list") == previous.tasks[3]
    assert [f.check_id for f in findings] == ["REF-CHURN"]


# --------------------------------------------------------------------------- classify / close / add


def test_classification_keep_revise_close():
    previous = _four_task_story()
    removed_only = previous.requirements[3].id
    new_reqs = [_req(TEXTS[0]), _req(TEXTS[1]), _req(CHANGED)]
    classes = classify_tasks(previous.tasks, requirement_diff(previous.requirements, new_reqs))
    assert {k: v[0] for k, v in classes.items()} == {"BE-borrow-endpoint": "KEEP", "BE-loans-table-migration": "KEEP",
                                                     "BE-renew-endpoint": "REVISE", "FE-overdue-list": "CLOSE"}
    assert classes["FE-overdue-list"][1] == [f"{removed_only} removed"]


def test_task_whose_requirements_were_all_removed_is_closed():
    previous = _four_task_story()
    new_reqs = [_req(TEXTS[0]), _req(TEXTS[1]), _req(TEXTS[2])]
    plan, _, _ = _update(previous, new_reqs, FakeLLM())
    assert "FE-overdue-list" not in {t.key for t in plan.tasks}
    assert all(t in previous.tasks for t in plan.tasks)  # the rest unchanged


def test_added_requirement_into_an_existing_task():
    previous = _four_task_story()
    added = _req("Members can see their loan history.")
    new_reqs = [*previous.requirements, added]
    plan, _, _ = _update(previous, new_reqs, FakeLLM(place_added_in="BE-borrow-endpoint"))
    borrow = next(t for t in plan.tasks if t.key == "BE-borrow-endpoint")
    assert added.id in borrow.requirement_ids and len(plan.tasks) == 4
    assert [t for t in plan.tasks if t.key != "BE-borrow-endpoint"] == [t for t in previous.tasks if t.key != "BE-borrow-endpoint"]


def test_added_requirement_as_a_new_task():
    previous = _four_task_story()
    added = _req("Members can see their loan history.")
    plan, _, _ = _update(previous, [*previous.requirements, added], FakeLLM())
    new = [t for t in plan.tasks if t.key not in {p.key for p in previous.tasks}]
    assert len(new) == 1 and new[0].requirement_ids == [added.id]
    assert all(t in previous.tasks for t in plan.tasks if t not in new)


# --------------------------------------------------------------------------- keys


def test_key_is_reused_only_for_same_story_track_and_shared_requirements():
    previous = _four_task_story()
    qa = _task("QA-loans-tests", Track.qa_general, [], derived=DerivedReason.testing)
    previous = previous.model_copy(update={"tasks": [*previous.tasks, qa]})
    regenerated = [t for t in previous.tasks if t.key not in ("QA-loans-tests", "BE-renew-endpoint")]
    regenerated += [_task("QA-loans-test-suite", Track.qa_general, [], derived=DerivedReason.testing),  # same derived reason
                    _task("BE-renew-loan-api", Track.backend, [previous.requirements[2].id]),  # shares a requirement
                    _task("FE-renew-button", Track.frontend, [previous.requirements[2].id])]  # other track: new key
    plan = previous.model_copy(update={"tasks": regenerated})
    matched = {t.key for t in match_old_keys(plan, previous, None, []).tasks}
    assert {"QA-loans-tests", "BE-renew-endpoint", "FE-renew-button"} <= matched
    assert "QA-loans-test-suite" not in matched and "BE-renew-loan-api" not in matched


def test_no_key_reuse_without_shared_requirements():
    previous = _four_task_story()
    plan = previous.model_copy(update={"tasks": [*previous.tasks[:3], _task("FE-unrelated", Track.frontend, [])]})
    assert {t.key for t in match_old_keys(plan, previous, None, []).tasks} == {
        "BE-borrow-endpoint", "BE-loans-table-migration", "BE-renew-endpoint", "FE-unrelated"}


# --------------------------------------------------------------------------- causes in G2


def test_every_change_has_a_cause():
    previous = _four_task_story()
    new_reqs = [_req(TEXTS[0]), _req(TEXTS[1]), _req(CHANGED)]
    plan, diff, _ = _update(previous, new_reqs, FakeLLM())
    causes = change_causes(plan, previous, diff, set())
    old_r3, new_r3 = previous.requirements[2].id, new_reqs[2].id
    assert causes["BE-renew-endpoint"] == [f"{old_r3} changed to {new_r3}"]
    assert causes["FE-overdue-list"] == [f"{previous.requirements[3].id} removed"]  # closed


def test_g2_shows_causes_and_zero_churn_for_a_prd_update(tmp_path):
    prd = tmp_path / "prd.md"
    out = tmp_path / "out"
    gh = FakeGitHub()
    prd.write_text(GENERIC_PRD, encoding="utf-8")
    build_graph(FakeLLM(), console=Console(quiet=True), github=gh.tool()).invoke(
        {"prd_path": str(prd), "out_dir": str(out), "publish": True, "auto_yes": True})
    prd.write_text(GENERIC_PRD.replace("- Cancel a reservation.", "- Cancel an open reservation."), encoding="utf-8")
    graph = build_graph(FakeLLM(), console=Console(quiet=True), checkpointer=MemorySaver(), github=gh.tool())
    config = {"configurable": {"thread_id": "u"}}
    graph.invoke({"prd_path": str(prd), "out_dir": str(out), "publish": True}, config)
    g2 = graph.invoke(Command(resume={"action": "approve"}), config)["__interrupt__"][0].value
    assert g2["gate"] == "G2" and g2["churn"] == []
    assert g2["changes"] and all(c["cause"] for c in g2["changes"])
    final = graph.invoke(Command(resume={"action": "confirm"}), config)
    assert final["publish_result"]["updated"]
    again = build_graph(FakeLLM(), console=Console(quiet=True), github=gh.tool()).invoke(
        {"prd_path": str(prd), "out_dir": str(out), "publish": True, "auto_yes": True})
    assert all(a.action is SyncActionType.unchanged for a in again["sync_actions"])


# --------------------------------------------------------------------------- repairs and G1 feedback in update runs

from agent import repair_update  # noqa: E402
from schemas import ReviewFinding, Severity  # noqa: E402


def _changed_plan():
    previous = _four_task_story()
    new_reqs = [_req(TEXTS[0]), _req(TEXTS[1]), _req(CHANGED), _req(TEXTS[3])]
    plan, diff, _ = _update(previous, new_reqs, FakeLLM())
    skeletons = [StorySkeleton(key=s.key, title=s.title, requirement_ids=s.requirement_ids) for s in plan.stories]
    return previous, plan, diff, skeletons


def _blocking(item, message="problem", check="CRIT-MISSING"):
    return ReviewFinding(check_id=check, severity=Severity.blocking, item_key=item, message=message)


def test_repair_revises_only_the_named_task(tmp_path):
    previous, plan, diff, skeletons = _changed_plan()
    llm = FakeLLM()
    repaired, _, touched, _ = repair_update(plan, skeletons, [_blocking("BE-renew-endpoint")], llm, [], previous, diff)
    before = {t.key: t for t in plan.tasks}
    after = {t.key: t for t in repaired.tasks}
    assert set(after) == set(before) and touched == ["BE-renew-endpoint"]
    for key in before:
        if key != "BE-renew-endpoint":
            assert after[key].model_dump_json() == before[key].model_dump_json()
    assert repaired.stories == plan.stories  # a task-level finding does not touch the story text
    assert not [n for n, _ in llm.calls if n == "StoryDetailDraft"]
    user = next(u for n, u in llm.calls if n == "StoryRepairDraft")
    assert "may revise: BE-renew-endpoint" in user


def test_repair_cannot_change_a_task_the_finding_does_not_name():
    previous, plan, diff, skeletons = _changed_plan()
    found = []
    repaired, _, touched, _ = repair_update(plan, skeletons, [_blocking("BE-renew-endpoint")], FakeLLM(repair_mode="rogue"),
                                            found, previous, diff)
    assert touched == ["BE-renew-endpoint"]
    assert any(f.check_id == "REF-RESTORE" and "does not name" in f.message for f in found)


def test_story_level_decision_revises_every_conflicting_item():
    previous, plan, diff, skeletons = _changed_plan()
    decision = _blocking("US-loans", "US-loans: renewals are limited to two.", check="G1-FEEDBACK")
    llm = FakeLLM(repair_mode="revise_all")  # the model finds every task in conflict with the decision
    repaired, _, touched, _ = repair_update(plan, skeletons, [decision], llm, [], previous, diff)
    user = next(u for n, u in llm.calls if n == "StoryRepairDraft")
    assert "revise the story ACs and EVERY task of this story that conflicts with it" in user
    assert set(touched) == {"US-loans", *(t.key for t in plan.tasks)}  # all of them, not a minimal set
    assert repaired.stories[0] != plan.stories[0]  # the story's ACs are revised too


def test_story_level_decision_keeps_tasks_that_do_not_conflict():
    previous, plan, diff, skeletons = _changed_plan()
    decision = _blocking("US-loans", "US-loans: renewals are limited to two.", check="G1-FEEDBACK")
    repaired, _, touched, _ = repair_update(plan, skeletons, [decision], FakeLLM(), [], previous, diff)
    assert set(touched) == {"US-loans", plan.tasks[0].key}  # only what the model reported as conflicting
    for t in repaired.tasks[1:]:
        assert t in plan.tasks


def test_new_task_only_when_returned_and_never_closing_published_tasks():
    previous, plan, diff, skeletons = _changed_plan()
    added, _, _, _ = repair_update(plan, skeletons, [_blocking("US-loans")], FakeLLM(repair_mode="new_task"), [], previous, diff)
    new = [t for t in added.tasks if t.key not in {x.key for x in plan.tasks}]
    assert len(new) == 1 and new[0].key.startswith("FE-")
    found = []
    closed, _, _, _ = repair_update(added, skeletons, [_blocking(new[0].key)], FakeLLM(repair_mode="close_new"), found,
                                    previous, diff)
    assert new[0].key not in {t.key for t in closed.tasks}  # created in this run -> may be removed
    assert {t.key for t in plan.tasks} <= {t.key for t in closed.tasks}  # published tasks are never closed here


def test_g1_feedback_in_an_update_run_uses_the_task_level_path(tmp_path):
    from langgraph.checkpoint.memory import MemorySaver
    from langgraph.types import Command
    from rich.console import Console

    from tests.test_pipeline import GENERIC_PRD

    prd = tmp_path / "prd.md"
    out = tmp_path / "out"
    prd.write_text(GENERIC_PRD, encoding="utf-8")
    build_graph(FakeLLM(), console=Console(quiet=True)).invoke({"prd_path": str(prd), "out_dir": str(out), "auto_yes": True})
    v1 = TicketPlan.model_validate_json((out / "plan.json").read_text(encoding="utf-8"))
    prd.write_text(GENERIC_PRD.replace("- Cancel a reservation.", "- Cancel an open reservation."), encoding="utf-8")
    llm = FakeLLM()
    graph = build_graph(llm, console=Console(quiet=True), checkpointer=MemorySaver())
    config = {"configurable": {"thread_id": "fb"}}
    first = graph.invoke({"prd_path": str(prd), "out_dir": str(out)}, config)
    story = next(s.key for s in first["plan"].stories if s.key not in first["carried"])
    before = {t.key: t for t in first["plan"].tasks}
    graph.invoke(Command(resume={"action": "feedback", "text": f"{story}: holds expire after 3 days."}), config)
    final = graph.invoke(Command(resume={"action": "approve"}), config)
    assert not [n for n, _ in llm.calls if n == "StoryDetailDraft"]  # never a full regeneration in an update run
    assert [n for n, _ in llm.calls].count("StoryRepairDraft") == 1
    after = {t.key: t for t in final["plan"].tasks}
    changed = [k for k in after if before.get(k) != after[k]]
    assert len(changed) == 1  # one task revised for the decision; every other task byte-for-byte
    assert all(after[k] == v1_t for k, v1_t in {t.key: t for t in v1.tasks}.items()
               if k in after and next(t for t in v1.tasks if t.key == k).story_key != story)


def test_update_and_repair_calls_use_the_revision_role():
    previous, plan, diff, skeletons = _changed_plan()
    llm = FakeLLM()
    _update(previous, [_req(TEXTS[0]), _req(TEXTS[1]), _req(CHANGED), _req(TEXTS[3])], llm)
    repair_update(plan, skeletons, [_blocking("BE-renew-endpoint")], llm, [], previous, diff)
    roles = {n: r for (n, _), r in zip(llm.calls, llm.roles) if n in ("StoryUpdateDraft", "StoryRepairDraft")}
    assert roles == {"StoryUpdateDraft": "revision", "StoryRepairDraft": "revision"}



# --------------------------------------------------------------------------- open findings survive G1 resets


def test_open_findings_survive_a_g1_reset_until_the_critic_confirms_them(tmp_path):
    """A finding that is not confirmed fixed stays open across rounds, keep-best and a G1 reset (bug 1)."""
    from langgraph.checkpoint.memory import MemorySaver
    from langgraph.types import Command
    from rich.console import Console

    from tests.test_pipeline import GENERIC_PRD

    prd = tmp_path / "prd.md"
    prd.write_text(GENERIC_PRD, encoding="utf-8")
    clean = build_graph(FakeLLM(), console=Console(quiet=True)).invoke(
        {"prd_path": str(prd), "out_dir": str(tmp_path / "c"), "auto_yes": True})
    story = clean["plan"].stories[0].key
    lost = _blocking(story, "The create form has no Status field, so In Progress is unreachable.")
    # call 0 raises it; calls 1-3 do not mention it and do not confirm it (critic silent); call 4 confirms it.
    llm = FakeLLM(critic_findings=[[lost]], unresolved_calls={1, 2, 3})
    graph = build_graph(llm, console=Console(quiet=True), checkpointer=MemorySaver())
    config = {"configurable": {"thread_id": "ledger"}}
    first = graph.invoke({"prd_path": str(prd), "out_dir": str(tmp_path / "o")}, config)
    open_before = [f for f in first["plan_report"].findings if "In Progress is unreachable" in f.message]
    assert first["status"].value == "NEEDS_REVIEW" and open_before  # still open: the critic never confirmed a fix
    other = clean["plan"].stories[-1].key
    second = graph.invoke(Command(resume={"action": "feedback", "text": f"{other}: holds expire after 3 days."}), config)
    assert any("In Progress is unreachable" in f.message for f in second["plan_report"].findings)  # survived reset
    assert any(open_before[0].finding_id in ids for ids in llm.open_seen[1:])  # the critic was asked to verify it
    third = graph.invoke(Command(resume={"action": "feedback", "text": f"{story}: add a Status field to the form."}), config)
    assert not any("In Progress is unreachable" in f.message for f in third["plan_report"].findings)  # confirmed fixed
    assert third["status"].value == "PASS"


def test_plan_wide_decision_is_checked_by_the_critic_against_the_whole_plan(tmp_path):
    from langgraph.checkpoint.memory import MemorySaver
    from langgraph.types import Command
    from rich.console import Console

    from tests.test_pipeline import GENERIC_PRD

    prd = tmp_path / "prd.md"
    prd.write_text(GENERIC_PRD, encoding="utf-8")
    llm = FakeLLM()
    graph = build_graph(llm, console=Console(quiet=True), checkpointer=MemorySaver())
    config = {"configurable": {"thread_id": "wide"}}
    graph.invoke({"prd_path": str(prd), "out_dir": str(tmp_path / "o")}, config)
    calls_before = len(llm.calls)
    graph.invoke(Command(resume={"action": "feedback", "text": "New loans start as Open."}), config)
    after = llm.calls[calls_before:]
    assert not [n for n, _ in after if n in ("StoryDetailDraft", "StoryRepairDraft")]  # no blanket repair of every story
    critic = [u for (n, u) in after if n == "ReviewReport"]
    assert critic and "Review the whole plan." in critic[0] and "New loans start as Open." in critic[0]


# --------------------------------------------------------------------------- citations from findings / decisions


from agent import cited_requirements  # noqa: E402


def test_cited_requirements_takes_only_existing_ids():
    reqs = [_req(t) for t in TEXTS]
    f = _blocking("US-loans", f"The story must cite {reqs[2].id} and also R-deadbeef, which does not exist.")
    assert cited_requirements(f, reqs) == [reqs[2].id]
    f2 = ReviewFinding(check_id="CRIT-MISSING", severity=Severity.blocking, item_key="US-loans", message="x",
                       requirement_ids=[reqs[0].id, "R-00000000"])
    assert cited_requirements(f2, reqs) == [reqs[0].id]


def test_cited_requirements_by_quote_but_not_by_paraphrase():
    reqs = [_req(t) for t in TEXTS]
    by_quote = _blocking("US-loans", f'The PRD says "{TEXTS[3]}" but no AC covers it.')
    assert cited_requirements(by_quote, reqs) == [reqs[3].id]
    paraphrase = _blocking("US-loans", "Late items should be shown somewhere.")
    assert cited_requirements(paraphrase, reqs) == []


def test_repair_adds_cited_ids_to_the_story_and_the_revised_task():
    previous, plan, diff, skeletons = _changed_plan()
    msg_id = plan.requirements[3].id  # cited by FE-overdue-list only, not by BE-renew-endpoint
    decision = _blocking("BE-renew-endpoint", f"BE-renew-endpoint must also show overdue loans ({msg_id}).",
                         check="G1-FEEDBACK")
    repaired, new_skeletons, _, _ = repair_update(plan, skeletons, [decision], FakeLLM(), [], previous, diff)
    renew = next(t for t in repaired.tasks if t.key == "BE-renew-endpoint")
    assert msg_id in renew.requirement_ids  # added by code, not by the model
    assert msg_id in repaired.stories[0].requirement_ids
    assert msg_id in next(s for s in new_skeletons if s.key == "US-loans").requirement_ids
    others = [t for t in repaired.tasks if t.key != "BE-renew-endpoint"]
    assert others == [t for t in plan.tasks if t.key != "BE-renew-endpoint"]  # not added to tasks it does not cover


# --------------------------------------------------------------------------- P12 plain language


from tools.validators import check_p12_plain_language  # noqa: E402


def test_p12_flags_internal_notes():
    plan = _four_task_story()
    rid = plan.requirements[0].id
    story = plan.stories[0].model_copy(update={"edge_cases": [
        f"The PRD text for this story does not include the requirement ID ({rid}).",
        "Editing a Completed task: the reviewer decision does not say.",
        "See BE-renew-endpoint for details.",
        "The critic found this unclear.",
        "The PRD does not state the maximum number of renewals (open question)."]})
    findings = check_p12_plain_language(plan.model_copy(update={"stories": [story]}))
    assert [f.check_id for f in findings] == ["P12"] * 4 and all(f.severity.value == "blocking" for f in findings)
    assert "edge case 5" not in " ".join(f.message for f in findings)  # a plain open question is fine


def test_p12_passes_plain_text_and_checks_tasks():
    plan = _four_task_story()
    assert check_p12_plain_language(plan) == []
    bad = plan.model_copy(update={"tasks": [plan.tasks[0].model_copy(update={"description": "Implements R-4a5d9f72."}),
                                            *plan.tasks[1:]]})
    assert [f.item_key for f in check_p12_plain_language(bad)] == [plan.tasks[0].key]


def test_story_prompts_carry_the_plain_language_rule():
    from agent import system_prompt

    for name in ("detail_stories", "update_story", "repair_update_story"):
        assert "Plain product language" in system_prompt(name) and "Requirement IDs belong only in" in system_prompt(name)


def test_finding_fix_is_a_cause_and_survives_the_churn_guard():
    previous = _four_task_story()
    fixed = previous.model_copy(update={"stories": [previous.stories[0].model_copy(update={"edge_cases": ["Plain."]})]})
    guarded = churn_guard(fixed, previous, None, set(), [], finding_keys={"US-loans"})
    assert guarded.stories[0].edge_cases == ["Plain."]  # caused by a finding fix: kept
    restored = churn_guard(fixed, previous, None, set(), [])
    assert restored.stories[0] == previous.stories[0]  # no cause: restored
    causes = change_causes(fixed, previous, None, set(), {"US-loans": ["finding P12"]})
    assert causes["US-loans"] == ["finding P12"]


# --------------------------------------------------------------------------- field-level repairs


from agent import apply_story_edits, plain_rewrite  # noqa: E402
from schemas import CriterionEditDraft, LineEditDraft, StoryEditsDraft  # noqa: E402


def _with_notes(plan):
    rid = plan.requirements[1].id
    story = plan.stories[0].model_copy(update={
        "edge_cases": ["A member renews twice: the second renewal is refused.",
                       "Renewing a returned loan: handled as in BE-borrow-endpoint.",
                       "Last Updated Date is set on every successful renewal."],
        "definition_of_done": ["Renew endpoint returns documented error responses.",
                               f"Due date stored as in {rid}."]})
    task = plan.tasks[0].model_copy(update={"definition_of_done": ["borrow done", "The critic finding is resolved."]})
    return plan.model_copy(update={"stories": [story], "tasks": [task, *plan.tasks[1:]]}), rid


def test_p12_repair_rewrites_only_the_flagged_lines_and_keeps_the_rest_byte_for_byte():
    plan, rid = _with_notes(_four_task_story())
    findings = check_p12_plain_language(plan)
    assert sorted(f.item_key for f in findings) == sorted(["US-loans", "US-loans", plan.tasks[0].key])
    llm = FakeLLM()
    skeletons = [StorySkeleton(key="US-loans", title="Manage loans", requirement_ids=plan.stories[0].requirement_ids)]
    fixed, _, touched, = plain_rewrite(plan, skeletons, findings, llm, [])
    assert set(touched) == {"US-loans", plan.tasks[0].key}
    assert [n for n, _ in llm.calls] == ["PlainRewriteDraft"] and llm.roles == ["revision"]  # one small call, no story rewrite
    before, after = plan.stories[0], fixed.stories[0]
    assert after.edge_cases[0] == before.edge_cases[0] and after.edge_cases[2] == before.edge_cases[2]
    assert after.edge_cases[1] != before.edge_cases[1] and "BE-" not in after.edge_cases[1]
    assert after.definition_of_done[0] == before.definition_of_done[0]
    assert rid not in after.definition_of_done[1]
    for name in ("title", "as_a", "i_want", "so_that", "business_description", "business_value",
                 "acceptance_criteria", "dependencies"):
        assert getattr(after, name) == getattr(before, name)
    assert after.requirement_ids == before.requirement_ids  # the cited ID was already on the story
    task_before, task_after = plan.tasks[0], fixed.tasks[0]
    assert task_after.definition_of_done[0] == "borrow done" and "critic" not in task_after.definition_of_done[1]
    assert task_after.model_dump(exclude={"definition_of_done"}) == task_before.model_dump(exclude={"definition_of_done"})
    for t_before, t_after in zip(plan.tasks[1:], fixed.tasks[1:]):
        assert t_after.model_dump_json() == t_before.model_dump_json()
    assert check_p12_plain_language(fixed) == []


def test_p12_repair_moves_a_named_requirement_id_into_the_citations():
    plan, rid = _with_notes(_four_task_story())
    task = plan.tasks[0]
    assert rid not in task.requirement_ids
    plan = plan.model_copy(update={"tasks": [task.model_copy(update={"description": f"Do borrow ({rid})."}),
                                             *plan.tasks[1:]]})
    findings = [f for f in check_p12_plain_language(plan) if f.item_key == task.key]
    fixed, _, _ = plain_rewrite(plan, [], findings, FakeLLM(), [])
    assert fixed.tasks[0].requirement_ids == [*task.requirement_ids, rid] and rid not in fixed.tasks[0].description


def test_story_level_repair_edits_only_the_named_lines():
    previous, plan, diff, skeletons = _changed_plan()
    plan, _ = _with_notes(plan)
    repaired, _, touched, _ = repair_update(plan, skeletons, [_blocking("US-loans")], FakeLLM(), [], previous, diff)
    before, after = plan.stories[0], repaired.stories[0]
    assert "US-loans" in touched
    assert after.acceptance_criteria[0] != before.acceptance_criteria[0]  # edited: AC 1 replaced
    assert after.acceptance_criteria[1:] == before.acceptance_criteria[1:]
    assert after.edge_cases == before.edge_cases  # not named by an edit: byte-for-byte
    assert after.definition_of_done == [*before.definition_of_done, "Fixed"]  # one line added, none dropped
    for name in ("as_a", "i_want", "so_that", "business_description", "business_value"):
        assert getattr(after, name) == getattr(before, name)


def test_story_edits_with_a_bad_number_are_ignored():
    story = _four_task_story().stories[0]
    found = []
    edits = StoryEditsDraft(definition_of_done=[LineEditDraft(op="remove", number=9)],
                            acceptance_criteria=[CriterionEditDraft(op="replace", number=2)])
    assert apply_story_edits(story, edits, found) == story
    assert len([f for f in found if f.check_id == "REF-RESTORE"]) == 2
    edits = StoryEditsDraft(acceptance_criteria=[CriterionEditDraft(op="remove", number=1)])
    assert apply_story_edits(story, edits, []).acceptance_criteria == story.acceptance_criteria[1:]


def test_p12_rewrite_names_the_notes_and_retries_once_when_a_note_is_left_in():
    plan, _ = _with_notes(_four_task_story())
    llm = FakeLLM()
    llm.plain_sloppy_once = True
    fixed, _, _ = plain_rewrite(plan, [], check_p12_plain_language(plan), llm, [])
    users = [u for n, u in llm.calls if n == "PlainRewriteDraft"]
    assert len(users) == 2 and "remove: a ticket key" in users[0]
    assert check_p12_plain_language(fixed) == []
