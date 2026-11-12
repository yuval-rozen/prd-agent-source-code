"""One positive and one negative test per check_id (SPEC §15). Fixtures use a generic library domain."""

import pytest

from schemas import (
    AcceptanceCriterion,
    DerivedReason,
    Label,
    ParentProject,
    ReqKind,
    Requirement,
    Size,
    TechnicalTask,
    TicketPlan,
    Track,
    UserStory,
    requirement_id_base,
)
from tools import validators as v
from tools.file_reader import load_prd
from tools.prd_search import PRDIndex

PRD = "# Library\n\n## Loans\n\n- Members can borrow a book.\n- Each loan stores a due date.\n\nThe team may pick any database.\n"


@pytest.fixture
def parsed(tmp_path):
    f = tmp_path / "prd.md"
    f.write_text(PRD, encoding="utf-8")
    return load_prd(f)


def _req(text, kind, unit_ids, **kw):
    return Requirement(id=requirement_id_base(text), unit_ids=unit_ids, source_quote=text, section_path=["Library", "Loans"],
                       kind=kind, statement=text, **kw)


@pytest.fixture
def reqs(parsed):
    u = [x.id for x in parsed.units]
    return [
        _req("Members can borrow a book.", ReqKind.functional, [u[0]]),
        _req("Each loan stores a due date.", ReqKind.data_model, [u[1]]),
        _req("The team may pick any database.", ReqKind.decision_open, [u[2]]),
    ]


def _ac(n=2):
    return [AcceptanceCriterion(given=f"a member with {i} loans", when="they borrow an available book",
                                then=f"the loan count becomes {i + 1}") for i in range(n)]


def _task(key, track, title, reqs_, labels, **kw):
    return TechnicalTask(key=key, story_key=kw.pop("story_key", "US-borrow-book"), title=title, track=track,
                         description="Do it.", size=kw.pop("size", Size.S), requirement_ids=reqs_, labels=labels, **kw)


@pytest.fixture
def plan(reqs):
    r_fun, r_data, r_dec = (r.id for r in reqs)
    story = UserStory(key="US-borrow-book", title="Borrow an available book", as_a="member", i_want="to borrow",
                      so_that="I can read", business_description="d", business_value="v", acceptance_criteria=_ac(),
                      requirement_ids=[r_fun, r_data, r_dec])
    tasks = [
        _task("BE-loans-table-migration", Track.backend, "[BE] Add loans table migration with due date", [r_data],
              [Label.type_task, Label.area_db, Label.prd_agent], touches_db=True),
        _task("BE-borrow-endpoint", Track.backend, "[BE] Add POST /loans endpoint", [r_fun],
              [Label.type_task, Label.area_backend, Label.prd_agent], touches_db=True, blocked_by=["BE-loans-table-migration"]),
        _task("FE-borrow-button", Track.frontend, "[FE] Add Borrow button to the book page", [r_fun],
              [Label.type_task, Label.area_frontend, Label.prd_agent], consumes_api=True, blocked_by=["BE-borrow-endpoint"]),
        _task("QA-borrow-test-suite", Track.qa_general, "[QA] Add test suite for borrowing", [],
              [Label.type_task, Label.area_qa, Label.prd_agent], derived_reason=DerivedReason.testing),
        _task("BE-database-choice-spike", Track.backend, "[BE] Decide which database stores loans", [r_dec],
              [Label.type_spike, Label.area_backend, Label.prd_agent], derived_reason=DerivedReason.decision_spike,
              definition_of_done=["Decision documented with rationale and trade-offs"]),
    ]
    project = ParentProject(key="EPIC-library", title="Library lending", scope="Loans", business_goals=["More loans"],
                            story_keys=["US-borrow-book"])
    return TicketPlan(prd_hash="h", project=project, stories=[story], tasks=tasks, requirements=reqs)


def _ids(findings):
    return [f.check_id for f in findings]


def _mut(plan, **updates):
    return TicketPlan.model_validate({**plan.model_dump(), **updates})


def _task_update(plan, key, **changes):
    tasks = [t.model_copy(update=changes) if t.key == key else t for t in plan.tasks]
    return plan.model_copy(update={"tasks": tasks})


def test_valid_plan_has_no_blocking_findings(plan, reqs, parsed):
    assert [f for f in v.check_plan(plan) if f.severity.value == "blocking"] == []
    assert v.check_requirements(reqs, parsed) == []


# --------------------------------------------------------------------------- R1 / R2


def test_r1_positive(reqs, parsed):
    assert v.check_r1_grounding(reqs, PRDIndex(parsed), 90) == []


def test_r1_negative(reqs, parsed):
    bad = reqs[0].model_copy(update={"source_quote": "Members can reserve a parking spot."})
    assert _ids(v.check_r1_grounding([bad], PRDIndex(parsed), 90)) == ["R1"]


def test_r2_positive(reqs, parsed):
    assert v.check_r2_unit_coverage(reqs, parsed) == []


def test_r2_negative_uncovered_unit(reqs, parsed):
    assert _ids(v.check_r2_unit_coverage(reqs[:2], parsed)) == ["R2"]


def test_r2_negative_list_item_marked_context(reqs, parsed):
    ctx = reqs[0].model_copy(update={"kind": ReqKind.context_only, "context_reason": "intro"})
    assert "list items state requirements" in v.check_r2_unit_coverage([ctx, *reqs[1:]], parsed)[0].message


def test_r2_negative_context_without_reason(reqs, parsed):
    ctx = reqs[2].model_copy(update={"kind": ReqKind.context_only})  # a sentence unit, so only the reason is missing
    assert [f.message for f in v.check_r2_unit_coverage([*reqs[:2], ctx], parsed)] == ["context_only requirement has no reason."]


# --------------------------------------------------------------------------- P1 - P11


def test_p1(plan):
    assert v.check_p1_coverage(plan) == []
    story = plan.stories[0].model_copy(update={"requirement_ids": plan.stories[0].requirement_ids[:2]})
    no_spike = [t for t in plan.tasks if t.key != "BE-database-choice-spike"]
    assert _ids(v.check_p1_coverage(plan.model_copy(update={"stories": [story], "tasks": no_spike}))) == ["P1"]


def test_p2(plan):
    assert v.check_p2_citations(plan) == []
    assert _ids(v.check_p2_citations(_task_update(plan, "QA-borrow-test-suite", derived_reason=None))) == ["P2"]
    assert _ids(v.check_p2_citations(_task_update(plan, "FE-borrow-button", requirement_ids=["R-00000000"]))) == ["P2"]


def test_p3(plan):
    assert v.check_p3_acceptance_criteria(plan) == []
    one = plan.stories[0].model_copy(update={"acceptance_criteria": _ac(1)})
    assert _ids(v.check_p3_acceptance_criteria(plan.model_copy(update={"stories": [one]}))) == ["P3"]
    vague = plan.stories[0].model_copy(update={"acceptance_criteria": [
        *_ac(1), AcceptanceCriterion(given="a member", when="they borrow", then="it works correctly")]})
    assert "vague" in v.check_p3_acceptance_criteria(plan.model_copy(update={"stories": [vague]}))[0].message


def test_p3_quantified_vague_word_is_allowed(plan):
    quantified = plan.stories[0].model_copy(update={"acceptance_criteria": [
        *_ac(1), AcceptanceCriterion(given="a member", when="they open the list", then="it loads fast, within 2 seconds")]})
    assert v.check_p3_acceptance_criteria(plan.model_copy(update={"stories": [quantified]})) == []


def test_p4(plan):
    assert v.check_p4_tracks(plan) == []
    no_be = _task_update(plan, "BE-loans-table-migration", requirement_ids=[])
    assert _ids(v.check_p4_tracks(no_be)) == ["P4"]
    no_qa = plan.model_copy(update={"tasks": [t for t in plan.tasks if t.track is not Track.qa_general]})
    assert _ids(v.check_p4_tracks(no_qa)) == ["P4"]


def test_p4_frontend_requirement_needs_frontend_task(plan):
    reqs = [r.model_copy(update={"kind": ReqKind.frontend}) if r.kind is ReqKind.functional else r for r in plan.requirements]
    assert v.check_p4_tracks(plan.model_copy(update={"requirements": reqs})) == []  # FE-borrow-button cites it
    no_fe = plan.model_copy(update={"requirements": reqs, "tasks": [t for t in plan.tasks if t.track is not Track.frontend]})
    assert _ids(v.check_p4_tracks(no_fe)) == ["P4"]


def test_p5(plan):
    assert v.check_p5_labels(plan) == []
    two_areas = _task_update(plan, "FE-borrow-button", labels=[Label.type_task, Label.area_frontend, Label.area_qa, Label.prd_agent])
    assert _ids(v.check_p5_labels(two_areas)) == ["P5"]
    story = plan.stories[0].model_copy(update={"labels": [Label.type_task, Label.prd_agent]})
    assert _ids(v.check_p5_labels(plan.model_copy(update={"stories": [story]}))) == ["P5"]


def test_p6(plan):
    assert v.check_p6_duplicate_titles(plan) == []
    dup = _task_update(plan, "FE-borrow-button", title="[BE] Add POST /loans endpoint")
    findings = v.check_p6_duplicate_titles(dup)
    assert _ids(findings) == ["P6"] and findings[0].item_key == "FE-borrow-button"


def test_p6_catches_duplicate_task_across_stories(plan):
    second = plan.stories[0].model_copy(update={"key": "US-return-book", "title": "Return a borrowed book"})
    copy = plan.tasks[2].model_copy(update={"key": "FE-borrow-button-2", "story_key": "US-return-book"})
    dup = plan.model_copy(update={"stories": [plan.stories[0], second], "tasks": [*plan.tasks, copy]})
    assert [(f.check_id, f.item_key) for f in v.check_p6_duplicate_titles(dup)] == [("P6", "FE-borrow-button-2")]


def test_p7(plan):
    assert v.check_p7_dependencies(plan) == []
    unknown = _task_update(plan, "FE-borrow-button", blocked_by=["BE-nope"])
    assert "unknown" in v.check_p7_dependencies(unknown)[0].message
    cycle = _task_update(plan, "BE-loans-table-migration", blocked_by=["FE-borrow-button"])
    assert any("cycle" in f.message for f in v.check_p7_dependencies(cycle))


def test_p7_warnings(plan):
    no_api_blocker = _task_update(plan, "FE-borrow-button", blocked_by=[])
    f = v.check_p7_dependencies(no_api_blocker)
    assert _ids(f) == ["P7"] and f[0].severity.value == "warning"
    no_db_blocker = _task_update(plan, "BE-borrow-endpoint", blocked_by=[])
    assert [x.severity.value for x in v.check_p7_dependencies(no_db_blocker)] == ["warning"]


def test_p8(plan):
    r_fun = plan.requirements[0].id
    constraint = Requirement(id=requirement_id_base("All screens show errors inline."), unit_ids=plan.requirements[0].unit_ids,
                             source_quote="All screens show errors inline.", section_path=["Library"], kind=ReqKind.constraint,
                             statement="All screens show errors inline.", applies_to_requirement_ids=[r_fun])
    with_c = plan.model_copy(update={"requirements": [*plan.requirements, constraint]})
    assert _ids(v.check_p8_constraints(with_c)) == ["P8"]
    story = with_c.stories[0].model_copy(update={"requirement_ids": [*with_c.stories[0].requirement_ids, constraint.id]})
    assert v.check_p8_constraints(with_c.model_copy(update={"stories": [story]})) == []


def test_p9(plan):
    assert v.check_p9_decisions(plan) == []
    no_rationale = _task_update(plan, "BE-database-choice-spike", definition_of_done=["Pick one"])
    assert _ids(v.check_p9_decisions(no_rationale)) == ["P9"]
    no_spike = plan.model_copy(update={"tasks": [t for t in plan.tasks if t.key != "BE-database-choice-spike"]})
    assert _ids(v.check_p9_decisions(no_spike)) == ["P9"]


def test_p10(plan):
    assert v.check_p10_sizing(plan) == []
    big = _task_update(plan, "BE-borrow-endpoint", size=Size.L)
    assert [(f.check_id, f.severity.value) for f in v.check_p10_sizing(big)] == [("P10", "warning")]


def test_p11(plan):
    assert v.check_p11_titles(plan) == []
    long = _task_update(plan, "BE-borrow-endpoint", title="[BE] " + "x" * 90)
    assert _ids(v.check_p11_titles(long)) == ["P11"]
    prefix = _task_update(plan, "BE-borrow-endpoint", title="[FE] Add POST /loans endpoint")
    assert _ids(v.check_p11_titles(prefix)) == ["P11"]
    generic = _task_update(plan, "BE-borrow-endpoint", title="[BE] Backend work")
    assert _ids(v.check_p11_titles(generic)) == ["P11"]
