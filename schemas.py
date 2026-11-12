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
from typing import Annotated

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


class ReviewReport(_Model):
    stage: NonEmpty
    round: int = Field(ge=0)
    verdict: Verdict
    blocking_count: int = 0
    warning_count: int = 0
    findings: list[ReviewFinding] = Field(default_factory=list)

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
    payload: dict | None = None
