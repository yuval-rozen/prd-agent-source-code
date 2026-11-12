"""S8 render_preview: deterministic Jinja rendering of issue bodies, payloads and review files (SPEC §6 S8).

The LLM never writes final issue Markdown. Issue references render as `#N` once an issue number is known
(publish pass 2) and as the ticket key before that.
"""

from __future__ import annotations

import json
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


def render_bodies(plan: TicketPlan, issue_numbers: dict[str, int] | None = None) -> dict[str, str]:
    """Return {ticket key: Markdown body} for the epic, every story and every task."""
    ref = _ref_fn(issue_numbers)
    reqs = {r.id: r for r in plan.requirements}
    bodies = {
        plan.project.key: _env.get_template("epic.md.j2").render(project=plan.project, stories=plan.stories, ref=ref)
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
    return {key: _tidy(body) for key, body in bodies.items()}


def build_payloads(plan: TicketPlan, issue_numbers: dict[str, int] | None = None) -> dict[str, dict]:
    """Raw GitHub REST payloads (POST /repos/{owner}/{repo}/issues) keyed by ticket key."""
    bodies = render_bodies(plan, issue_numbers)
    items = [plan.project, *plan.stories, *plan.tasks]
    return {
        item.key: {"title": item.title, "body": bodies[item.key], "labels": [str(lb) for lb in item.labels]}
        for item in items
    }


def citations(plan: TicketPlan) -> dict[str, list[str]]:
    """Requirement ID -> keys of the stories and tasks that cite it."""
    cited: dict[str, list[str]] = defaultdict(list)
    for item in [*plan.stories, *plan.tasks]:
        for rid in item.requirement_ids:
            cited[rid].append(item.key)
    return cited


def _md_cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def render_plan_md(plan: TicketPlan) -> str:
    payloads = build_payloads(plan)
    parts = [f"# {plan.project.title}\n", f"`{plan.project.key}` · labels: {', '.join(payloads[plan.project.key]['labels'])}\n"]
    parts.append(payloads[plan.project.key]["body"])
    for story in plan.stories:
        p = payloads[story.key]
        parts.append(f"\n---\n\n## {story.title}\n\n`{story.key}` · labels: {', '.join(p['labels'])}\n\n{p['body']}")
        for task in (t for t in plan.tasks if t.story_key == story.key):
            tp = payloads[task.key]
            parts.append(f"\n### {task.title}\n\n`{task.key}` · labels: {', '.join(tp['labels'])}\n\n{tp['body']}")
    return _tidy("\n".join(parts))


def render_requirements_md(plan: TicketPlan) -> str:
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


def render_validation_report(plan: TicketPlan, reports: list[ReviewReport] | None = None, status: str | None = None) -> str:
    cited = citations(plan)
    lines = ["# Validation report\n", f"**Final status:** {status or 'NOT CHECKED'}\n"]
    if not reports:
        lines.append("No checks have run on this plan yet.\n")
    for report in reports or []:
        lines += [
            f"## {report.stage} — round {report.round}: {report.verdict.value} "
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


def write_outputs(plan: TicketPlan, out_dir: Path, reports: list[ReviewReport] | None = None, status: str | None = None) -> list[Path]:
    out_dir = Path(out_dir)
    payload_dir = out_dir / "payloads"
    payload_dir.mkdir(parents=True, exist_ok=True)
    for stale in payload_dir.glob("*.json"):
        stale.unlink()
    written = [save_plan(plan, out_dir)]
    files = {
        "plan.md": render_plan_md(plan),
        "requirements.md": render_requirements_md(plan),
        "validation_report.md": render_validation_report(plan, reports, status),
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
