"""Epic traceability: the epic cites requirements, appears in the coverage matrix, and P13 is repaired field-level."""

from agent import remap_project, repair_epic
from schemas import BusinessGoal, RequirementDiff
from tests.fake_llm import FakeLLM
from tests.test_task_level_update import _four_task_story, _req
from tools import renderer
from tools.validators import check_p13_epic_grounding


def _cited_epic(plan):
    rid = plan.requirements[0].id
    epic = plan.project.model_copy(update={
        "requirement_ids": [rid], "business_goals": [BusinessGoal(text="g", requirement_ids=[rid])]})
    return plan.model_copy(update={"project": epic}), rid


def test_epic_appears_in_the_coverage_matrix_and_its_issue_lists_its_requirements():
    plan, rid = _cited_epic(_four_task_story())
    assert plan.project.key in renderer.citations(plan)[rid]
    report = renderer.render_validation_report(plan, [], "PASS", {})
    row = next(line for line in report.splitlines() if line.startswith(f"| `{rid}`"))
    assert f"`{plan.project.key}`" in row
    body = renderer.render_bodies(plan)[plan.project.key]
    assert "## Requirements" in body and rid in body and "- g" in body


def test_p13_repair_adds_citations_and_keeps_the_epic_text_byte_for_byte():
    plan = _four_task_story()  # its epic cites nothing
    findings = check_p13_epic_grounding(plan)
    assert [f.check_id for f in findings] == ["P13", "P13"]
    llm = FakeLLM()
    fixed, touched = repair_epic(plan, findings, llm, [])
    assert touched == [plan.project.key] and llm.roles == ["revision"]
    epic, before = fixed.project, plan.project
    assert [g.text for g in epic.business_goals] == [g.text for g in before.business_goals]
    assert (epic.key, epic.title, epic.scope, epic.story_keys) == (before.key, before.title, before.scope,
                                                                    before.story_keys)
    assert epic.requirement_ids == [plan.requirements[0].id]
    assert check_p13_epic_grounding(fixed) == []
    assert fixed.stories == plan.stories and fixed.tasks == plan.tasks


def test_update_run_epic_citations_follow_the_requirement_diff():
    plan, rid = _cited_epic(_four_task_story())
    new_id = _req("Members can borrow two books.").id
    moved = remap_project(plan.project, RequirementDiff(changed=[(rid, new_id)]))
    assert moved.requirement_ids == [new_id] and moved.business_goals[0].requirement_ids == [new_id]
    assert moved.business_goals[0].text == plan.project.business_goals[0].text
    gone = remap_project(plan.project, RequirementDiff(removed=[rid]))
    assert gone.requirement_ids == [] and gone.business_goals[0].requirement_ids == []  # P13 then flags it
