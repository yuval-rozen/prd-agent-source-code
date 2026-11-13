"""Data contracts for the pipeline (SPEC §9).

Pydantic validators enforce only *local* rules (key formats, non-empty Given/When/Then, unique labels,
non-empty titles). Title length is P11 only. Cross-item rules (coverage, AC counts, tracks, dependencies...) are validators.py checks
that produce ReviewFindings, so the repair loop can fix them instead of failing on parse.
"""

from __future__ import annotations

import hashlib
import re
import string
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, StringConstraints, model_validator

# --------------------------------------------------------------------------- enums


class ReqKind(StrEnum):
    functional = "functional"
    data_model = "data_model"
    validation_rule = "validation_rule"
    frontend = "frontend"
    backend = "backend"
    non_functional = "non_functional"
    constraint = "constraint"
    decision_open = "decision_open"
    context_only = "context_only"


class Track(StrEnum):
    frontend = "frontend"
    backend = "backend"
    qa_general = "qa_general"


TRACK_PREFIX: dict[Track, str] = {Track.frontend: "[FE]", Track.backend: "[BE]", Track.qa_general: "[QA]"}


class Label(StrEnum):
    type_epic = "type:epic"
    type_story = "type:story"
    type_task = "type:task"
    type_spike = "type:spike"
    area_frontend = "area:frontend"
    area_backend = "area:backend"
    area_qa = "area:qa"
    area_db = "area:db"
    area_infra = "area:infra"
    prd_agent = "prd-agent"


class Size(StrEnum):
    S = "S"
    M = "M"
    L = "L"


class Severity(StrEnum):
    blocking = "blocking"
    warning = "warning"


class Status(StrEnum):
    PASS = "PASS"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    ABORTED = "ABORTED"


class Verdict(StrEnum):
    pass_ = "pass"
    fail = "fail"


class DerivedReason(StrEnum):
    testing = "testing"
    migration = "migration"
    scaffolding = "scaffolding"
    decision_spike = "decision_spike"


class UnitKind(StrEnum):
    bullet = "bullet"
    sentence = "sentence"
    table_row = "table_row"


class SyncActionType(StrEnum):
    create = "create"
    update = "update"
    close = "close"
    link = "link"  # add a native GitHub sub-issue link: payload {"parent": <parent key>}
    unchanged = "unchanged"


# --------------------------------------------------------------------------- ID helpers

_SLUG = r"[a-z0-9]+(?:-[a-z0-9]+)*"
REQ_ID_RE = re.compile(r"^R-[0-9a-f]{8}(?:-[2-9]|-[1-9][0-9]+)?$")
UNIT_ID_RE = re.compile(r"^U-[0-9a-f]{6}-[0-9a-f]{8}(?:-[2-9]|-[1-9][0-9]+)?$")
EPIC_KEY_RE = re.compile(rf"^EPIC-{_SLUG}$")
STORY_KEY_RE = re.compile(rf"^US-{_SLUG}$")
TASK_KEY_RE = re.compile(rf"^(?:FE|BE|QA)-{_SLUG}$")

_BULLET_PREFIX = re.compile(r"^\s*(?:[-*+•▪◦●]|\d+[.)]|[a-zA-Z][.)])\s+")
_PUNCT_TABLE = str.maketrans({c: " " for c in string.punctuation + "“”‘’–—…•·"})


def short_hash(text: str, length: int = 8) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:length]


def normalize_quote(text: str) -> str:
    """Normalize a quote for ID derivation: lowercase, strip bullets and punctuation, collapse whitespace."""
    text = _BULLET_PREFIX.sub("", text.strip())
    text = text.lower().translate(_PUNCT_TABLE)
    return " ".join(text.split())


def requirement_id_base(source_quote: str) -> str:
    return f"R-{short_hash(normalize_quote(source_quote))}"


def assign_requirement_ids(quotes: list[str]) -> list[str]:
    """Content-derived IDs in document order; repeats of the same normalized quote get -2, -3, ..."""
    seen: dict[str, int] = {}
    ids: list[str] = []
    for quote in quotes:
        base = requirement_id_base(quote)
        seen[base] = seen.get(base, 0) + 1
        ids.append(base if seen[base] == 1 else f"{base}-{seen[base]}")
    return ids


def slugify(text: str, max_words: int = 6) -> str:
    words = normalize_quote(text).split()[:max_words]
    return "-".join(re.sub(r"[^a-z0-9]", "", w) for w in words if re.sub(r"[^a-z0-9]", "", w)) or "item"


# --------------------------------------------------------------------------- reusable field types


def _matches(pattern: re.Pattern[str], what: str):
    def check(value: str) -> str:
        if not pattern.match(value):
            raise ValueError(f"invalid {what}: {value!r}")
        return value

    return check


def _unique_labels(labels: list[Label]) -> list[Label]:
    if len(labels) != len(set(labels)):
        raise ValueError(f"duplicate labels: {[str(lb) for lb in labels]}")
    return labels


ReqId = Annotated[str, AfterValidator(_matches(REQ_ID_RE, "requirement id"))]
UnitId = Annotated[str, AfterValidator(_matches(UNIT_ID_RE, "unit id"))]
EpicKey = Annotated[str, AfterValidator(_matches(EPIC_KEY_RE, "epic key"))]
StoryKey = Annotated[str, AfterValidator(_matches(STORY_KEY_RE, "story key"))]
TaskKey = Annotated[str, AfterValidator(_matches(TASK_KEY_RE, "task key"))]
NonEmpty = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
# Title length (<= 80) is deliberately NOT enforced here: P11 reports it so the repair loop fixes the one
# long title instead of the whole structured response failing to parse.
TITLE_MAX_LEN = 80
Title = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1),
    Field(description=f"Imperative, specific, names the object, at most {TITLE_MAX_LEN} characters."),
]
Labels = Annotated[list[Label], AfterValidator(_unique_labels)]


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


# --------------------------------------------------------------------------- PRD parsing


class Unit(_Model):
    id: UnitId
    section_path: list[str]
    kind: UnitKind
    text: NonEmpty
    order: int = Field(ge=0, description="Position in the document, 0-based.")


class Section(_Model):
    path: list[str]
    title: str
    level: int = Field(ge=0)
    text: str = ""
    unit_ids: list[UnitId] = Field(default_factory=list)
    children: list[Section] = Field(default_factory=list)


class ParsedPRD(_Model):
    source_path: str
    markdown: str
    prd_hash: str
    root: Section
    units: list[Unit]


# --------------------------------------------------------------------------- requirements


class Requirement(_Model):
    id: ReqId
    unit_ids: list[UnitId] = Field(min_length=1)
    source_quote: NonEmpty
    section_path: list[str]
    kind: ReqKind
    statement: NonEmpty
    applies_to_requirement_ids: list[ReqId] = Field(default_factory=list)
    context_reason: str | None = None


class RequirementList(_Model):
    requirements: list[Requirement]


class RequirementDiff(_Model):
    added: list[ReqId] = Field(default_factory=list)
    changed: list[tuple[ReqId, ReqId]] = Field(default_factory=list, description="(old_id, new_id)")
    removed: list[ReqId] = Field(default_factory=list)


# --------------------------------------------------------------------------- tickets


class AcceptanceCriterion(_Model):
    given: NonEmpty
    when: NonEmpty
    then: NonEmpty


class ParentProject(_Model):
    key: EpicKey
    title: Title
    scope: NonEmpty
    business_goals: list[NonEmpty] = Field(min_length=1)
    story_keys: list[StoryKey] = Field(default_factory=list)
    labels: Labels = Field(default_factory=lambda: [Label.type_epic, Label.prd_agent])


class UserStory(_Model):
    key: StoryKey
    title: Title
    as_a: NonEmpty
    i_want: NonEmpty
    so_that: NonEmpty
    business_description: NonEmpty
    business_value: NonEmpty
    acceptance_criteria: list[AcceptanceCriterion]
    edge_cases: list[NonEmpty] = Field(default_factory=list)
    dependencies: list[StoryKey] = Field(default_factory=list)
    definition_of_done: list[NonEmpty] = Field(default_factory=list)
    requirement_ids: list[ReqId] = Field(default_factory=list)
    labels: Labels = Field(default_factory=lambda: [Label.type_story, Label.prd_agent])


class TechnicalTask(_Model):
    key: TaskKey
    story_key: StoryKey
    title: Title
    track: Track
    description: NonEmpty
    size: Size
    consumes_api: bool = False
    touches_db: bool = False
    blocked_by: list[TaskKey] = Field(default_factory=list)
    requirement_ids: list[ReqId] = Field(default_factory=list)
    derived_reason: DerivedReason | None = None
    definition_of_done: list[NonEmpty] = Field(default_factory=list)
    labels: Labels = Field(default_factory=list)

    @model_validator(mode="after")
    def _key_matches_track(self) -> TechnicalTask:
        expected = {Track.frontend: "FE-", Track.backend: "BE-", Track.qa_general: "QA-"}[self.track]
        if not self.key.startswith(expected):
            raise ValueError(f"task key {self.key!r} must start with {expected!r} for track {self.track}")
        if self.key in self.blocked_by:
            raise ValueError(f"task {self.key!r} cannot block itself")
        return self


class TicketPlan(_Model):
    prd_hash: str
    project: ParentProject
    stories: list[UserStory] = Field(default_factory=list)
    tasks: list[TechnicalTask] = Field(default_factory=list)
    requirements: list[Requirement] = Field(default_factory=list)
    # G1 feedback, kept so a reviewer decision survives the next PRD version (it is context, not ticket content,
    # so it does not enter any content hash).
    reviewer_decisions: list[ReviewFinding] = Field(default_factory=list)

    @model_validator(mode="after")
    def _unique_keys(self) -> TicketPlan:
        keys = [self.project.key, *(s.key for s in self.stories), *(t.key for t in self.tasks)]
        dupes = sorted({k for k in keys if keys.count(k) > 1})
        if dupes:
            raise ValueError(f"duplicate ticket keys: {dupes}")
        return self


# --------------------------------------------------------------------------- review


class ReviewFinding(_Model):
    check_id: NonEmpty
    severity: Severity
    item_key: str | None = None
    requirement_ids: list[str] = Field(default_factory=list)
    message: NonEmpty
    suggested_fix: str | None = None
    finding_id: str | None = Field(default=None, description="Set by code; leave empty.")


class ReviewReport(_Model):
    stage: NonEmpty
    round: int = Field(ge=0)
    verdict: Verdict
    blocking_count: int = 0
    warning_count: int = 0
    findings: list[ReviewFinding] = Field(default_factory=list)
    resolved: list[str] = Field(default_factory=list, description=(
        "IDs of open findings from earlier rounds (given in the input) that the current plan fixes."))
    still_open: list[str] = Field(default_factory=list, description=(
        "IDs of open findings from earlier rounds (given in the input) that are still present."))

    @model_validator(mode="after")
    def _counts(self) -> ReviewReport:
        self.blocking_count = sum(f.severity == Severity.blocking for f in self.findings)
        self.warning_count = sum(f.severity == Severity.warning for f in self.findings)
        self.verdict = Verdict.fail if self.blocking_count else Verdict.pass_
        return self


# --------------------------------------------------------------------------- sync


class SyncAction(_Model):
    key: NonEmpty
    action: SyncActionType
    issue_number: int | None = None
    issue_id: int | None = None  # GitHub's issue id (not its number); needed for sub-issue links
    payload: dict | None = None


# --------------------------------------------------------------------------- LLM-facing drafts
# The LLM fills these via native structured output. Code then derives IDs, normalizes keys, assigns labels
# and links parents, so the LLM never has to reproduce hashes or label vocabularies exactly.


class RequirementDraft(_Model):
    unit_ids: list[str] = Field(description="References of the PRD units this requirement comes from, e.g. ['u3'].")
    source_quote: str = Field(description="Verbatim text copied from the PRD that states the requirement.")
    kind: ReqKind
    statement: str = Field(description="One-sentence, testable restatement. Add nothing the quote does not say.")
    context_reason: str | None = Field(
        default=None, description="Only for kind=context_only: why this unit is context, not a requirement."
    )


class RequirementDraftList(_Model):
    requirements: list[RequirementDraft]


class EpicDraft(_Model):
    title: str
    scope: str = Field(description="What the project covers, in 2-4 sentences, grounded in the PRD.")
    business_goals: list[str] = Field(description="Business goals stated or directly implied by the PRD overview.")


class StorySkeletonDraft(_Model):
    key: str = Field(description="Stable key 'US-<kebab-case-slug>' naming the capability.")
    title: str
    requirement_ids: list[str] = Field(description="IDs of the requirements this story delivers.")


class ConstraintScopeDraft(_Model):
    constraint_id: str = Field(description="ID of a requirement of kind constraint.")
    applies_to_requirement_ids: list[str] = Field(
        description="Requirement IDs the constraint applies to; empty list means it applies globally."
    )


class StoryPlanDraft(_Model):
    epic: EpicDraft
    stories: list[StorySkeletonDraft]
    constraint_scopes: list[ConstraintScopeDraft] = Field(default_factory=list)


class TaskArea(StrEnum):
    frontend = "frontend"
    backend = "backend"
    qa = "qa"
    db = "db"
    infra = "infra"


class TaskDraft(_Model):
    key_slug: str = Field(description="Short kebab-case slug naming the artifact, e.g. 'loans-table-migration'.")
    title: str = Field(description="Starts with [FE], [BE] or [QA] matching the track; names the concrete artifact.")
    track: Track
    area: TaskArea = Field(description="frontend for FE, qa for QA; backend, db or infra for BE tasks.")
    description: str
    size: Size
    consumes_api: bool = Field(description="True if the task calls an API provided by a backend task.")
    touches_db: bool = Field(description="True if the task reads or writes the database schema or data.")
    requirement_ids: list[str] = Field(description="Requirement IDs this task implements; may be empty if derived.")
    derived_reason: DerivedReason | None = Field(
        default=None, description="Required when requirement_ids is empty: why the task exists."
    )
    is_spike: bool = Field(description="True only for a task that resolves an open decision (decision_open).")
    definition_of_done: list[str]


class StoryContentDraft(_Model):
    as_a: str
    i_want: str
    so_that: str
    business_description: str
    business_value: str
    acceptance_criteria: list[AcceptanceCriterion]
    edge_cases: list[str]
    dependencies: list[str] = Field(description="Keys of other stories (from the given list) this story depends on.")
    definition_of_done: list[str]


class StoryDetailDraft(_Model):
    story: StoryContentDraft
    tasks: list[TaskDraft]


class StorySkeleton(_Model):
    key: StoryKey
    title: Title
    requirement_ids: list[ReqId] = Field(default_factory=list)


class TaskRevisionDraft(_Model):
    task_key: str = Field(description="Key of an existing task marked REVISE in the input.")
    task: TaskDraft = Field(description="The complete revised task.")


class AddedPlacementDraft(_Model):
    requirement_id: str = Field(description="ID of a requirement marked ADDED in the input.")
    mode: Literal["revise_existing", "new_task"] = Field(
        description="revise_existing: extend one existing task of this story to cover it; new_task: add a task.")
    task_key: str | None = Field(default=None, description="With revise_existing: the key of the existing task.")
    task: TaskDraft = Field(description="The complete revised task (revise_existing) or the new task (new_task).")


class StoryUpdateDraft(_Model):
    """Update run, one affected story: code already decided which tasks are kept, revised or closed."""

    story: StoryContentDraft
    revised_tasks: list[TaskRevisionDraft] = Field(description="Exactly one entry per task marked REVISE.")
    added_requirements: list[AddedPlacementDraft] = Field(description="Exactly one entry per ADDED requirement.")


class FindingFixDraft(_Model):
    finding: int = Field(description="Number of the finding (or reviewer decision) in the input that this fixes.")
    revised_tasks: list[TaskRevisionDraft] = Field(
        description="Existing tasks changed to fix it; only tasks the input allows for this finding.")
    new_task: TaskDraft | None = Field(default=None, description="Only if no existing task can cover the fix.")
    close_tasks: list[str] = Field(default_factory=list,
                                   description="Keys of tasks created in this run that the fix makes redundant.")


class StoryRepairDraft(_Model):
    """Update run, repair or G1 feedback on one story: change only what the findings need."""

    story: StoryContentDraft
    fixes: list[FindingFixDraft] = Field(description="One entry per finding in the input.")


class DependencyEdgeDraft(_Model):
    task_key: str = Field(description="Key of the task that is blocked.")
    blocked_by: list[str] = Field(description="Keys of the tasks that must be finished first.")


class DependencyPlanDraft(_Model):
    edges: list[DependencyEdgeDraft]


TicketPlan.model_rebuild()
