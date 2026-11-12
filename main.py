"""CLI entry point (SPEC §13).

Milestone 1: `run` executes S1 (load_prd) and prints a summary; later stages are added in milestone 2+.
"""

from __future__ import annotations

import json
import logging
import sys
from enum import IntEnum, StrEnum
from pathlib import Path
from typing import Annotated

import typer
from pydantic import ValidationError
from rich.console import Console
from rich.table import Table
from rich.tree import Tree

from config import ConfigError, load_settings
from schemas import TicketPlan
from tools.file_reader import PRDReadError, iter_sections, load_prd


class ExitCode(IntEnum):
    OK = 0
    ERROR = 1
    BAD_INPUT = 2
    CONFIG = 3
    LLM = 4
    GITHUB = 5
    ABORTED = 6


class PreviewFormat(StrEnum):
    table = "table"
    md = "md"
    json = "json"


app = typer.Typer(add_completion=False, no_args_is_help=True, help="PRD -> GitHub Issues agent.")
console = Console()
err_console = Console(stderr=True)
_state = {"debug": False}


def _fail(message: str, code: ExitCode, exc: BaseException | None = None) -> None:
    err_console.print(f"[bold red]Error:[/] {message}")
    if _state["debug"] and exc is not None:
        err_console.print_exception(show_locals=False)
    raise typer.Exit(int(code))


@app.callback()
def _main(debug: Annotated[bool, typer.Option("--debug", help="Show details and tracebacks.")] = False) -> None:
    _state["debug"] = debug
    logging.basicConfig(level=logging.DEBUG if debug else logging.WARNING, format="%(name)s: %(message)s")


@app.command()
def run(
    prd: Annotated[Path, typer.Argument(help="Path to the PRD (PDF / DOCX / MD / TXT).")],
    out: Annotated[Path, typer.Option("--out", help="Output directory.")] = Path("out"),
    replay: Annotated[bool, typer.Option("--replay", help="Run from the LLM cache; no API key needed.")] = False,
    yes: Annotated[bool, typer.Option("--yes", help="Auto-approve gates (only when status is PASS).")] = False,
    publish: Annotated[bool, typer.Option("--publish", help="Sync the plan to GitHub after approval.")] = False,
    repo: Annotated[str | None, typer.Option("--repo", help="Target repo owner/name (with --publish).")] = None,
    force: Annotated[bool, typer.Option("--force", help="Allow publishing a NEEDS_REVIEW plan.")] = False,
) -> None:
    """Run the pipeline on a PRD. Without --publish it is a dry run that stops after the plan review."""
    try:
        settings = load_settings()
        if publish:
            settings.require_github(repo)
    except ConfigError as exc:
        _fail(str(exc), ExitCode.CONFIG, exc)
    if repo and not publish:
        _fail("--repo is only used together with --publish.", ExitCode.BAD_INPUT)

    console.rule("[bold]S1 load_prd")
    try:
        parsed = load_prd(prd)
    except PRDReadError as exc:
        _fail(str(exc), ExitCode.BAD_INPUT, exc)

    tree = Tree(f"[bold]{prd.name}[/]  [dim]prd_hash={parsed.prd_hash[:12]}[/]")
    nodes = {(): tree}
    for section in iter_sections(parsed.root):
        if not section.path:
            continue
        parent = nodes[tuple(section.path[:-1])]
        nodes[tuple(section.path)] = parent.add(f"{section.title} [dim]({len(section.unit_ids)} units)[/]")
    console.print(tree)
    console.print(f"[green]Loaded[/] {len(parsed.units)} units in {sum(1 for _ in iter_sections(parsed.root)) - 1} sections.")
    console.print(
        "[yellow]Stages S2+ are not implemented yet (milestone 2). "
        f"Options recorded: out={out}, replay={replay}, yes={yes}, publish={publish}, force={force}.[/]"
    )


@app.command()
def preview(
    format: Annotated[PreviewFormat, typer.Option("--format", help="Output format.")] = PreviewFormat.table,
    out: Annotated[Path, typer.Option("--out", help="Output directory of a previous run.")] = Path("out"),
) -> None:
    """Show the saved plan from a previous run."""
    plan_path = out / "plan.json"
    if not plan_path.is_file():
        _fail(f"No saved plan at {plan_path}. Run `main.py run <prd>` first.", ExitCode.BAD_INPUT)
    try:
        plan = TicketPlan.model_validate_json(plan_path.read_text(encoding="utf-8"))
    except (ValidationError, json.JSONDecodeError) as exc:
        _fail(f"Saved plan at {plan_path} is invalid: {type(exc).__name__}", ExitCode.BAD_INPUT, exc)

    if format is PreviewFormat.json:
        console.print_json(plan.model_dump_json())
    elif format is PreviewFormat.md:
        md_path = out / "plan.md"
        if not md_path.is_file():
            _fail(f"No rendered plan at {md_path}.", ExitCode.BAD_INPUT)
        console.print(md_path.read_text(encoding="utf-8"), markup=False)
    else:
        table = Table(title=plan.project.title)
        for col in ("Key", "Type", "Title", "Parent", "Blocked by"):
            table.add_column(col)
        table.add_row(plan.project.key, "epic", plan.project.title, "", "")
        for story in plan.stories:
            table.add_row(story.key, "story", story.title, plan.project.key, "")
            for task in (t for t in plan.tasks if t.story_key == story.key):
                table.add_row(task.key, task.track.value, task.title, story.key, ", ".join(task.blocked_by))
        console.print(table)


if __name__ == "__main__":
    try:
        app()
    except KeyboardInterrupt:
        err_console.print("[yellow]Interrupted.[/]")
        sys.exit(int(ExitCode.ABORTED))
