import pytest
from pydantic import ValidationError

from schemas import (
    AcceptanceCriterion,
    Label,
    ParentProject,
    Requirement,
    ReqKind,
    ReviewFinding,
    ReviewReport,
    Severity,
    Size,
    TechnicalTask,
    TicketPlan,
    Track,
    UserStory,
    Verdict,
    assign_requirement_ids,
    normalize_quote,
    requirement_id_base,
    slugify,
)

UNIT = "U-abcdef-12345678"


def _story(**kw):
    base = dict(
        key="US-reserve-book", title="Reserve a book from the catalogue", as_a="member",
        i_want="to reserve a book", so_that="I can borrow it later",
        business_description="Members reserve books.", business_value="More loans.",
        acceptance_criteria=[AcceptanceCriterion(given="a free book", when="I reserve it", then="it is held")],
    )
    return UserStory(**{**base, **kw})


def _task(**kw):
    base = dict(
        key="BE-reservations-endpoint", story_key="US-reserve-book", title="[BE] Add POST /reservations endpoint",
        track=Track.backend, description="Create the endpoint.", size=Size.M,
    )
    return TechnicalTask(**{**base, **kw})


# --------------------------------------------------------------------------- requirement IDs


def test_same_text_same_id():
    assert requirement_id_base("Members can reserve a book.") == requirement_id_base("Members can reserve a book.")


def test_id_ignores_case_bullets_punctuation_whitespace():
    a = requirement_id_base("- Members can reserve a book.")
    b = requirement_id_base("  members   CAN reserve a book  ")
    c = requirement_id_base("1. Members can reserve, a book!")
    assert a == b == c


def test_different_text_different_id():
    assert requirement_id_base("Reserve a book.") != requirement_id_base("Return a book.")


def test_id_format():
    rid = requirement_id_base("Reserve a book.")
    assert rid.startswith("R-") and len(rid) == 10


def test_identical_quotes_get_suffixes_in_order():
    ids = assign_requirement_ids(["Same.", "Other.", "Same.", "same"])
    base = requirement_id_base("Same.")
    assert ids[0] == base and ids[2] == f"{base}-2" and ids[3] == f"{base}-3"
    assert ids[1] == requirement_id_base("Other.")


def test_inserting_a_requirement_keeps_existing_ids():
    before = assign_requirement_ids(["A thing.", "B thing.", "C thing."])
    after = assign_requirement_ids(["A thing.", "New thing.", "B thing.", "C thing."])
    assert set(before) <= set(after)


def test_normalize_quote():
    assert normalize_quote("• Title: **mandatory**; can’t be empty.") == "title mandatory can t be empty"


def test_slugify():
    assert slugify("Reserve a Book (online)!") == "reserve-a-book-online"
    assert slugify("!!!") == "item"


# --------------------------------------------------------------------------- local validators


def test_requirement_valid_and_bad_id():
    rid = requirement_id_base("Reserve a book.")
    Requirement(id=rid, unit_ids=[UNIT], source_quote="Reserve a book.", section_path=["F"],
                kind=ReqKind.functional, statement="Members can reserve a book.")
    with pytest.raises(ValidationError):
        Requirement(id="R-1", unit_ids=[UNIT], source_quote="x", section_path=[], kind=ReqKind.functional,
                    statement="x")


def test_requirement_needs_a_unit():
    with pytest.raises(ValidationError):
        Requirement(id=requirement_id_base("x"), unit_ids=[], source_quote="x", section_path=[],
                    kind=ReqKind.functional, statement="x")


def test_gwt_must_be_non_empty():
    AcceptanceCriterion(given="a", when="b", then="c")
    with pytest.raises(ValidationError):
        AcceptanceCriterion(given="a", when="   ", then="c")


@pytest.mark.parametrize("key", ["US-reserve-book", "US-a1"])
def test_story_key_ok(key):
    assert _story(key=key).key == key


@pytest.mark.parametrize("key", ["US_reserve", "us-reserve", "US-", "STORY-1", "US-Reserve"])
def test_story_key_bad(key):
    with pytest.raises(ValidationError):
        _story(key=key)


def test_title_length():
    _story(title="x" * 80)
    with pytest.raises(ValidationError):
        _story(title="x" * 81)
    with pytest.raises(ValidationError):
        _story(title="   ")


def test_labels_unique():
    _story(labels=[Label.type_story, Label.prd_agent])
    with pytest.raises(ValidationError):
        _story(labels=[Label.type_story, Label.type_story])


def test_unknown_label_rejected():
    with pytest.raises(ValidationError):
        _story(labels=["type:bogus"])


def test_task_key_must_match_track():
    _task()
    with pytest.raises(ValidationError):
        _task(key="FE-reservations-endpoint")


def test_task_cannot_block_itself():
    with pytest.raises(ValidationError):
        _task(blocked_by=["BE-reservations-endpoint"])


def test_extra_fields_forbidden():
    with pytest.raises(ValidationError):
        _task(priority="high")


def test_plan_rejects_duplicate_keys():
    project = ParentProject(key="EPIC-library", title="Library catalogue", scope="All of it", business_goals=["Loans"])
    TicketPlan(prd_hash="h", project=project, stories=[_story()], tasks=[_task()])
    with pytest.raises(ValidationError):
        TicketPlan(prd_hash="h", project=project, stories=[_story()], tasks=[_task(), _task()])


def test_plan_roundtrip_json():
    project = ParentProject(key="EPIC-library", title="Library catalogue", scope="All of it", business_goals=["Loans"])
    plan = TicketPlan(prd_hash="h", project=project, stories=[_story()], tasks=[_task()])
    assert TicketPlan.model_validate_json(plan.model_dump_json()) == plan


def test_review_report_counts_and_verdict():
    findings = [
        ReviewFinding(check_id="P3", severity=Severity.blocking, message="vague AC"),
        ReviewFinding(check_id="P10", severity=Severity.warning, message="large task"),
    ]
    r = ReviewReport(stage="check_plan", round=1, verdict=Verdict.pass_, findings=findings)
    assert (r.blocking_count, r.warning_count, r.verdict) == (1, 1, Verdict.fail)
    ok = ReviewReport(stage="check_plan", round=1, verdict=Verdict.fail, findings=findings[1:])
    assert ok.verdict is Verdict.pass_
