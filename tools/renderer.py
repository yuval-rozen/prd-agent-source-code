"""S8 render_preview: deterministic Jinja rendering of issue bodies, payloads and review files (SPEC §6 S8).

The LLM never writes final issue Markdown. Issue references render as `#N` once an issue number is known
(publish pass 2) and as the ticket key before that.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined
from rich.tree import Tree

from schemas import ReqKind, ReviewReport, TicketPlan
from tools.state_store import save_plan

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"

_env = Environment(
    loader=FileSystemLoader(TEMPLATE_DIR),
    undefined=StrictUndefined,
    trim_blocks=True,
    lstrip_blocks=True,
    keep_trailing_newline=True,
    autoescape=False,
)


def _ref_fn(issue_numbers: dict[str, int] | None):
    numbers = issue_numbers or {}

    def ref(key: str) -> str:
        return f"#{numbers[key]}" if key in numbers else f"`{key}`"

    return ref


def _tidy(text: str) -> str:
    lines = [line.rstrip() for line in text.strip().split("\n")]
    out: list[str] = []
    for line in lines:
        if line == "" and out and out[-1] == "":
            continue
        out.append(line)
    return "\n".join(out) + "\n"


def content_hash(plan: TicketPlan, key: str) -> str:
    """Hash of a ticket's plan data (SPEC §10): title, content fields, labels, parent key, blocked_by keys, plus the
    keys of its children (so a story's task checklist is refreshed when tasks change). It is computed from the
    plan, never from the rendered body, so real issue numbers do not affect it."""
    items = {i.key: i for i in [plan.project, *plan.stories, *plan.tasks]}
    data = items[key].model_dump(mode="json")
    if key in {s.key for s in plan.stories}:
        data["_children"] = [t.key for t in plan.tasks if t.story_key == key]
    canonical = json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


def marker(key: str, digest: str) -> str:
    return f"<!-- prd-agent:key={key};hash={digest} -->"


def render_bodies(plan: TicketPlan, issue_numbers: dict[str, int] | None = None, with_marker: bool = True) -> dict[str, str]:
    """Return {ticket key: Markdown body} for the epic, every story and every task. Each body ends with the
    idempotency marker `<!-- prd-agent:key=<KEY>;hash=<content_hash> -->`."""
    ref = _ref_fn(issue_numbers)
    reqs = {r.id: r for r in plan.requirements}
    bodies = {
        plan.project.key: _env.get_template("epic.md.j2").render(
            project=plan.project, stories=plan.stories, ref=ref,
            requirements=[reqs[i] for i in plan.project.requirement_ids if i in reqs])
    }
    for story in plan.stories:
        bodies[story.key] = _env.get_template("story.md.j2").render(
            project=plan.project,
            story=story,
            tasks=[t for t in plan.tasks if t.story_key == story.key],
            requirements=[reqs[i] for i in story.requirement_ids if i in reqs],
            ref=ref,
        )
    for task in plan.tasks:
        bodies[task.key] = _env.get_template("task.md.j2").render(
            task=task, requirements=[reqs[i] for i in task.requirement_ids if i in reqs], ref=ref
        )
    out = {key: _tidy(body) for key, body in bodies.items()}
    if with_marker:
        out = {key: f"{body}\n{marker(key, content_hash(plan, key))}\n" for key, body in out.items()}
    return out


def build_payloads(plan: TicketPlan, issue_numbers: dict[str, int] | None = None, with_marker: bool = True) -> dict[str, dict]:
    """Raw GitHub REST payloads (POST /repos/{owner}/{repo}/issues) keyed by ticket key."""
    bodies = render_bodies(plan, issue_numbers, with_marker)
    items = [plan.project, *plan.stories, *plan.tasks]
    return {
        item.key: {"title": item.title, "body": bodies[item.key], "labels": [str(lb) for lb in item.labels]}
        for item in items
    }


def citations(plan: TicketPlan) -> dict[str, list[str]]:
    """Requirement ID -> keys of the epic, stories and tasks that cite it."""
    cited: dict[str, list[str]] = defaultdict(list)
    for item in [plan.project, *plan.stories, *plan.tasks]:
        for rid in item.requirement_ids:
            cited[rid].append(item.key)
    return cited


def _md_cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def demote_headings(markdown: str, levels: int) -> str:
    """Push every Markdown heading down by `levels` (## -> ### for 1), capped at ######."""
    return re.sub(r"^(#{1,6}) ", lambda m: "#" * min(len(m.group(1)) + levels, 6) + " ", markdown, flags=re.MULTILINE)


def render_plan_md(plan: TicketPlan) -> str:
    """One document: # epic > ## story > ### story sections and ### task > #### task sections.
    Issue bodies keep their own ## sections; only plan.md shifts them under their ticket heading."""
    payloads = build_payloads(plan, with_marker=False)  # the marker is for GitHub, not for reading
    parts = [f"# {plan.project.title}\n", f"`{plan.project.key}` · labels: {', '.join(payloads[plan.project.key]['labels'])}\n"]
    parts.append(payloads[plan.project.key]["body"])
    for story in plan.stories:
        p = payloads[story.key]
        parts.append(f"\n---\n\n## {story.title}\n\n`{story.key}` · labels: {', '.join(p['labels'])}\n\n"
                     f"{demote_headings(p['body'], 1)}")
        for task in (t for t in plan.tasks if t.story_key == story.key):
            tp = payloads[task.key]
            parts.append(f"\n### Task: {task.title}\n\n`{task.key}` · labels: {', '.join(tp['labels'])}\n\n"
                         f"{demote_headings(tp['body'], 2)}")
    return _tidy("\n".join(parts))


def render_requirement_diff(diff, plan: TicketPlan, previous_requirements) -> list[str]:
    new_by = {r.id: r for r in plan.requirements}
    old_by = {r.id: r for r in previous_requirements or []}
    lines = ["", "## Requirement diff (update run)", "",
             f"{len(diff.added)} added · {len(diff.changed)} changed · {len(diff.removed)} removed", ""]
    if diff.added or diff.changed or diff.removed:
        lines += ["| Change | Old | New |", "|---|---|---|"]
    for rid in diff.added:
        lines.append(f"| added | — | `{rid}` {_md_cell(new_by[rid].source_quote)} |")
    for old, new in diff.changed:
        lines.append(f"| changed | `{old}` {_md_cell(old_by[old].source_quote if old in old_by else '')} "
                     f"| `{new}` {_md_cell(new_by[new].source_quote)} |")
    for rid in diff.removed:
        lines.append(f"| removed | `{rid}` {_md_cell(old_by[rid].source_quote if rid in old_by else '')} | — |")
    return lines


def render_requirements_md(plan: TicketPlan, diff=None, previous_requirements=None) -> str:
    cited = citations(plan)
    by_kind: dict[ReqKind, list] = defaultdict(list)
    for req in plan.requirements:
        by_kind[req.kind].append(req)
    actionable = [r for r in plan.requirements if r.kind is not ReqKind.context_only]
    covered = [r for r in actionable if cited.get(r.id)]
    lines = [
        "# Requirements\n",
        f"- Total: {len(plan.requirements)} ({len(actionable)} actionable, "
        f"{len(plan.requirements) - len(actionable)} context only)",
        f"- Cited by at least one ticket: {len(covered)} / {len(actionable)} actionable",
        "",
        "| Kind | Count |",
        "|---|---|",
    ]
    counts = Counter(r.kind for r in plan.requirements)
    lines += [f"| {kind.value} | {counts[kind]} |" for kind in ReqKind if counts[kind]]
    if diff is not None:
        lines += render_requirement_diff(diff, plan, previous_requirements)
    for kind in ReqKind:
        reqs = by_kind.get(kind)
        if not reqs:
            continue
        lines += ["", f"## {kind.value}", "", "| ID | Section | Statement | Source quote | Cited by |", "|---|---|---|---|---|"]
        for r in reqs:
            extra = f" — {r.context_reason}" if r.context_reason else ""
            applies = f" (applies to: {', '.join(r.applies_to_requirement_ids) or 'all'})" if kind is ReqKind.constraint else ""
            lines.append(
                f"| `{r.id}` | {_md_cell(' > '.join(r.section_path[1:]) or '-')} | {_md_cell(r.statement + applies + extra)} "
                f"| {_md_cell(r.source_quote)} | {', '.join(f'`{k}`' for k in cited.get(r.id, [])) or '—'} |"
            )
    return "\n".join(lines) + "\n"


_WARNING_NOTES = {
    "P7": "Advisory dependency hint (SPEC §8 lists it as a warning); confirm the ordering at review.",
    "P10": "Sizing advisory (SPEC §8 lists it as a warning); split the item if the team agrees.",
}


def _why_remaining(f, stop_reasons: dict[str, str | None], stage: str) -> str:
    if f.check_id.startswith("REF-"):
        return "Code already applied the stated correction; listed for traceability."
    if f.severity.value == "blocking":
        reason = stop_reasons.get(stage) or "the repair loop stopped"
        return f"Not resolved: {reason}. Needs a human decision at G1 (approve, feedback or abort)."
    if f.check_id.startswith("CRIT-"):
        return "Non-blocking critic suggestion; it does not stop the pipeline."
    return _WARNING_NOTES.get(f.check_id, "Warning only; it does not block the pipeline.")


def render_remaining(reports: list[ReviewReport], stop_reasons: dict[str, str | None]) -> list[str]:
    latest: dict[str, ReviewReport] = {}
    for r in reports:
        latest[r.stage] = r  # reports are in order; keep the final round of each stage
    rows = [(stage, f) for stage, r in latest.items() for f in r.findings]
    lines = ["## Remaining findings", ""]
    if not rows:
        return lines + ["None.", ""]
    lines += ["Every finding still open in the final round of each stage, with the reason it remains.", "",
              "| Stage | Check | Severity | Item | Finding | Why it remains |", "|---|---|---|---|---|---|"]
    for stage, f in sorted(rows, key=lambda x: (x[1].severity.value != "blocking", x[0], x[1].check_id)):
        detail = f.message + (f" Suggested fix: {f.suggested_fix}" if f.suggested_fix else "")
        lines.append(f"| {stage} | {f.check_id} | {f.severity.value} | {f.item_key or '-'} | {_md_cell(detail)} "
                     f"| {_md_cell(_why_remaining(f, stop_reasons, stage))} |")
    return lines + [""]


def render_validation_report(plan: TicketPlan, reports: list[ReviewReport] | None = None, status: str | None = None,
                             stop_reasons: dict[str, str | None] | None = None) -> str:
    cited = citations(plan)
    stop_reasons = stop_reasons or {}
    lines = ["# Validation report\n", f"**Final status:** {status or 'NOT CHECKED'}\n"]
    lines += [f"- {stage}: {reason}" for stage, reason in stop_reasons.items() if reason]
    if any(stop_reasons.values()):
        lines.append("")
    if reports:
        lines += render_remaining(reports, stop_reasons)
        lines += ["## Findings per round", ""]
    if not reports:
        lines.append("No checks have run on this plan yet.\n")
    for report in reports or []:
        lines += [
            f"### {report.stage} — round {report.round}: {report.verdict.value} "
            f"({report.blocking_count} blocking, {report.warning_count} warnings)",
            "",
        ]
        if report.findings:
            lines += ["| Check | Severity | Item | Message | Suggested fix |", "|---|---|---|---|---|"]
            lines += [
                f"| {f.check_id} | {f.severity.value} | {f.item_key or '-'} | {_md_cell(f.message)} | {_md_cell(f.suggested_fix or '')} |"
                for f in report.findings
            ]
            lines.append("")
    lines += ["## Coverage matrix", "", "| Requirement | Kind | Tickets |", "|---|---|---|"]
    for r in plan.requirements:
        lines.append(f"| `{r.id}` | {r.kind.value} | {', '.join(f'`{k}`' for k in cited.get(r.id, [])) or '—'} |")
    return "\n".join(lines) + "\n"


def write_outputs(plan: TicketPlan, out_dir: Path, reports: list[ReviewReport] | None = None, status: str | None = None,
                  stop_reasons: dict[str, str | None] | None = None, requirement_diff=None,
                  previous_requirements=None) -> list[Path]:
    out_dir = Path(out_dir)
    payload_dir = out_dir / "payloads"
    payload_dir.mkdir(parents=True, exist_ok=True)
    for stale in payload_dir.glob("*.json"):
        stale.unlink()
    written = [save_plan(plan, out_dir)]
    files = {
        "plan.md": render_plan_md(plan),
        "requirements.md": render_requirements_md(plan, requirement_diff, previous_requirements),
        "validation_report.md": render_validation_report(plan, reports, status, stop_reasons),
    }
    for name, text in files.items():
        path = out_dir / name
        path.write_text(text, encoding="utf-8")
        written.append(path)
    for key, payload in build_payloads(plan).items():
        path = payload_dir / f"{key}.json"
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        written.append(path)
    return written


def plan_tree(plan: TicketPlan) -> Tree:
    tree = Tree(f"[bold]{plan.project.title}[/] [dim]{plan.project.key}[/]")
    for story in plan.stories:
        node = tree.add(f"[cyan]{story.title}[/] [dim]{story.key} · {len(story.acceptance_criteria)} ACs[/]")
        for task in (t for t in plan.tasks if t.story_key == story.key):
            node.add(f"{task.title} [dim]{task.key} · {task.size.value}[/]")
    return tree
