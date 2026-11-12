"""The pipeline graph (SPEC §5-§6).

Code orchestrates; the LLM only fills narrow, schema-bound drafts (see schemas.*Draft). Every ID, key and
label is derived by code here, so the plan stays stable and PRD-agnostic. Whenever code has to drop or
replace something the LLM returned (an unknown requirement ID, an unknown story dependency, a mangled unit
ID, an area that does not fit the track), it records a ReviewFinding instead of doing it silently.

Milestone 2: S1 load_prd -> S2 extract_requirements -> S4 plan_stories -> S5 detail_stories
-> S8 render_preview -> S11 summary. Checks, repair loops and gates arrive in milestone 3.
"""

from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Protocol, TypedDict, TypeVar

from jinja2 import Environment, FileSystemLoader, StrictUndefined
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel
from rapidfuzz import fuzz
from rich.console import Console

from schemas import (
    TASK_KEY_RE,
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
from tools import renderer, state_store
from tools.file_reader import iter_sections, load_prd

log = logging.getLogger("prd_agent.agent")
PROMPT_DIR = Path(__file__).resolve().parent / "prompts"
DEFAULT_PARALLEL_CALLS = 4

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
    previous_plan: TicketPlan | None
    skeletons: list[StorySkeleton]
    plan: TicketPlan
    plan_report: ReviewReport | None
    reference_findings: Findings
    rounds: int
    blocking_history: list[int]
    sync_actions: list[SyncAction]
    publish: bool
    auto_yes: bool
    force: bool
    status: Status
    outputs: list[str]
    started_at: float


def _finding(check_id: str, message: str, item_key: str | None = None, requirement_ids: list[str] | None = None,
             suggested_fix: str | None = None) -> ReviewFinding:
    log.warning("[%s] %s%s", check_id, f"{item_key}: " if item_key else "", message)
    return ReviewFinding(check_id=check_id, severity=Severity.warning, item_key=item_key,
                         requirement_ids=requirement_ids or [], message=message, suggested_fix=suggested_fix)


def reference_report(findings: Findings) -> ReviewReport:
    return ReviewReport(stage="reference_normalization", round=0, verdict=Verdict.pass_, findings=findings)


# --------------------------------------------------------------------------- prompts

_prompt_env = Environment(loader=FileSystemLoader(PROMPT_DIR), undefined=StrictUndefined, keep_trailing_newline=True)


def system_prompt(name: str) -> str:
    shared = (PROMPT_DIR / "_shared_rules.md").read_text(encoding="utf-8")
    return _prompt_env.get_template(f"{name}.md").render(shared_rules=shared)


def _prd_block(body: str) -> str:
    return f"<prd>\n{body.strip()}\n</prd>"


def _parallel(fn, items: list, workers: int = DEFAULT_PARALLEL_CALLS) -> list:
    if len(items) <= 1 or workers <= 1:
        return [fn(item) for item in items]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(fn, items))  # preserves input order -> deterministic results


def _workers(llm: Any) -> int:
    return int(getattr(llm, "max_parallel", DEFAULT_PARALLEL_CALLS))


# --------------------------------------------------------------------------- S2 extract_requirements


def section_user_message(section: Section, parsed: ParsedPRD) -> str:
    units = {u.id: u for u in parsed.units}
    lines = [f"[{uid}] {units[uid].text}" for uid in section.unit_ids]
    return f"Section: {' > '.join(section.path)}\n\n" + _prd_block("\n".join(lines))


def drafts_to_requirements(
    section_drafts: list[tuple[Section, RequirementDraftList]], parsed: ParsedPRD, findings: Findings | None = None
) -> list[Requirement]:
    """Attach unit IDs, derive content IDs in document order (suffixes for repeated quotes)."""
    findings = findings if findings is not None else []
    units = {u.id: u for u in parsed.units}
    rows: list[tuple[Section, Any, list[str]]] = []
    for section, draft in section_drafts:
        section_units = [units[uid] for uid in section.unit_ids]
        for req in draft.requirements:
            unit_ids = [uid for uid in req.unit_ids if uid in section.unit_ids]
            unknown = [uid for uid in req.unit_ids if uid not in section.unit_ids]
            if not unit_ids and section_units:
                best = max(section_units, key=lambda u: fuzz.partial_ratio(req.source_quote.lower(), u.text.lower()))
                unit_ids = [best.id]
                findings.append(_finding(
                    "REF-UNIT", f"Unknown unit ID(s) {unknown or '(none given)'} for quote {req.source_quote[:60]!r}; "
                    f"attached to best-matching unit {best.id}.", item_key=" > ".join(section.path)))
            elif unknown:
                findings.append(_finding(
                    "REF-UNIT", f"Dropped unknown unit ID(s) {unknown} for quote {req.source_quote[:60]!r}.",
                    item_key=" > ".join(section.path)))
            rows.append((section, req, sorted(set(unit_ids), key=lambda uid: units[uid].order)))
    rows.sort(key=lambda row: min((units[uid].order for uid in row[2]), default=10**9))
    ids = assign_requirement_ids([req.source_quote for _, req, _ in rows])
    return [
        Requirement(
            id=rid,
            unit_ids=unit_ids,
            source_quote=req.source_quote.strip(),
            section_path=section.path,
            kind=req.kind,
            statement=req.statement.strip(),
            context_reason=(req.context_reason or None) if req.kind is ReqKind.context_only else None,
        )
        for rid, (section, req, unit_ids) in zip(ids, rows)
        if unit_ids
    ]


def extract_requirements(parsed: ParsedPRD, llm: StructuredLLM, sections: list[Section] | None = None,
                         findings: Findings | None = None) -> list[Requirement]:
    targets = sections if sections is not None else [s for s in iter_sections(parsed.root) if s.unit_ids]
    system = system_prompt("extract_requirements")
    drafts = _parallel(
        lambda s: llm.structured(RequirementDraftList, system, section_user_message(s, parsed), role="extract"),
        targets, _workers(llm),
    )
    return drafts_to_requirements(list(zip(targets, drafts)), parsed, findings)


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


def _known_only(ids: list[str], known: set[str], check_id: str, item_key: str, what: str, findings: Findings) -> list[str]:
    unique = list(dict.fromkeys(ids))
    unknown = [i for i in unique if i not in known]
    if unknown:
        findings.append(_finding(check_id, f"Dropped unknown {what}: {', '.join(unknown)}.", item_key=item_key,
                                 requirement_ids=unknown if check_id == "REF-REQ" else None))
    return [i for i in unique if i in known]


def apply_story_plan(
    draft: StoryPlanDraft, requirements: list[Requirement], findings: Findings | None = None
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
        applies = _known_only([i for i in c.applies_to_requirement_ids if i != c.constraint_id], known,
                              "REF-REQ", c.constraint_id, "applies-to requirement ID(s)", findings)
        scopes[c.constraint_id] = applies
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
        r
        for r in requirements
        if r.kind is ReqKind.constraint
        and (r.id in cited or not r.applies_to_requirement_ids or cited & set(r.applies_to_requirement_ids))
    ]


def story_user_message(skeleton: StorySkeleton, requirements: list[Requirement], skeletons: list[StorySkeleton]) -> str:
    reqs = {r.id: r for r in requirements}
    own = [reqs[i] for i in skeleton.requirement_ids if i in reqs and reqs[i].kind is not ReqKind.constraint]
    constraints = applicable_constraints(skeleton, requirements)
    fmt = lambda r: f'[{r.id}] ({r.kind.value}) {r.statement}  | quote: "{r.source_quote}"'  # noqa: E731
    body = "\n".join(fmt(r) for r in own)
    cons = "\n".join(fmt(r) + ("" if r.applies_to_requirement_ids else "  [global]") for r in constraints) or "none"
    others = "\n".join(f"{s.key}: {s.title}" for s in skeletons if s.key != skeleton.key) or "none"
    return (
        f"Story key: {skeleton.key}\nStory title: {skeleton.title}\n\n"
        f"Requirements of this story:\n{_prd_block(body)}\n\n"
        f"Constraints that apply to this story:\n{_prd_block(cons)}\n\n"
        f"Other stories (for dependencies):\n{others}"
    )


def _task_labels(draft: TaskDraft, key: str, findings: Findings) -> list[Label]:
    allowed = _ALLOWED_AREAS[draft.track]
    area = draft.area
    if area not in allowed:
        area = allowed[0]
        findings.append(_finding("REF-AREA", f"Area {draft.area.value!r} does not fit track {draft.track.value!r}; "
                                 f"used {area.value!r}.", item_key=key))
    type_label = Label.type_spike if draft.is_spike else Label.type_task
    return [type_label, Label(f"area:{area.value}"), Label.prd_agent]


def apply_story_detail(
    skeleton: StorySkeleton, draft: StoryDetailDraft, known_req_ids: set[str], story_keys: set[str],
    taken_task_keys: set[str], findings: Findings | None = None,
) -> tuple[UserStory, list[TechnicalTask]]:
    findings = findings if findings is not None else []
    c = draft.story
    deps = [normalize_story_key(d) for d in c.dependencies]
    self_refs = [d for d in deps if d == skeleton.key]
    if self_refs:
        findings.append(_finding("REF-STORY", "Dropped a dependency of the story on itself.", item_key=skeleton.key))
    deps = _known_only([d for d in deps if d != skeleton.key], story_keys, "REF-STORY", skeleton.key,
                       "story dependency key(s)", findings)
    story = UserStory(
        key=skeleton.key,
        title=skeleton.title,
        as_a=c.as_a,
        i_want=c.i_want,
        so_that=c.so_that,
        business_description=c.business_description,
        business_value=c.business_value,
        acceptance_criteria=c.acceptance_criteria,
        edge_cases=[e for e in c.edge_cases if e.strip()],
        dependencies=deps,
        definition_of_done=[d for d in c.definition_of_done if d.strip()],
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
        tasks.append(
            TechnicalTask(
                key=key,
                story_key=skeleton.key,
                title=t.title.strip(),
                track=t.track,
                description=t.description,
                size=t.size,
                consumes_api=t.consumes_api,
                touches_db=t.touches_db,
                requirement_ids=_known_only(t.requirement_ids, known_req_ids, "REF-REQ", key, "requirement ID(s)", findings),
                derived_reason=t.derived_reason,
                definition_of_done=[d for d in t.definition_of_done if d.strip()],
                labels=_task_labels(t, key, findings),
            )
        )
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


# --------------------------------------------------------------------------- graph


def build_graph(llm: StructuredLLM, console: Console | None = None, checkpointer=None, timings: dict | None = None):
    """Compile the graph. `timings` (if given) receives {stage name: seconds}, also when a stage fails."""
    console = console or Console()
    timings = timings if timings is not None else {}

    def timed(name: str, fn):
        def run(state: AgentState) -> AgentState:
            started = time.monotonic()
            try:
                return fn(state)
            finally:
                timings[name] = round(time.monotonic() - started, 1)

        return run

    def stage(name: str) -> None:
        console.rule(f"[bold]{name}")

    def n_load_prd(state: AgentState) -> AgentState:
        stage("S1 load_prd")
        parsed = load_prd(state["prd_path"])
        previous = state_store.load_plan(Path(state["out_dir"]))
        sections = sum(1 for _ in iter_sections(parsed.root)) - 1
        console.print(f"{len(parsed.units)} units in {sections} sections · prd_hash {parsed.prd_hash[:12]}")
        console.print("Update run: previous plan loaded." if previous else "First run: no previous plan.")
        return {"parsed": parsed, "units": parsed.units, "previous_plan": previous, "reference_findings": [],
                "started_at": state.get("started_at") or time.monotonic()}

    def n_extract(state: AgentState) -> AgentState:
        stage("S2 extract_requirements")
        findings: Findings = []
        reqs = extract_requirements(state["parsed"], llm, findings=findings)
        actionable = sum(r.kind is not ReqKind.context_only for r in reqs)
        console.print(f"{len(reqs)} requirements ({actionable} actionable)")
        return {"requirements": reqs, "reference_findings": state.get("reference_findings", []) + findings}

    def n_plan(state: AgentState) -> AgentState:
        stage("S4 plan_stories")
        findings: Findings = []
        project, skeletons, reqs = plan_stories(state["requirements"], llm, state.get("previous_plan"), findings)
        console.print(f"Epic {project.key} · {len(skeletons)} stories")
        plan = TicketPlan(prd_hash=state["parsed"].prd_hash, project=project, requirements=reqs)
        return {"skeletons": skeletons, "requirements": reqs, "plan": plan,
                "reference_findings": state.get("reference_findings", []) + findings}

    def n_detail(state: AgentState) -> AgentState:
        stage("S5 detail_stories")
        findings: Findings = []
        stories, tasks = detail_stories(state["skeletons"], state["requirements"], llm, findings)
        console.print(f"{len(stories)} stories detailed · {len(tasks)} tasks")
        plan = state["plan"].model_copy(update={"stories": stories, "tasks": tasks})
        return {"plan": TicketPlan.model_validate(plan.model_dump()),
                "reference_findings": state.get("reference_findings", []) + findings}

    def n_render(state: AgentState) -> AgentState:
        stage("S8 render_preview")
        reports = [reference_report(state.get("reference_findings", []))]
        written = renderer.write_outputs(state["plan"], Path(state["out_dir"]), reports=reports)
        console.print(renderer.plan_tree(state["plan"]))
        return {"outputs": [str(p) for p in written]}

    def n_summary(state: AgentState) -> AgentState:
        stage("S11 summary")
        plan = state["plan"]
        console.print(
            f"Epic: 1 · Stories: {len(plan.stories)} · Tasks: {len(plan.tasks)} · "
            f"Requirements: {len(plan.requirements)}"
        )
        refs = state.get("reference_findings", [])
        if refs:
            console.print(f"[yellow]{len(refs)} reference finding(s) (unknown IDs dropped or replaced); "
                          "see validation_report.md.[/]")
        console.print(f"Outputs in {state['out_dir']}/ (plan.json, plan.md, requirements.md, validation_report.md, payloads/)")
        cost = getattr(llm, "cost", None)
        if cost is not None:
            console.print(f"[bold]Cost:[/] {cost.summary()}")
        if state.get("started_at"):
            per_stage = " · ".join(f"{k} {v:.1f}s" for k, v in timings.items())
            console.print(f"[bold]Time:[/] {time.monotonic() - state['started_at']:.1f}s ({per_stage})")
        console.print("[yellow]Checks (S3/S6/S7) and gates arrive in milestone 3; this plan is unchecked.[/]")
        return {}

    graph = StateGraph(AgentState)
    for name, fn in [
        ("load_prd", n_load_prd),
        ("extract_requirements", n_extract),
        ("plan_stories", n_plan),
        ("detail_stories", n_detail),
        ("render_preview", n_render),
        ("summary", n_summary),
    ]:
        graph.add_node(name, timed(name, fn))
    graph.add_edge(START, "load_prd")
    graph.add_edge("load_prd", "extract_requirements")
    graph.add_edge("extract_requirements", "plan_stories")
    graph.add_edge("plan_stories", "detail_stories")
    graph.add_edge("detail_stories", "render_preview")
    graph.add_edge("render_preview", "summary")
    graph.add_edge("summary", END)
    return graph.compile(checkpointer=checkpointer)
