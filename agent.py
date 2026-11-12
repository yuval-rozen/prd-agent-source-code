"""The pipeline graph (SPEC §5-§7).

Code orchestrates; the LLM only fills narrow, schema-bound drafts (see schemas.*Draft). Every ID, key and
label is derived by code here, so the plan stays stable and PRD-agnostic. Whenever code has to drop or
replace something the LLM returned (an unknown requirement ID, an unknown story dependency, a mangled unit
reference, an area that does not fit the track, an edge that would close a cycle), it records a
ReviewFinding instead of doing it silently.

S1 load_prd -> S2 extract_requirements -> S3 check_requirements <-> repair_requirements
-> S4 plan_stories -> S5 detail_stories -> S6 map_dependencies -> S7 check_plan <-> repair_plan
-> S8 render_preview -> G1 approve_plan -> [only with --publish] S9 sync_diff -> G2 confirm_diff -> S10 publish
-> S11 summary.
"""

from __future__ import annotations

import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor
from graphlib import CycleError, TopologicalSorter
from pathlib import Path
from typing import Any, Protocol, TypedDict, TypeVar

from jinja2 import Environment, FileSystemLoader, StrictUndefined
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt
from pydantic import BaseModel
from rapidfuzz import fuzz
from rich.console import Console
from rich.table import Table

from schemas import (
    TASK_KEY_RE,
    DependencyPlanDraft,
    Label,
    ParentProject,
    ParsedPRD,
    ReqKind,
    Requirement,
    RequirementDiff,
    RequirementDraftList,
    ReviewFinding,
    ReviewReport,
    Section,
    Severity,
    Status,
    StoryDetailDraft,
    StoryPlanDraft,
    StorySkeleton,
    SyncAction,
    SyncActionType,
    TaskArea,
    TaskDraft,
    TechnicalTask,
    TicketPlan,
    Track,
    UserStory,
    Verdict,
    assign_requirement_ids,
    slugify,
)
from tools import renderer, state_store, validators
from tools.github_tool import publish, sync_diff
from tools.file_reader import iter_sections, load_prd

log = logging.getLogger("prd_agent.agent")
PROMPT_DIR = Path(__file__).resolve().parent / "prompts"
DEFAULT_PARALLEL_CALLS = 4
DEFAULT_MAX_REPAIR_ROUNDS = 3
CRITIC_CHECKS = {"CRIT-MISSING", "CRIT-MISREPRESENTED", "CRIT-UNREQUESTED", "CRIT-UNTESTABLE-AC", "CRIT-CONSTRAINT",
                 "CRIT-OVERLAP"}

T = TypeVar("T", bound=BaseModel)
Findings = list[ReviewFinding]


class StructuredLLM(Protocol):
    def structured(self, schema: type[T], system: str, user: str, *, role: str = "generation") -> T: ...


class AgentState(TypedDict, total=False):
    prd_path: str
    out_dir: str
    parsed: ParsedPRD
    units: list
    requirements: list[Requirement]
    requirement_diff: RequirementDiff | None
    req_report: ReviewReport | None
    req_rounds: int
    req_blocking_history: list[int]
    req_stop_reason: str | None
    previous_plan: TicketPlan | None
    skeletons: list[StorySkeleton]
    plan: TicketPlan
    plan_report: ReviewReport | None
    plan_rounds: int
    plan_blocking_history: list[int]
    plan_stop_reason: str | None
    repaired_keys: list[str]
    best_plan: dict | None
    feedback_findings: Findings
    reviewer_decisions: Findings
    reports: list[ReviewReport]
    reference_findings: Findings
    sync_actions: list[SyncAction]
    publish_decision: str | None
    publish_result: dict | None
    publish: bool
    auto_yes: bool
    force: bool
    status: Status
    approval: str | None
    outputs: list[str]
    started_at: float


def _finding(check_id: str, message: str, item_key: str | None = None, requirement_ids: list[str] | None = None,
             suggested_fix: str | None = None, severity: Severity = Severity.warning) -> ReviewFinding:
    log.warning("[%s] %s%s", check_id, f"{item_key}: " if item_key else "", message)
    return ReviewFinding(check_id=check_id, severity=severity, item_key=item_key,
                         requirement_ids=requirement_ids or [], message=message, suggested_fix=suggested_fix)


def reference_report(findings: Findings) -> ReviewReport:
    return ReviewReport(stage="reference_normalization", round=0, verdict=Verdict.pass_, findings=findings)


def should_repair(report: ReviewReport, rounds_done: int, history: list[int], max_rounds: int) -> tuple[bool, str | None]:
    """SPEC §7: repair while blocking findings remain, rounds < max, and the blocking count keeps decreasing."""
    if report.blocking_count == 0:
        return False, None
    if rounds_done >= max_rounds:
        return False, f"stopped after {rounds_done} repair round(s) (MAX_REPAIR_ROUNDS={max_rounds})"
    if len(history) >= 2 and history[-1] >= history[-2]:
        return False, f"stopped: blocking findings did not decrease ({history[-2]} -> {history[-1]})"
    return True, None


# --------------------------------------------------------------------------- prompts

_prompt_env = Environment(loader=FileSystemLoader(PROMPT_DIR), undefined=StrictUndefined, keep_trailing_newline=True)


def system_prompt(name: str) -> str:
    shared = (PROMPT_DIR / "_shared_rules.md").read_text(encoding="utf-8")
    return _prompt_env.get_template(f"{name}.md").render(shared_rules=shared)


def _prd_block(body: str, tag: str = "prd") -> str:
    return f"<{tag}>\n{body.strip()}\n</{tag}>"


def _parallel(fn, items: list, workers: int = DEFAULT_PARALLEL_CALLS) -> list:
    if len(items) <= 1 or workers <= 1:
        return [fn(item) for item in items]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(fn, items))  # preserves input order -> deterministic results


def _workers(llm: Any) -> int:
    return int(getattr(llm, "max_parallel", DEFAULT_PARALLEL_CALLS))


def _feedback_block(findings: Findings) -> str:
    lines = []
    for f in findings:
        fix = f" Fix: {f.suggested_fix}" if f.suggested_fix else ""
        where = f" ({f.item_key})" if f.item_key else ""
        lines.append(f"- [{f.check_id}]{where} {f.message}{fix}")
    return "\n".join(lines)


# --------------------------------------------------------------------------- S2 extract_requirements


def section_user_message(section: Section, parsed: ParsedPRD, feedback: Findings | None = None,
                         previous: list[Requirement] | None = None) -> str:
    """Units are listed with short local references (u1, u2, ...) that code maps back to unit IDs."""
    units = {u.id: u for u in parsed.units}
    lines = [f"[u{i}] {units[uid].text}" for i, uid in enumerate(section.unit_ids, 1)]
    msg = f"Section: {' > '.join(section.path)}\n\n" + _prd_block("\n".join(lines))
    if feedback:
        ref = {uid: f"u{i}" for i, uid in enumerate(section.unit_ids, 1)}
        msg += "\n\nA previous extraction of this section had these problems. Fix all of them:\n"
        msg += "\n".join(re.sub(r"U-[0-9a-f]{6}-[0-9a-f]{8}(?:-\d+)?", lambda m: ref.get(m.group(0), m.group(0)), line)
                         for line in _feedback_block(feedback).splitlines())
        if previous:
            msg += "\n\nPrevious extraction (for reference):\n" + "\n".join(
                f"- ({r.kind.value}) {r.source_quote}" for r in previous)
    return msg


def _resolve_unit_refs(refs: list[str], section: Section) -> tuple[list[str], list[str]]:
    resolved, unknown = [], []
    for ref in refs:
        ref = ref.strip()
        match = re.fullmatch(r"\[?u?(\d+)\]?", ref, flags=re.IGNORECASE)
        if match and 1 <= int(match.group(1)) <= len(section.unit_ids):
            resolved.append(section.unit_ids[int(match.group(1)) - 1])
        elif ref in section.unit_ids:
            resolved.append(ref)
        else:
            unknown.append(ref)
    return resolved, unknown


def drafts_to_rows(section_drafts: list[tuple[Section, RequirementDraftList]], parsed: ParsedPRD,
                   findings: Findings) -> list[dict]:
    units = {u.id: u for u in parsed.units}
    rows = []
    for section, draft in section_drafts:
        section_units = [units[uid] for uid in section.unit_ids]
        for req in draft.requirements:
            unit_ids, unknown = _resolve_unit_refs(req.unit_ids, section)
            where = " > ".join(section.path)
            if not unit_ids and section_units:
                best = max(section_units, key=lambda u: fuzz.partial_ratio(req.source_quote.lower(), u.text.lower()))
                unit_ids = [best.id]
                findings.append(_finding("REF-UNIT", f"Unknown unit reference(s) {unknown or '(none given)'} for quote "
                                         f"{req.source_quote[:60]!r}; attached to best-matching unit {best.id}.", where))
            elif unknown:
                findings.append(_finding("REF-UNIT", f"Dropped unknown unit reference(s) {unknown} for quote "
                                         f"{req.source_quote[:60]!r}.", where))
            rows.append({
                "section_path": section.path, "unit_ids": sorted(set(unit_ids), key=lambda uid: units[uid].order),
                "source_quote": req.source_quote.strip(), "kind": req.kind, "statement": req.statement.strip(),
                "context_reason": (req.context_reason or None) if req.kind is ReqKind.context_only else None,
                "applies_to_requirement_ids": [],
            })
    return rows


def rows_to_requirements(rows: list[dict], parsed: ParsedPRD) -> list[Requirement]:
    """Document order, then content-derived IDs (suffixes for repeated quotes)."""
    order = {u.id: u.order for u in parsed.units}
    rows = sorted(rows, key=lambda r: min((order[uid] for uid in r["unit_ids"]), default=10**9))
    ids = assign_requirement_ids([r["source_quote"] for r in rows])
    return [Requirement(id=rid, **row) for rid, row in zip(ids, rows) if row["unit_ids"]]


def drafts_to_requirements(section_drafts, parsed: ParsedPRD, findings: Findings | None = None) -> list[Requirement]:
    return rows_to_requirements(drafts_to_rows(section_drafts, parsed, findings if findings is not None else []), parsed)


def extract_sections(parsed: ParsedPRD, llm: StructuredLLM, sections: list[Section], findings: Findings,
                     feedback: dict[tuple, Findings] | None = None, previous: list[Requirement] | None = None) -> list[dict]:
    system = system_prompt("extract_requirements")
    feedback = feedback or {}
    prev_by_section: dict[tuple, list[Requirement]] = {}
    for r in previous or []:
        prev_by_section.setdefault(tuple(r.section_path), []).append(r)

    def call(section: Section):
        key = tuple(section.path)
        user = section_user_message(section, parsed, feedback.get(key), prev_by_section.get(key))
        return llm.structured(RequirementDraftList, system, user, role="extract")

    drafts = _parallel(call, sections, _workers(llm))
    return drafts_to_rows(list(zip(sections, drafts)), parsed, findings)


def extract_requirements(parsed: ParsedPRD, llm: StructuredLLM, sections: list[Section] | None = None,
                         findings: Findings | None = None) -> list[Requirement]:
    targets = sections if sections is not None else [s for s in iter_sections(parsed.root) if s.unit_ids]
    rows = extract_sections(parsed, llm, targets, findings if findings is not None else [])
    return rows_to_requirements(rows, parsed)


def repair_requirements(parsed: ParsedPRD, requirements: list[Requirement], report: ReviewReport, llm: StructuredLLM,
                        findings: Findings) -> list[Requirement]:
    """Re-extract only the sections with blocking R1/R2 findings, with those findings attached."""
    units = {u.id: u for u in parsed.units}
    reqs = {r.id: r for r in requirements}
    feedback: dict[tuple, Findings] = {}
    for f in report.findings:
        if f.severity is not Severity.blocking:
            continue
        if f.item_key in units:
            path = tuple(units[f.item_key].section_path)
        elif f.item_key in reqs:
            path = tuple(reqs[f.item_key].section_path)
        else:
            continue
        feedback.setdefault(path, []).append(f)
    sections = [s for s in iter_sections(parsed.root) if tuple(s.path) in feedback]
    new_rows = extract_sections(parsed, llm, sections, findings, feedback, requirements)
    kept = [r.model_dump(exclude={"id"}) for r in requirements if tuple(r.section_path) not in feedback]
    return rows_to_requirements(kept + new_rows, parsed)


# --------------------------------------------------------------------------- S4 plan_stories


def normalize_story_key(key: str) -> str:
    stripped = key.strip()
    if stripped.lower().startswith("us-"):
        stripped = stripped[3:]
    return f"US-{slugify(stripped, max_words=8)}"


def _dedupe(key: str, taken: set[str]) -> str:
    candidate, n = key, 2
    while candidate in taken:
        candidate, n = f"{key}-{n}", n + 1
    taken.add(candidate)
    return candidate


def requirements_user_message(requirements: list[Requirement], previous_plan: TicketPlan | None) -> str:
    lines = [
        f"[{r.id}] ({r.kind.value}) {' > '.join(r.section_path[1:]) or 'Document'}: {r.statement}"
        f'  | quote: "{r.source_quote}"'
        for r in requirements
    ]
    msg = "Requirements:\n\n" + _prd_block("\n".join(lines))
    if previous_plan is not None:
        prev = "\n".join(f"{s.key}: {s.title} (requirements: {', '.join(s.requirement_ids)})" for s in previous_plan.stories)
        msg += "\n\nPrevious plan (reuse these keys for unchanged or modified scope):\n" + prev
    else:
        msg += "\n\nPrevious plan: none (first run)."
    return msg


def _known_only(ids: list[str], known: set[str], check_id: str, item_key: str | None, what: str,
                findings: Findings) -> list[str]:
    unique = list(dict.fromkeys(ids))
    unknown = [i for i in unique if i not in known]
    if unknown:
        findings.append(_finding(check_id, f"Dropped unknown {what}: {', '.join(unknown)}.", item_key=item_key,
                                 requirement_ids=unknown if check_id == "REF-REQ" else None))
    return [i for i in unique if i in known]


def apply_story_plan(draft: StoryPlanDraft, requirements: list[Requirement], findings: Findings | None = None
                     ) -> tuple[ParentProject, list[StorySkeleton], list[Requirement]]:
    findings = findings if findings is not None else []
    known = {r.id for r in requirements}
    constraints = {r.id for r in requirements if r.kind is ReqKind.constraint}
    taken: set[str] = set()
    skeletons = []
    for s in draft.stories:
        key = _dedupe(normalize_story_key(s.key), taken)
        if key != s.key.strip():
            findings.append(_finding("REF-KEY", f"Story key {s.key!r} normalized to {key!r}.", item_key=key))
        req_ids = _known_only(s.requirement_ids, known, "REF-REQ", key, "requirement ID(s)", findings)
        skeletons.append(StorySkeleton(key=key, title=s.title.strip(), requirement_ids=req_ids))
    scopes: dict[str, list[str]] = {}
    for c in draft.constraint_scopes:
        if c.constraint_id not in constraints:
            findings.append(_finding("REF-CONSTRAINT", f"Scope given for {c.constraint_id}, which is not a constraint "
                                     "requirement; ignored.", requirement_ids=[c.constraint_id]))
            continue
        scopes[c.constraint_id] = _known_only([i for i in c.applies_to_requirement_ids if i != c.constraint_id], known,
                                              "REF-REQ", c.constraint_id, "applies-to requirement ID(s)", findings)
    updated = [r.model_copy(update={"applies_to_requirement_ids": scopes.get(r.id, [])}) if r.id in constraints else r
               for r in requirements]
    project = ParentProject(
        key=f"EPIC-{slugify(draft.epic.title, max_words=5)}",
        title=draft.epic.title.strip(),
        scope=draft.epic.scope.strip(),
        business_goals=[g.strip() for g in draft.epic.business_goals if g.strip()] or ["(no business goal stated)"],
        story_keys=[s.key for s in skeletons],
    )
    return project, skeletons, updated


def plan_stories(requirements: list[Requirement], llm: StructuredLLM, previous_plan: TicketPlan | None = None,
                 findings: Findings | None = None):
    draft = llm.structured(StoryPlanDraft, system_prompt("plan_stories"), requirements_user_message(requirements, previous_plan))
    return apply_story_plan(draft, requirements, findings)


# --------------------------------------------------------------------------- S5 detail_stories

_TRACK_PREFIX = {Track.frontend: "FE", Track.backend: "BE", Track.qa_general: "QA"}
_ALLOWED_AREAS = {
    Track.frontend: [TaskArea.frontend],
    Track.qa_general: [TaskArea.qa],
    Track.backend: [TaskArea.backend, TaskArea.db, TaskArea.infra],
}


def applicable_constraints(skeleton: StorySkeleton, requirements: list[Requirement]) -> list[Requirement]:
    cited = set(skeleton.requirement_ids)
    return [
        r for r in requirements
        if r.kind is ReqKind.constraint
        and (r.id in cited or not r.applies_to_requirement_ids or cited & set(r.applies_to_requirement_ids))
    ]


def _req_line(r: Requirement) -> str:
    return f'[{r.id}] ({r.kind.value}) {r.statement}  | quote: "{r.source_quote}"'


def _task_line(t: TechnicalTask) -> str:
    area = next((str(lb) for lb in t.labels if str(lb).startswith("area:")), "-")
    return (f"{t.key} [{t.track.value}, {area}, {t.size.value}, api={'yes' if t.consumes_api else 'no'}, "
            f"db={'yes' if t.touches_db else 'no'}] {t.title}")


def story_user_message(skeleton: StorySkeleton, requirements: list[Requirement], skeletons: list[StorySkeleton],
                       feedback: Findings | None = None, current: tuple[UserStory, list[TechnicalTask]] | None = None,
                       other_tasks: list[TechnicalTask] | None = None, decisions: list[str] | None = None) -> str:
    reqs = {r.id: r for r in requirements}
    own = [reqs[i] for i in skeleton.requirement_ids if i in reqs and reqs[i].kind is not ReqKind.constraint]
    constraints = applicable_constraints(skeleton, requirements)
    body = "\n".join(_req_line(r) for r in own)
    cons = "\n".join(_req_line(r) + ("" if r.applies_to_requirement_ids else "  [global]") for r in constraints) or "none"
    others = []
    for s in skeletons:
        if s.key == skeleton.key:
            continue
        stmts = "; ".join(f"({reqs[i].kind.value}) {reqs[i].statement}" for i in s.requirement_ids if i in reqs)
        others.append(f"{s.key}: {s.title} — {stmts}")
    msg = (
        f"Story key: {skeleton.key}\nStory title: {skeleton.title}\n\n"
        f"Requirements of this story:\n{_prd_block(body)}\n\n"
        f"Constraints that apply to this story:\n{_prd_block(cons)}\n\n"
        f"Other stories, in plan order, with their requirements (for dependencies and shared work):\n"
        + ("\n".join(others) or "none")
    )
    if other_tasks:
        msg += "\n\nTasks that other stories already contain (do not repeat their work):\n" + "\n".join(
            _task_line(t) for t in other_tasks)
    if current is not None:
        story, tasks = current
        acs = "\n".join(f"  AC: Given {a.given}; When {a.when}; Then {a.then}" for a in story.acceptance_criteria)
        msg += (f"\n\nCurrent version of this story:\n{story.title}\n{acs}\n"
                + "\n".join(f"  TASK {_task_line(t)}" for t in tasks))
    if decisions:
        msg += "\n\n" + _decisions_block(decisions)
    if feedback:
        msg += "\n\nReview findings to fix in this story:\n" + _feedback_block(feedback)
    return msg


def _decisions_block(decisions: list[str]) -> str:
    return ("Reviewer decisions made by the human reviewer at the review gate. They are authoritative: treat them like "
            "PRD text where the PRD is silent. Follow them; do not report them as unrequested, misrepresented or as "
            "assumptions; and report anything that contradicts them:\n" + "\n".join(f"- {d}" for d in decisions))


def decisions_for(decisions: list[ReviewFinding], keys: set[str] | None = None) -> list[str]:
    """Reviewer decisions (G1 feedback) that concern the given items; decisions without an item apply everywhere."""
    out = [f.message for f in decisions if keys is None or f.item_key is None or f.item_key in keys]
    return list(dict.fromkeys(out))


_GWT_PREFIX = {part: re.compile(rf"^\s*\**{part}\**\s*[:,]?\s+", re.IGNORECASE) for part in ("given", "when", "then")}


def normalize_acceptance_criteria(acs):
    """The template renders the Given/When/Then keywords, so a part that repeats its keyword is stripped."""
    out, stripped = [], 0
    for ac in acs:
        parts = {}
        for name, pattern in _GWT_PREFIX.items():
            text = getattr(ac, name)
            new = pattern.sub("", text, count=1)
            if new != text and new.strip():
                stripped += 1
                text = new[0].upper() + new[1:] if name == "given" else new
            parts[name] = text
        out.append(ac.model_copy(update=parts))
    return out, stripped


def _task_labels(draft: TaskDraft, key: str, findings: Findings) -> list[Label]:
    allowed = _ALLOWED_AREAS[draft.track]
    area = draft.area
    if area not in allowed:
        area = allowed[0]
        findings.append(_finding("REF-AREA", f"Area {draft.area.value!r} does not fit track {draft.track.value!r}; "
                                 f"used {area.value!r}.", item_key=key))
    type_label = Label.type_spike if draft.is_spike else Label.type_task
    return [type_label, Label(f"area:{area.value}"), Label.prd_agent]


def apply_story_detail(skeleton: StorySkeleton, draft: StoryDetailDraft, known_req_ids: set[str], story_keys: set[str],
                       taken_task_keys: set[str], findings: Findings | None = None
                       ) -> tuple[UserStory, list[TechnicalTask]]:
    findings = findings if findings is not None else []
    c = draft.story
    acs, stripped = normalize_acceptance_criteria(c.acceptance_criteria)
    if stripped:
        findings.append(_finding("REF-AC", f"Removed a repeated Given/When/Then keyword from {stripped} AC part(s).",
                                 item_key=skeleton.key))
    deps = [normalize_story_key(d) for d in c.dependencies]
    if any(d == skeleton.key for d in deps):
        findings.append(_finding("REF-STORY", "Dropped a dependency of the story on itself.", item_key=skeleton.key))
    deps = _known_only([d for d in deps if d != skeleton.key], story_keys, "REF-STORY", skeleton.key,
                       "story dependency key(s)", findings)
    story = UserStory(
        key=skeleton.key, title=skeleton.title, as_a=c.as_a, i_want=c.i_want, so_that=c.so_that,
        business_description=c.business_description, business_value=c.business_value,
        acceptance_criteria=acs, edge_cases=[e for e in c.edge_cases if e.strip()],
        dependencies=deps, definition_of_done=[d for d in c.definition_of_done if d.strip()],
        requirement_ids=skeleton.requirement_ids,
    )
    story_slug = skeleton.key[3:]
    tasks = []
    for t in draft.tasks:
        prefix = _TRACK_PREFIX[t.track]
        slug = slugify(t.key_slug, max_words=5)
        key = f"{prefix}-{slug}"
        if key in taken_task_keys or not TASK_KEY_RE.match(key):
            key = f"{prefix}-{story_slug}-{slug}"
        key = _dedupe(key, taken_task_keys)
        tasks.append(TechnicalTask(
            key=key, story_key=skeleton.key, title=t.title.strip(), track=t.track, description=t.description,
            size=t.size, consumes_api=t.consumes_api, touches_db=t.touches_db,
            requirement_ids=_known_only(t.requirement_ids, known_req_ids, "REF-REQ", key, "requirement ID(s)", findings),
            derived_reason=t.derived_reason, definition_of_done=[d for d in t.definition_of_done if d.strip()],
            labels=_task_labels(t, key, findings),
        ))
    return story, tasks


def detail_stories(skeletons: list[StorySkeleton], requirements: list[Requirement], llm: StructuredLLM,
                   findings: Findings | None = None):
    findings = findings if findings is not None else []
    system = system_prompt("detail_stories")
    drafts = _parallel(lambda s: llm.structured(StoryDetailDraft, system, story_user_message(s, requirements, skeletons)),
                       skeletons, _workers(llm))
    known = {r.id for r in requirements}
    story_keys = {s.key for s in skeletons}
    taken: set[str] = set()
    stories, tasks = [], []
    for skeleton, draft in zip(skeletons, drafts):  # sequential, in story order -> deterministic keys
        story, story_tasks = apply_story_detail(skeleton, draft, known, story_keys, taken, findings)
        stories.append(story)
        tasks.extend(story_tasks)
    return stories, tasks


# --------------------------------------------------------------------------- S6 map_dependencies


def dependencies_user_message(plan: TicketPlan, focus: set[str] | None = None) -> str:
    lines = [f"{_task_line(t)}  (story {t.story_key})" for t in plan.tasks]
    msg = "Tasks:\n" + _prd_block("\n".join(lines), "plan")
    if focus:
        msg += ("\n\nOnly these tasks are new; return their blockers, plus any existing task that should now be "
                f"blocked by one of them: {', '.join(sorted(focus))}")
    return msg


def apply_dependencies(plan: TicketPlan, draft: DependencyPlanDraft, findings: Findings,
                       editable: set[str] | None = None) -> TicketPlan:
    """LLM proposes, code verifies: unknown keys and self-edges are dropped, edges that would close a cycle are
    skipped, edges to keys that no longer exist are removed. With `editable`, only edges of those tasks (and new
    edges pointing to them) change; other tasks keep their existing edges."""
    keys = [t.key for t in plan.tasks]
    known = set(keys)
    proposed: dict[str, list[str]] = {}
    for edge in draft.edges:
        if edge.task_key not in known:
            findings.append(_finding("REF-DEP", f"Dependency given for unknown task {edge.task_key!r}; ignored."))
            continue
        blockers = _known_only(edge.blocked_by, known, "REF-DEP", edge.task_key, "blocker key(s)", findings)
        if edge.task_key in blockers:
            findings.append(_finding("REF-DEP", "Dropped a dependency of the task on itself.", item_key=edge.task_key))
            blockers = [b for b in blockers if b != edge.task_key]
        proposed.setdefault(edge.task_key, []).extend(b for b in blockers if b not in proposed.get(edge.task_key, []))

    graph: dict[str, list[str]] = {}
    for t in plan.tasks:
        existing = [b for b in t.blocked_by if b in known]
        dropped = [b for b in t.blocked_by if b not in known]
        if dropped:
            findings.append(_finding("REF-DEP", f"Removed blocked_by edges to tasks that no longer exist: "
                                     f"{', '.join(dropped)}.", item_key=t.key))
        if editable is None or t.key in editable:
            graph[t.key] = []
            candidates = proposed.get(t.key, [])
        else:
            graph[t.key] = list(existing)
            candidates = [b for b in proposed.get(t.key, []) if b in editable and b not in existing]
        for blocker in candidates:
            graph[t.key].append(blocker)
            try:
                list(TopologicalSorter(graph).static_order())
            except CycleError:
                graph[t.key].remove(blocker)
                findings.append(_finding("REF-CYCLE", f"Skipped edge {t.key} <- {blocker}: it would create a cycle.",
                                         item_key=t.key))
    tasks = [t.model_copy(update={"blocked_by": graph.get(t.key, [])}) for t in plan.tasks]
    return plan.model_copy(update={"tasks": tasks})


def map_dependencies(plan: TicketPlan, llm: StructuredLLM, findings: Findings, editable: set[str] | None = None) -> TicketPlan:
    if not plan.tasks:
        return plan
    draft = llm.structured(DependencyPlanDraft, system_prompt("map_dependencies"), dependencies_user_message(plan, editable))
    return apply_dependencies(plan, draft, findings, editable)


# --------------------------------------------------------------------------- S7 critic


def compact_plan(plan: TicketPlan) -> str:
    lines = [f"EPIC {plan.project.key}: {plan.project.title}", f"  Scope: {plan.project.scope}"]
    for s in plan.stories:
        lines.append(f"STORY {s.key}: {s.title} (requirements: {', '.join(s.requirement_ids) or '-'}; "
                     f"depends on: {', '.join(s.dependencies) or '-'})")
        lines.append(f"  As a {s.as_a}, I want {s.i_want}, so that {s.so_that}.")
        lines += [f"  AC{i}: Given {a.given}; When {a.when}; Then {a.then}" for i, a in enumerate(s.acceptance_criteria, 1)]
        if s.edge_cases:
            lines.append(f"  Edge cases: {'; '.join(s.edge_cases)}")
        for t in (t for t in plan.tasks if t.story_key == s.key):
            lines.append(f"  TASK {_task_line(t)}")
            lines.append(f"    {t.description[:400]}")
            lines.append(f"    requirements: {', '.join(t.requirement_ids) or '-'}; blocked_by: {', '.join(t.blocked_by) or '-'}")
    lines.append("REQUIREMENTS")
    lines += [_req_line(r) for r in plan.requirements]
    return "\n".join(lines)


def critic_user_message(plan: TicketPlan, parsed: ParsedPRD, focus: list[str] | None,
                        decisions: list[str] | None = None) -> list[dict]:
    """Two text blocks: the PRD (stable across rounds, so it carries the prompt-cache breakpoint) and the plan
    (changes every round, so it is sent as ordinary input instead of being written to the cache)."""
    prd = "PRD:\n" + _prd_block(parsed.markdown) + "\n\n"
    plan_text = "Plan:\n" + _prd_block(compact_plan(plan), "plan")
    if decisions:
        plan_text += "\n\n" + _decisions_block(decisions)
    if focus:
        plan_text += ("\n\nThis is a repair round. Review ONLY these repaired items (use the whole plan as context, "
                      f"for example to find overlap with other stories): {', '.join(focus)}")
    else:
        plan_text += "\n\nReview the whole plan."
    return [{"type": "text", "text": prd, "cache_control": {"type": "ephemeral"}}, {"type": "text", "text": plan_text}]


def run_critic(plan: TicketPlan, parsed: ParsedPRD, llm: StructuredLLM, round_no: int,
               focus: list[str] | None = None, decisions: list[str] | None = None) -> Findings:
    """One structured call (response_format = ReviewReport) on the whole PRD and the whole plan."""
    report = llm.structured(ReviewReport, system_prompt("critic"), critic_user_message(plan, parsed, focus, decisions),
                            role="critic")
    keys = {plan.project.key, *(s.key for s in plan.stories), *(t.key for t in plan.tasks)}
    req_ids = {r.id for r in plan.requirements}
    out = []
    for f in report.findings:
        check_id = f.check_id.strip().upper()
        if check_id not in CRITIC_CHECKS:
            check_id = "CRIT-OTHER"
        item = f.item_key if f.item_key in keys else None
        message = f.message if item or not f.item_key else f"(about unknown item {f.item_key!r}) {f.message}"
        if focus and item not in set(focus):
            continue  # repair rounds: findings on the repaired items only
        out.append(f.model_copy(update={"check_id": check_id, "item_key": item, "message": message,
                                        "requirement_ids": [r for r in f.requirement_ids if r in req_ids]}))
    return out


# --------------------------------------------------------------------------- repair_plan


def _story_for_requirement(rid: str, plan: TicketPlan, skeletons: list[StorySkeleton]) -> str | None:
    """Pick the story that should receive a requirement: one already citing it, else the story citing most
    requirements from the same PRD section, else the first story."""
    reqs = {r.id: r for r in plan.requirements}
    citing = [s.key for s in skeletons if rid in s.requirement_ids]
    if citing:
        return citing[0]
    if rid not in reqs or not skeletons:
        return None
    section = reqs[rid].section_path
    scored = [(sum(reqs[i].section_path == section for i in s.requirement_ids if i in reqs), -n, s.key)
              for n, s in enumerate(skeletons)]
    best = max(scored)
    return best[2]


def resolve_repair_targets(findings: Findings, plan: TicketPlan, skeletons: list[StorySkeleton]
                           ) -> tuple[dict[str, Findings], list[StorySkeleton], Findings]:
    """Group blocking findings by the story to regenerate. Returns (story -> findings, updated skeletons,
    findings that cannot be routed to a story)."""
    story_keys = {s.key for s in plan.stories}
    task_story = {t.key: t.story_key for t in plan.tasks}
    skeletons = [s.model_copy(deep=True) for s in skeletons]
    by_key = {s.key: s for s in skeletons}
    targets: dict[str, Findings] = {}
    unroutable: Findings = []
    for f in findings:
        if f.severity is not Severity.blocking:
            continue
        story = f.item_key if f.item_key in story_keys else task_story.get(f.item_key or "")
        if f.check_id == "CRIT-OVERLAP":
            # Overlap involves several tasks; the critic may name the duplicate only in the text. Repair every story
            # whose task is mentioned, so the duplicate itself is regenerated (with the other stories' tasks shown).
            mentioned = re.findall(r"\b(?:FE|BE|QA)-[a-z0-9]+(?:-[a-z0-9]+)*\b", f"{f.message} {f.suggested_fix or ''}")
            for key in dict.fromkeys(mentioned):
                other = task_story.get(key)
                if other and other != story:
                    targets.setdefault(other, []).append(f)
        if story is None and f.requirement_ids:
            story = _story_for_requirement(f.requirement_ids[0], plan, skeletons)
            if story is not None:
                for rid in f.requirement_ids:
                    if rid not in by_key[story].requirement_ids:
                        by_key[story].requirement_ids.append(rid)
        if story is None:
            unroutable.append(f)
            continue
        targets.setdefault(story, []).append(f)
    return targets, skeletons, unroutable


def repair_plan(plan: TicketPlan, skeletons: list[StorySkeleton], findings: Findings, llm: StructuredLLM,
                ref_findings: Findings, decisions: Findings | None = None
                ) -> tuple[TicketPlan, list[StorySkeleton], list[str], Findings]:
    """Regenerate ONLY the stories (and their tasks) that blocking findings point to; merge back by key."""
    targets, skeletons, unroutable = resolve_repair_targets(findings, plan, skeletons)
    if not targets:
        return plan, skeletons, [], unroutable
    sk_by_key = {s.key: s for s in skeletons}
    system = system_prompt("detail_stories")
    story_by_key = {s.key: s for s in plan.stories}
    order = [s.key for s in plan.stories if s.key in targets]

    def call(key: str) -> StoryDetailDraft:
        others = [t for t in plan.tasks if t.story_key not in targets]
        current = (story_by_key[key], [t for t in plan.tasks if t.story_key == key])
        mine = decisions_for(decisions or [], {key, *(t.key for t in current[1])})
        user = story_user_message(sk_by_key[key], plan.requirements, skeletons, targets[key], current, others, mine)
        return llm.structured(StoryDetailDraft, system, user)

    drafts = _parallel(call, order, _workers(llm))
    known = {r.id for r in plan.requirements}
    story_keys = {s.key for s in plan.stories}
    taken = {t.key for t in plan.tasks if t.story_key not in targets}
    new_stories, new_tasks = {}, {}
    for key, draft in zip(order, drafts):
        story, tasks = apply_story_detail(sk_by_key[key], draft, known, story_keys, taken, ref_findings)
        new_stories[key], new_tasks[key] = story, tasks
    stories = [new_stories.get(s.key, s) for s in plan.stories]
    tasks: list[TechnicalTask] = []
    for s in plan.stories:  # keep plan order: story by story
        tasks += new_tasks[s.key] if s.key in new_tasks else [t for t in plan.tasks if t.story_key == s.key]
    repaired = plan.model_copy(update={"stories": stories, "tasks": tasks})
    new_task_keys = {t.key for ts in new_tasks.values() for t in ts}
    repaired = map_dependencies(TicketPlan.model_validate(repaired.model_dump()), llm, ref_findings, editable=new_task_keys)
    return TicketPlan.model_validate(repaired.model_dump()), skeletons, order + sorted(new_task_keys), unroutable


# --------------------------------------------------------------------------- G1


def feedback_to_findings(text: str, plan: TicketPlan) -> Findings:
    """Turn reviewer feedback into blocking findings. Keys mentioned in the text target those items; feedback
    without a key applies to every story."""
    keys = {s.key for s in plan.stories} | {t.key for t in plan.tasks}
    mentioned = [k for k in re.findall(r"\b(?:US|FE|BE|QA)-[a-z0-9-]+\b", text) if k in keys]
    targets = mentioned or [s.key for s in plan.stories]
    return [ReviewFinding(check_id="G1-FEEDBACK", severity=Severity.blocking, item_key=k, message=text.strip())
            for k in dict.fromkeys(targets)]


def plan_status(state: AgentState) -> Status:
    if state.get("approval") == "abort":
        return Status.ABORTED
    reports = [state.get("req_report"), state.get("plan_report")]
    return Status.NEEDS_REVIEW if any(r is not None and r.blocking_count for r in reports) else Status.PASS


# --------------------------------------------------------------------------- graph


def build_graph(llm: StructuredLLM, console: Console | None = None, checkpointer=None, timings: dict | None = None,
                max_repair_rounds: int = DEFAULT_MAX_REPAIR_ROUNDS, grounding_threshold: float = 90.0,
                duplicate_threshold: float = 90.0, github=None):
    """Compile the graph. `timings` (if given) receives {stage name: seconds}, also when a stage fails.
    `github` is a tools.github_tool.GitHubTool, required only when the run publishes (S9 / G2 / S10)."""
    console = console or Console()
    timings = timings if timings is not None else {}
    cost = getattr(llm, "cost", None)

    def timed(name: str, fn):
        def run(state: AgentState) -> AgentState:
            if cost is not None:
                cost.stage = name
            started = time.monotonic()
            try:
                return fn(state)
            finally:
                timings[name] = round(timings.get(name, 0.0) + time.monotonic() - started, 1)

        return run

    def stage(name: str) -> None:
        console.rule(f"[bold]{name}")

    def refs(state: AgentState, new: Findings) -> Findings:
        return state.get("reference_findings", []) + new

    # ---- S1 / S2 / S3
    def n_load_prd(state: AgentState) -> AgentState:
        stage("S1 load_prd")
        parsed = load_prd(state["prd_path"])
        previous = state_store.load_plan(Path(state["out_dir"]))
        sections = sum(1 for _ in iter_sections(parsed.root)) - 1
        console.print(f"{len(parsed.units)} units in {sections} sections · prd_hash {parsed.prd_hash[:12]}")
        console.print("Update run: previous plan loaded." if previous else "First run: no previous plan.")
        return {"parsed": parsed, "units": parsed.units, "previous_plan": previous, "reference_findings": [],
                "reports": [], "req_rounds": 0, "req_blocking_history": [], "plan_rounds": 0,
                "plan_blocking_history": [], "repaired_keys": [], "best_plan": None, "feedback_findings": [], "reviewer_decisions": [], "approval": None,
                "started_at": state.get("started_at") or time.monotonic()}

    def n_extract(state: AgentState) -> AgentState:
        stage("S2 extract_requirements")
        found: Findings = []
        reqs = extract_requirements(state["parsed"], llm, findings=found)
        console.print(f"{len(reqs)} requirements ({sum(r.kind is not ReqKind.context_only for r in reqs)} actionable)")
        return {"requirements": reqs, "reference_findings": refs(state, found)}

    def n_check_requirements(state: AgentState) -> AgentState:
        stage("S3 check_requirements")
        findings = validators.check_requirements(state["requirements"], state["parsed"], grounding_threshold)
        report = ReviewReport(stage="check_requirements", round=state["req_rounds"] + 1, verdict=Verdict.pass_,
                              findings=findings)
        history = state["req_blocking_history"] + [report.blocking_count]
        _, reason = should_repair(report, state["req_rounds"], history, max_repair_rounds)
        console.print(f"round {report.round}: {report.blocking_count} blocking, {report.warning_count} warnings"
                      + (f" · {reason}" if reason else ""))
        return {"req_report": report, "req_blocking_history": history, "req_stop_reason": reason,
                "reports": state["reports"] + [report]}

    def route_requirements(state: AgentState) -> str:
        repair, _ = should_repair(state["req_report"], state["req_rounds"], state["req_blocking_history"], max_repair_rounds)
        return "repair_requirements" if repair else "plan_stories"

    def n_repair_requirements(state: AgentState) -> AgentState:
        stage("repair_requirements")
        found: Findings = []
        reqs = repair_requirements(state["parsed"], state["requirements"], state["req_report"], llm, found)
        console.print(f"re-extracted failing sections · {len(reqs)} requirements")
        return {"requirements": reqs, "req_rounds": state["req_rounds"] + 1, "reference_findings": refs(state, found)}

    # ---- S4 / S5 / S6
    def n_plan(state: AgentState) -> AgentState:
        stage("S4 plan_stories")
        found: Findings = []
        project, skeletons, reqs = plan_stories(state["requirements"], llm, state.get("previous_plan"), found)
        console.print(f"Epic {project.key} · {len(skeletons)} stories")
        plan = TicketPlan(prd_hash=state["parsed"].prd_hash, project=project, requirements=reqs)
        return {"skeletons": skeletons, "requirements": reqs, "plan": plan, "reference_findings": refs(state, found)}

    def n_detail(state: AgentState) -> AgentState:
        stage("S5 detail_stories")
        found: Findings = []
        stories, tasks = detail_stories(state["skeletons"], state["requirements"], llm, found)
        console.print(f"{len(stories)} stories detailed · {len(tasks)} tasks")
        plan = state["plan"].model_copy(update={"stories": stories, "tasks": tasks})
        return {"plan": TicketPlan.model_validate(plan.model_dump()), "reference_findings": refs(state, found)}

    def n_map_dependencies(state: AgentState) -> AgentState:
        stage("S6 map_dependencies")
        found: Findings = []
        plan = map_dependencies(state["plan"], llm, found)
        console.print(f"{sum(len(t.blocked_by) for t in plan.tasks)} blocked_by edges")
        return {"plan": plan, "reference_findings": refs(state, found)}

    # ---- S7 and repair_plan
    def n_check_plan(state: AgentState) -> AgentState:
        stage("S7 check_plan")
        plan = state["plan"]
        round_no = state["plan_rounds"] + 1
        deterministic = validators.check_plan(plan, duplicate_threshold)
        focus = (state.get("repaired_keys") or None) if round_no > 1 else None
        critic = run_critic(plan, state["parsed"], llm, round_no, focus,
                            decisions_for(state.get("reviewer_decisions") or []))
        if focus and state.get("plan_report") is not None:  # carry earlier critic findings on untouched items
            keys = {plan.project.key, *(s.key for s in plan.stories), *(t.key for t in plan.tasks)}
            carried = [f for f in state["plan_report"].findings
                       if f.check_id.startswith("CRIT-") and f.item_key not in set(focus) and f.item_key in keys]
            critic = carried + critic
        report = ReviewReport(stage="check_plan", round=round_no, verdict=Verdict.pass_, findings=deterministic + critic)
        history = state["plan_blocking_history"] + [report.blocking_count]
        repair, reason = should_repair(report, state["plan_rounds"], history, max_repair_rounds)
        if repair and not resolve_repair_targets(report.findings, plan, state["skeletons"])[0]:
            reason = "stopped: the remaining blocking findings cannot be tied to a story or task to regenerate"
        best = state.get("best_plan")
        update: dict = {}
        if best is None or report.blocking_count < best["report"].blocking_count:
            best = {"plan": plan, "report": report, "skeletons": state["skeletons"]}
            update["best_plan"] = best
        elif reason and best["report"].blocking_count < report.blocking_count:
            # Stopping on a round that is worse than an earlier one: keep the best plan seen (fewest blocking).
            reason += (f"; kept the plan of round {best['report'].round} ({best['report'].blocking_count} blocking) "
                       f"instead of round {round_no} ({report.blocking_count} blocking)")
            update.update(plan=best["plan"], skeletons=best["skeletons"])
            report = best["report"]
        n_crit = sum(f.check_id.startswith("CRIT-") for f in report.findings)
        console.print(f"round {round_no}: {report.blocking_count} blocking, {report.warning_count} warnings "
                      f"({n_crit} from the critic{', repaired items only' if focus else ''})"
                      + (f" · {reason}" if reason else ""))
        reports = state["reports"] + [ReviewReport(stage="check_plan", round=round_no, verdict=Verdict.pass_,
                                                   findings=deterministic + critic)]
        if update.get("plan") is not None:
            reports.append(report.model_copy(update={"stage": "check_plan", "round": report.round}))
        return {"plan_report": report, "plan_blocking_history": history, "plan_stop_reason": reason,
                "reports": reports, "feedback_findings": [], **update}

    def route_plan(state: AgentState) -> str:
        repair, _ = should_repair(state["plan_report"], state["plan_rounds"], state["plan_blocking_history"], max_repair_rounds)
        if repair and not resolve_repair_targets(state["plan_report"].findings, state["plan"], state["skeletons"])[0]:
            repair = False
        return "repair_plan" if repair else "render_preview"

    def n_repair_plan(state: AgentState) -> AgentState:
        stage("repair_plan")
        found: Findings = []
        findings = list(state["plan_report"].findings) + list(state.get("feedback_findings") or [])
        plan, skeletons, repaired, unroutable = repair_plan(state["plan"], state["skeletons"], findings, llm, found,
                                                            state.get("reviewer_decisions") or [])
        console.print(f"regenerated {sum(k.startswith('US-') for k in repaired)} story(ies): "
                      f"{', '.join(k for k in repaired if k.startswith('US-')) or 'none'}"
                      + (f" · {len(unroutable)} finding(s) not tied to a story" if unroutable else ""))
        return {"plan": plan, "skeletons": skeletons, "repaired_keys": repaired, "plan_rounds": state["plan_rounds"] + 1,
                "reference_findings": refs(state, found)}

    # ---- S8 / G1 / S11
    def n_render(state: AgentState) -> AgentState:
        stage("S8 render_preview")
        status = plan_status(state)
        reports = state["reports"] + [reference_report(state.get("reference_findings", []))]
        stop = {"check_requirements": state.get("req_stop_reason"), "check_plan": state.get("plan_stop_reason")}
        written = renderer.write_outputs(state["plan"], Path(state["out_dir"]), reports=reports, status=status.value,
                                         stop_reasons=stop)
        console.print(renderer.plan_tree(state["plan"]))
        console.print(f"Status: [bold]{status.value}[/]")
        return {"outputs": [str(p) for p in written], "status": status}

    def n_approve(state: AgentState) -> AgentState:
        stage("G1 approve_plan")
        status = state["status"]
        if state.get("auto_yes") and status is Status.PASS:
            console.print("--yes and status PASS: approved automatically.")
            return {"approval": "approve"}
        report = state.get("plan_report")
        answer = interrupt({
            "gate": "G1",
            "status": status.value,
            "stories": len(state["plan"].stories),
            "tasks": len(state["plan"].tasks),
            "blocking": [f.model_dump(mode="json") for f in (report.findings if report else []) if f.severity is Severity.blocking],
            "warnings": report.warning_count if report else 0,
            "out_dir": state["out_dir"],
        })
        action = (answer or {}).get("action", "abort") if isinstance(answer, dict) else str(answer)
        if action == "feedback":
            text = (answer or {}).get("text", "") if isinstance(answer, dict) else ""
            fb = feedback_to_findings(text, state["plan"]) if text.strip() else []
            # Feedback is a reviewer decision: it stays authoritative for the critic and every later repair, and it
            # starts a fresh repair cycle (rounds, history and the best-round baseline reset), so an earlier round
            # without the decision can never be restored over it.
            return {"approval": "feedback", "feedback_findings": fb,
                    "reviewer_decisions": (state.get("reviewer_decisions") or []) + fb,
                    "plan_rounds": 0, "plan_blocking_history": [], "best_plan": None}
        return {"approval": "approve" if action == "approve" else "abort"}

    def route_approval(state: AgentState) -> str:
        if state.get("approval") == "feedback" and state.get("feedback_findings"):
            return "repair_plan"
        if state.get("approval") == "approve" and state.get("publish"):
            return "sync_diff"
        return "summary"

    # ---- S9 / G2 / S10
    def n_sync_diff(state: AgentState) -> AgentState:
        stage("S9 sync_diff")
        if github is None:
            raise RuntimeError("--publish needs a GitHub client")
        listing = github.list_marked_issues()
        actions = sync_diff(state["plan"], listing)
        counts = {k.value: sum(a.action is k for a in actions) for k in SyncActionType}
        console.print(f"{github.repo}: {len(listing.issues)} managed issue(s) found · "
                      + " · ".join(f"{k} {v}" for k, v in counts.items()))
        if listing.ignored_unmarked:
            numbers = ", ".join(f"#{n}" for n in listing.ignored_unmarked)
            console.print(f"[dim]{len(listing.ignored_unmarked)} issue(s) labelled prd-agent without a marker are "
                          f"never touched: {numbers}[/]")
        for key, number in listing.duplicate_keys:
            console.print(f"[yellow]Issue #{number} repeats the key {key}; only the first issue is managed.[/]")
        return {"sync_actions": actions}

    def n_confirm_diff(state: AgentState) -> AgentState:
        stage("G2 confirm_diff")
        actions = state["sync_actions"]
        if state["status"] is Status.NEEDS_REVIEW and not state.get("force"):
            console.print("[red]Refusing to publish: status is NEEDS_REVIEW. Resolve the findings or pass --force.[/]")
            return {"publish_decision": "refused"}
        changes = [a for a in actions if a.action is not SyncActionType.unchanged]
        if not changes:
            console.print("Nothing to change on GitHub.")
            return {"publish_decision": "confirm"}
        if state.get("auto_yes"):
            console.print("--yes: diff confirmed automatically.")
            return {"publish_decision": "confirm"}
        answer = interrupt({
            "gate": "G2",
            "repo": github.repo if github is not None else "",
            "counts": {k.value: sum(a.action is k for a in actions) for k in SyncActionType},
            "changes": [{"key": a.key, "action": a.action.value, "issue": a.issue_number,
                         "title": (a.payload or {}).get("title")} for a in changes],
        })
        action = answer.get("action") if isinstance(answer, dict) else str(answer)
        return {"publish_decision": "confirm" if action == "confirm" else "abort"}

    def route_publish(state: AgentState) -> str:
        changes = any(a.action is not SyncActionType.unchanged for a in state.get("sync_actions") or [])
        return "publish" if state.get("publish_decision") == "confirm" and changes else "summary"

    def n_publish(state: AgentState) -> AgentState:
        stage("S10 publish")
        result = publish(state["plan"], state["sync_actions"], github)
        console.print(f"created {len(result.created)} · updated {len(result.updated)} · closed {len(result.closed)} · "
                      f"unchanged {len(result.unchanged)} · relinked {len(result.relinked)} · "
                      f"labels created {len(result.labels_created)}")
        return {"publish_result": {"numbers": result.numbers, "created": result.created, "updated": result.updated,
                                   "closed": result.closed, "unchanged": result.unchanged,
                                   "relinked": result.relinked, "labels_created": result.labels_created}}

    def n_summary(state: AgentState) -> AgentState:
        stage("S11 summary")
        status = plan_status(state)
        plan = state["plan"]
        console.print(f"Status: [bold]{status.value}[/] · Epic: 1 · Stories: {len(plan.stories)} · "
                      f"Tasks: {len(plan.tasks)} · Requirements: {len(plan.requirements)}")
        if state.get("reference_findings"):
            console.print(f"[yellow]{len(state['reference_findings'])} reference finding(s); see validation_report.md.[/]")
        console.print(f"Outputs in {state['out_dir']}/ (plan.json, plan.md, requirements.md, validation_report.md, payloads/)")
        table = Table(title="Time and cost per stage")
        for col in ("Stage", "Time (s)", "Calls", "Cost (USD)", "Models"):
            table.add_column(col)
        for name, seconds in timings.items():
            entry = (cost.by_stage.get(name) if cost is not None else None) or {}
            table.add_row(name, f"{seconds:.1f}", str(entry.get("calls", 0)), f"{entry.get('cost_usd', 0.0):.4f}",
                          ", ".join(entry.get("models", [])))
        console.print(table)
        if cost is not None:
            critic = cost.by_role.get("critic", {})
            console.print(f"[bold]Cost:[/] {cost.summary()}")
            console.print(f"[bold]Critic cost:[/] ${critic.get('cost_usd', 0.0):.4f} in {critic.get('calls', 0)} call(s)")
        if state.get("started_at"):
            console.print(f"[bold]Time:[/] {time.monotonic() - state['started_at']:.1f}s")
        if state.get("approval") == "abort":
            console.print("[red]Aborted at G1; nothing was published.[/]")
        decision = state.get("publish_decision")
        published = state.get("publish_result")
        if state.get("publish") and published and github is not None:
            epic = published["numbers"].get(plan.project.key)
            link = f" · epic {github.issue_url(epic)}" if epic else ""
            console.print(f"[bold]Published[/] to {github.repo}: created {len(published['created'])}, updated "
                          f"{len(published['updated'])}, closed {len(published['closed'])}, unchanged "
                          f"{len(published['unchanged'])}{link}")
        elif state.get("publish") and decision == "refused":
            console.print("[yellow]Nothing was published (refused at G2: status NEEDS_REVIEW).[/]")
        elif state.get("publish") and decision == "abort":
            console.print("[yellow]Nothing was published (aborted at G2).[/]")
        elif state.get("publish") and decision == "confirm":
            console.print("GitHub already matches the plan: 0 changes.")
        return {"status": status}

    graph = StateGraph(AgentState)
    nodes = [
        ("load_prd", n_load_prd), ("extract_requirements", n_extract), ("check_requirements", n_check_requirements),
        ("repair_requirements", n_repair_requirements), ("plan_stories", n_plan), ("detail_stories", n_detail),
        ("map_dependencies", n_map_dependencies), ("check_plan", n_check_plan), ("repair_plan", n_repair_plan),
        ("render_preview", n_render), ("approve_plan", n_approve), ("sync_diff", n_sync_diff),
        ("confirm_diff", n_confirm_diff), ("publish", n_publish), ("summary", n_summary),
    ]
    for name, fn in nodes:
        graph.add_node(name, timed(name, fn))
    graph.add_edge(START, "load_prd")
    graph.add_edge("load_prd", "extract_requirements")
    graph.add_edge("extract_requirements", "check_requirements")
    graph.add_conditional_edges("check_requirements", route_requirements, ["repair_requirements", "plan_stories"])
    graph.add_edge("repair_requirements", "check_requirements")
    graph.add_edge("plan_stories", "detail_stories")
    graph.add_edge("detail_stories", "map_dependencies")
    graph.add_edge("map_dependencies", "check_plan")
    graph.add_conditional_edges("check_plan", route_plan, ["repair_plan", "render_preview"])
    graph.add_edge("repair_plan", "check_plan")
    graph.add_edge("render_preview", "approve_plan")
    graph.add_conditional_edges("approve_plan", route_approval, ["repair_plan", "sync_diff", "summary"])
    graph.add_edge("sync_diff", "confirm_diff")
    graph.add_conditional_edges("confirm_diff", route_publish, ["publish", "summary"])
    graph.add_edge("publish", "summary")
    graph.add_edge("summary", END)
    return graph.compile(checkpointer=checkpointer)
