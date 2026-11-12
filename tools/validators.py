"""Deterministic checks (SPEC §8). Each returns ReviewFindings with check_id + severity.

All checks are blocking unless noted. Validators are never weakened to make a run pass (SPEC §17).
"""

from __future__ import annotations

import re
from collections import defaultdict
from graphlib import CycleError, TopologicalSorter

from rapidfuzz import fuzz

from schemas import (
    TITLE_MAX_LEN,
    TRACK_PREFIX,
    Label,
    ParsedPRD,
    ReqKind,
    Requirement,
    ReviewFinding,
    Severity,
    TicketPlan,
    Track,
    UnitKind,
)
from tools.prd_search import PRDIndex

B, W = Severity.blocking, Severity.warning

VAGUE_WORDS = re.compile(
    r"(?<![\w-])(works|correctly|properly|as expected|user-friendly|user friendly|fast|etc\.?)(?![\w-])", re.IGNORECASE
)
GENERIC_TITLES = {"implement feature", "backend work", "frontend work", "testing", "misc"}
MAX_TASKS_PER_STORY = 8
DECISION_DOD = re.compile(r"\b(rationale|trade-?offs?)\b", re.IGNORECASE)


def _f(check_id: str, message: str, severity: Severity = B, item_key: str | None = None,
       requirement_ids: list[str] | None = None, suggested_fix: str | None = None) -> ReviewFinding:
    return ReviewFinding(check_id=check_id, severity=severity, item_key=item_key,
                         requirement_ids=requirement_ids or [], message=message, suggested_fix=suggested_fix)


# --------------------------------------------------------------------------- requirements (S3)


def check_r1_grounding(requirements: list[Requirement], index: PRDIndex, threshold: float) -> list[ReviewFinding]:
    out = []
    for r in requirements:
        result = index.verify_quote(r.source_quote, threshold)
        if not result.grounded:
            out.append(_f("R1", f"Source quote is not found in the PRD (best match {result.score:.0f} < {threshold:.0f}): "
                          f"{r.source_quote[:120]!r}", item_key=r.id, requirement_ids=[r.id],
                          suggested_fix="Copy the requirement text verbatim from the PRD unit."))
    return out


def check_r2_unit_coverage(requirements: list[Requirement], parsed: ParsedPRD) -> list[ReviewFinding]:
    """Every unit is in a requirement. context_only needs a reason. A list item (bullet / table row) covered
    only by context_only requirements is flagged too: list items in a PRD state requirements."""
    by_unit: dict[str, list[Requirement]] = defaultdict(list)
    for r in requirements:
        for uid in r.unit_ids:
            by_unit[uid].append(r)
    out = []
    for u in parsed.units:
        reqs = by_unit.get(u.id, [])
        where = " > ".join(u.section_path)
        if not reqs:
            out.append(_f("R2", f"PRD unit is not covered by any requirement ({where}): {u.text!r}", item_key=u.id,
                          suggested_fix="Extract a requirement for this unit, or mark it context_only with a reason."))
            continue
        if all(r.kind is ReqKind.context_only for r in reqs) and u.kind in (UnitKind.bullet, UnitKind.table_row):
            out.append(_f("R2", f"List item is marked context_only, but list items state requirements ({where}): "
                          f"{u.text!r}", item_key=u.id, requirement_ids=[r.id for r in reqs],
                          suggested_fix="Classify it with its real kind (e.g. frontend, data_model, functional)."))
    for r in requirements:
        if r.kind is ReqKind.context_only and not (r.context_reason or "").strip():
            out.append(_f("R2", "context_only requirement has no reason.", item_key=r.id, requirement_ids=[r.id],
                          suggested_fix="Give context_reason, or classify it as a requirement."))
    return out


def check_requirements(requirements: list[Requirement], parsed: ParsedPRD, threshold: float = 90.0) -> list[ReviewFinding]:
    index = PRDIndex(parsed, requirements)
    return check_r1_grounding(requirements, index, threshold) + check_r2_unit_coverage(requirements, parsed)


# --------------------------------------------------------------------------- plan (S7)


def _tickets(plan: TicketPlan):
    return [plan.project, *plan.stories, *plan.tasks]


def check_p1_coverage(plan: TicketPlan) -> list[ReviewFinding]:
    cited = {rid for item in [*plan.stories, *plan.tasks] for rid in item.requirement_ids}
    return [
        _f("P1", f"Requirement is not cited by any story or task: {r.statement[:120]!r}", requirement_ids=[r.id],
           suggested_fix="Add it to the story that delivers this capability.")
        for r in plan.requirements if r.kind is not ReqKind.context_only and r.id not in cited
    ]


def check_p2_citations(plan: TicketPlan) -> list[ReviewFinding]:
    known = {r.id for r in plan.requirements}
    out = []
    for item in [*plan.stories, *plan.tasks]:
        unknown = [i for i in item.requirement_ids if i not in known]
        if unknown:
            out.append(_f("P2", f"Cites unknown requirement IDs: {', '.join(unknown)}", item_key=item.key, requirement_ids=unknown))
    for t in plan.tasks:
        if not t.requirement_ids and t.derived_reason is None:
            out.append(_f("P2", "Task cites no requirement and has no derived_reason.", item_key=t.key,
                          suggested_fix="Cite the requirement it implements, or set derived_reason."))
    return out


def check_p3_acceptance_criteria(plan: TicketPlan) -> list[ReviewFinding]:
    out = []
    for s in plan.stories:
        if len(s.acceptance_criteria) < 2:
            out.append(_f("P3", f"Story has {len(s.acceptance_criteria)} acceptance criteria; at least 2 are required.",
                          item_key=s.key))
        for i, ac in enumerate(s.acceptance_criteria, 1):
            for part_name in ("given", "when", "then"):
                text = getattr(ac, part_name)
                match = VAGUE_WORDS.search(text)
                if match and not re.search(r"\d", text):
                    out.append(_f("P3", f"AC {i} '{part_name}' uses the vague word {match.group(1)!r} without a "
                                  f"measurable value: {text[:120]!r}", item_key=s.key,
                                  suggested_fix="Replace it with an observable, specific outcome."))
    return out


def check_p4_tracks(plan: TicketPlan) -> list[ReviewFinding]:
    by_req: dict[str, set[Track]] = defaultdict(set)
    for t in plan.tasks:
        for rid in t.requirement_ids:
            by_req[rid].add(t.track)
    out = []
    for r in plan.requirements:
        if r.kind in (ReqKind.backend, ReqKind.data_model) and Track.backend not in by_req[r.id]:
            out.append(_f("P4", f"{r.kind.value} requirement has no backend task: {r.statement[:100]!r}", requirement_ids=[r.id],
                          suggested_fix="Add or extend a [BE] task that cites it."))
        if r.kind is ReqKind.frontend and Track.frontend not in by_req[r.id]:
            out.append(_f("P4", f"frontend requirement has no frontend task: {r.statement[:100]!r}", requirement_ids=[r.id],
                          suggested_fix="Add or extend a [FE] task that cites it."))
    for s in plan.stories:
        if not any(t.story_key == s.key and t.track is Track.qa_general for t in plan.tasks):
            out.append(_f("P4", "Story has no qa_general task.", item_key=s.key))
    return out


def check_p5_labels(plan: TicketPlan) -> list[ReviewFinding]:
    expected_type = {plan.project.key: {Label.type_epic}}
    expected_type.update({s.key: {Label.type_story} for s in plan.stories})
    expected_type.update({t.key: {Label.type_task, Label.type_spike} for t in plan.tasks})
    task_keys = {t.key for t in plan.tasks}
    out = []
    for item in _tickets(plan):
        labels = [str(lb) for lb in item.labels]
        types = [lb for lb in item.labels if str(lb).startswith("type:")]
        areas = [lb for lb in item.labels if str(lb).startswith("area:")]
        if len(labels) != len(set(labels)):
            out.append(_f("P5", f"Duplicate labels: {labels}", item_key=item.key))
        if len(types) != 1 or types[0] not in expected_type[item.key]:
            out.append(_f("P5", f"Needs exactly one matching type:* label, has {[str(t) for t in types]}", item_key=item.key))
        if item.key in task_keys and len(areas) != 1:
            out.append(_f("P5", f"Task needs exactly one area:* label, has {[str(a) for a in areas]}", item_key=item.key))
        if item.key not in task_keys and areas:
            out.append(_f("P5", f"Only tasks carry area:* labels, has {[str(a) for a in areas]}", item_key=item.key))
        if Label.prd_agent not in item.labels:
            out.append(_f("P5", "Missing the prd-agent label.", item_key=item.key))
    return out


def _norm_title(title: str) -> str:
    return " ".join(title.lower().split())


def check_p6_duplicate_titles(plan: TicketPlan, threshold: float = 90.0) -> list[ReviewFinding]:
    out = []
    for group in (plan.stories, plan.tasks):
        for i, a in enumerate(group):
            for b in group[i + 1:]:
                score = fuzz.ratio(_norm_title(a.title), _norm_title(b.title))
                if score >= threshold:
                    out.append(_f("P6", f"Title is a near-duplicate ({score:.0f}) of {a.key}: {b.title!r}", item_key=b.key,
                                  suggested_fix=f"Merge the work into {a.key} or make the title name a different artifact."))
    return out


def check_p7_dependencies(plan: TicketPlan) -> list[ReviewFinding]:
    tasks = {t.key: t for t in plan.tasks}
    out = []
    for t in plan.tasks:
        unknown = [k for k in t.blocked_by if k not in tasks]
        if unknown:
            out.append(_f("P7", f"blocked_by references unknown tasks: {', '.join(unknown)}", item_key=t.key))
    try:
        list(TopologicalSorter({t.key: [k for k in t.blocked_by if k in tasks] for t in plan.tasks}).static_order())
    except CycleError as exc:
        cycle = exc.args[1] if len(exc.args) > 1 else []
        out.append(_f("P7", f"Dependency cycle: {' -> '.join(cycle)}", item_key=cycle[0] if cycle else None))
    for t in plan.tasks:
        blockers = [tasks[k] for k in t.blocked_by if k in tasks]
        if t.consumes_api and t.track is not Track.backend and not any(b.track is Track.backend for b in blockers):
            out.append(_f("P7", "Task consumes an API but is not blocked by any backend task.", W, item_key=t.key))
        if t.touches_db and Label.area_db not in t.labels and not any(Label.area_db in b.labels for b in blockers):
            out.append(_f("P7", "Task touches the database but is not blocked by an area:db task.", W, item_key=t.key))
    return out


def check_p8_constraints(plan: TicketPlan) -> list[ReviewFinding]:
    out = []
    for c in plan.requirements:
        if c.kind is not ReqKind.constraint or not c.applies_to_requirement_ids:
            continue
        scope = set(c.applies_to_requirement_ids)
        for s in plan.stories:
            if scope & set(s.requirement_ids) and c.id not in s.requirement_ids:
                out.append(_f("P8", f"Story cites requirements in the scope of constraint {c.id} but not the constraint: "
                              f"{c.statement[:100]!r}", item_key=s.key, requirement_ids=[c.id],
                              suggested_fix="Cite the constraint and reflect it in an acceptance criterion."))
    return out


def check_p9_decisions(plan: TicketPlan) -> list[ReviewFinding]:
    out = []
    spikes = [t for t in plan.tasks if Label.type_spike in t.labels]
    for r in plan.requirements:
        if r.kind is not ReqKind.decision_open:
            continue
        mine = [t for t in spikes if r.id in t.requirement_ids]
        if not mine:
            out.append(_f("P9", f"Open decision has no spike task: {r.statement[:100]!r}", requirement_ids=[r.id],
                          suggested_fix="Add a type:spike task that cites it."))
        elif not any(DECISION_DOD.search(" ".join(t.definition_of_done)) for t in mine):
            out.append(_f("P9", "Spike task's Definition of Done does not require a documented rationale / trade-offs.",
                          item_key=mine[0].key, requirement_ids=[r.id]))
    return out


def check_p10_sizing(plan: TicketPlan) -> list[ReviewFinding]:
    out = []
    for s in plan.stories:
        n = sum(t.story_key == s.key for t in plan.tasks)
        if n > MAX_TASKS_PER_STORY:
            out.append(_f("P10", f"Story has {n} tasks (> {MAX_TASKS_PER_STORY}); consider splitting it.", W, item_key=s.key))
    for t in plan.tasks:
        if t.size.value == "L":
            out.append(_f("P10", "Task is size L; consider splitting it.", W, item_key=t.key))
    return out


def check_p11_titles(plan: TicketPlan) -> list[ReviewFinding]:
    out = []
    for item in _tickets(plan):
        title = item.title.strip()
        if not title:
            out.append(_f("P11", "Title is empty.", item_key=item.key))
            continue
        if len(title) > TITLE_MAX_LEN:
            out.append(_f("P11", f"Title is {len(title)} characters (max {TITLE_MAX_LEN}): {title!r}", item_key=item.key,
                          suggested_fix="Shorten it while keeping the object it names."))
        bare = re.sub(r"^\[(FE|BE|QA)\]\s*", "", title, flags=re.IGNORECASE).strip(" .").lower()
        if bare in GENERIC_TITLES:
            out.append(_f("P11", f"Title is only a generic phrase: {title!r}", item_key=item.key))
    for t in plan.tasks:
        prefix = TRACK_PREFIX[t.track]
        if not t.title.strip().startswith(prefix):
            out.append(_f("P11", f"Task title must start with {prefix} for track {t.track.value}: {t.title!r}", item_key=t.key))
    return out


PLAN_CHECKS = (
    check_p1_coverage, check_p2_citations, check_p3_acceptance_criteria, check_p4_tracks, check_p5_labels,
    check_p7_dependencies, check_p8_constraints, check_p9_decisions, check_p10_sizing, check_p11_titles,
)


def check_plan(plan: TicketPlan, duplicate_threshold: float = 90.0) -> list[ReviewFinding]:
    findings = []
    for check in PLAN_CHECKS:
        findings += check(plan)
    findings += check_p6_duplicate_titles(plan, duplicate_threshold)
    order = {f"P{i}": i for i in range(1, 12)}
    return sorted(findings, key=lambda f: (order.get(f.check_id, 99), f.item_key or ""))
