"""CLI entry point (SPEC §13).

Milestone 2: `run` executes S1 -> S2 -> S4 -> S5 -> S8 -> S11 (no checks or gates yet).
"""

from __future__ import annotations

import hashlib
import json
import logging
import sys
import time
import uuid
from enum import IntEnum, StrEnum
from pathlib import Path
from typing import Annotated

import typer
from pydantic import ValidationError
from rich.console import Console
from rich.table import Table

from agent import build_graph
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from langgraph.types import Command
from config import ConfigError, load_settings
from llm import LLM, BudgetExceeded, LLMError
from schemas import Status, TicketPlan
from tools.file_reader import PRDReadError
from tools.github_tool import GitHubError, GitHubTool


class ExitCode(IntEnum):
    OK = 0
    ERROR = 1
    BAD_INPUT = 2
    CONFIG = 3
    LLM = 4
    GITHUB = 5
    ABORTED = 6
    BUDGET = 7


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
    gate_answers: Annotated[Path | None, typer.Option(
        "--gate-answers", help="With --replay: the recorded G1 answers to offer (default: OUT/gate_answers.json).")] = None,
) -> None:
    """Run the pipeline on a PRD. Without --publish it is a dry run that stops after the plan review."""
    if repo and not publish:
        _fail("--repo is only used together with --publish.", ExitCode.BAD_INPUT)
    if not prd.is_file():
        _fail(f"PRD file not found: {prd}", ExitCode.BAD_INPUT)
    github = None
    try:
        settings = load_settings()
        if publish:
            token, target_repo = settings.require_github(repo)
            github = GitHubTool(token.get_secret_value(), target_repo, dry_run=False)
        llm = LLM(settings, replay=replay)
    except ConfigError as exc:
        _fail(str(exc), ExitCode.CONFIG, exc)

    prd_sha = hashlib.sha256(prd.read_bytes()).hexdigest()
    recorded = load_gate_answers(gate_answers or out / GATE_ANSWERS_FILE, prd_sha) if replay else None
    if replay and recorded:
        console.print(f"[dim]Recorded G1 answers found: {len(recorded['g1'])} (offered at each G1; G2 is never "
                      "answered from the recording).[/]")
    given: dict[str, list[dict]] = {"g1": [], "g2": []}
    timings: dict[str, float] = {}
    graph = build_graph(llm, console=console, timings=timings, checkpointer=MemorySaver(serde=_checkpoint_serde()),
                        max_repair_rounds=settings.max_repair_rounds, grounding_threshold=settings.grounding_threshold,
                        duplicate_threshold=settings.duplicate_title_threshold, github=github)
    config = {"configurable": {"thread_id": f"run-{uuid.uuid4().hex[:8]}"}, "recursion_limit": 100}
    initial = {"prd_path": str(prd), "out_dir": str(out), "publish": publish, "auto_yes": yes, "force": force}
    started = time.monotonic()
    outcome: dict = {"error": None, "exit_code": int(ExitCode.OK), "state": {}}
    try:
        result = graph.invoke(initial, config)
        while result.get("__interrupt__"):  # G1 approve_plan / G2 confirm_diff
            payload = result["__interrupt__"][0].value
            if payload.get("gate") == "G2":  # always a manual confirmation (or --yes), never from a recording
                answer = _ask_publish(payload)
                given["g2"].append(answer)
            else:
                offered = recorded["g1"][len(given["g1"])] if recorded and len(given["g1"]) < len(recorded["g1"]) else None
                answer = _ask_approval(payload, offered)
                given["g1"].append(answer)
            result = graph.invoke(Command(resume=answer), config)
        outcome["state"] = result
        if result.get("status") is Status.ABORTED:
            outcome.update(exit_code=int(ExitCode.ABORTED), error="aborted at G1")
        elif publish and result.get("publish_decision") in ("refused", "abort"):
            outcome.update(exit_code=int(ExitCode.ABORTED), error=f"publish {result['publish_decision']} at G2")
    except PRDReadError as exc:
        outcome.update(error=str(exc), exit_code=int(ExitCode.BAD_INPUT))
        _fail(str(exc), ExitCode.BAD_INPUT, exc)
    except BudgetExceeded as exc:
        outcome.update(error=str(exc), exit_code=int(ExitCode.BUDGET))
        _fail(str(exc), ExitCode.BUDGET, exc)
    except LLMError as exc:
        outcome.update(error=str(exc), exit_code=int(ExitCode.LLM))
        _fail(str(exc), ExitCode.LLM, exc)
    except GitHubError as exc:
        outcome.update(error=str(exc), exit_code=int(ExitCode.GITHUB))
        _fail(f"{exc} Publishing is idempotent: fix the cause and re-run to resume.", ExitCode.GITHUB, exc)
    finally:
        cache = llm.cache
        if cache.hits or cache.misses:
            console.print(f"[dim]LLM response cache: {cache.hits} hits, {cache.misses} misses · cost {llm.cost.summary()}[/]")
        _write_run_stats(out, settings, llm, timings, time.monotonic() - started, outcome, replay)
        if given["g1"] or given["g2"]:
            save_gate_answers(out / GATE_ANSWERS_FILE, prd_sha, given)
    if outcome["exit_code"] == int(ExitCode.ABORTED):
        raise typer.Exit(int(ExitCode.ABORTED))


def _checkpoint_serde() -> JsonPlusSerializer:
    """Allow LangGraph's checkpointer to restore our own schema types (and nothing else) at the G1 gate."""
    import schemas

    names = [n for n, obj in vars(schemas).items() if isinstance(obj, type) and obj.__module__ == "schemas"]
    return JsonPlusSerializer(allowed_msgpack_modules=[("schemas", n) for n in names])


GATE_ANSWERS_FILE = "gate_answers.json"


def save_gate_answers(path: Path, prd_sha: str, given: dict[str, list[dict]]) -> None:
    """Every run records the human gate answers next to its outputs (no secrets: only approve / feedback text /
    abort / confirm), so a --replay of the recording can offer the same G1 answers."""
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {"prd_sha256": prd_sha, "g1": given["g1"], "g2": given["g2"]}
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_gate_answers(path: Path, prd_sha: str) -> dict | None:
    """The recorded answers, only if they were recorded for this exact PRD file."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if data.get("prd_sha256") != prd_sha or not isinstance(data.get("g1"), list):
        return None
    return data


def _describe(answer: dict) -> str:
    return f"feedback: {answer.get('text', '')!r}" if answer.get("action") == "feedback" else answer.get("action", "?")


def _ask_approval(payload: dict, offered: dict | None = None) -> dict:
    """G1: show status and blocking findings; answer approve | feedback | abort. EOF (no terminal) = abort.
    In --replay, `offered` is the answer the recorded run gave at this G1: Enter accepts it, or type another."""
    console.rule("[bold]G1 review")
    console.print(f"Status: [bold]{payload['status']}[/] · {payload['stories']} stories · {payload['tasks']} tasks · "
                  f"{len(payload['blocking'])} blocking, {payload['warnings']} warnings")
    for f in payload["blocking"]:
        console.print(f"  [red]{f['check_id']}[/] {f.get('item_key') or '-'}: {f['message']}")
    diff = payload.get("requirement_diff")
    if diff:
        console.print(f"Requirement diff: {len(diff['added'])} added · {len(diff['changed'])} changed · "
                      f"{len(diff['removed'])} removed (see requirements.md)")
    console.print(f"Review {payload['out_dir']}/plan.md and validation_report.md.")
    try:
        if offered:
            console.print(f"Recorded answer: [bold]{_describe(offered)}[/]")
            choice = input("Enter = use the recorded answer, or type approve / feedback / abort: ").strip().lower()
            if not choice:
                return dict(offered)
        else:
            choice = input("approve / feedback / abort [abort]: ").strip().lower() or "abort"
        if choice.startswith("f"):
            return {"action": "feedback", "text": input("Feedback (mention ticket keys to target them): ")}
    except EOFError:
        choice = "abort"
    return {"action": "approve" if choice.startswith("ap") else "abort"}


def _ask_publish(payload: dict) -> dict:
    """G2: show the create / update / close actions; answer confirm | abort. EOF (no terminal) = abort."""
    console.rule("[bold]G2 confirm GitHub changes")
    counts = payload["counts"]
    console.print(f"{payload['repo']}: create {counts['create']} · update {counts['update']} · "
                  f"close {counts['close']} · sub-issue links {counts.get('link', 0)} · unchanged {counts['unchanged']}")
    for c in payload["changes"]:
        number = f"#{c['issue']}" if c.get("issue") else "new"
        detail = c.get("title") or (f"sub-issue of {c['parent']}" if c.get("parent") else "")
        cause = c.get("cause")
        why = f"  [dim]<- {'; '.join(cause)}[/]" if cause else ("  [red]<- no cause (churn)[/]" if cause is not None else "")
        console.print(f"  {c['action']:<7} {number:<6} {c['key']}  {detail}{why}")
    if payload.get("churn") is not None:
        console.print(f"Changes without a requirement cause (churn): {len(payload['churn'])}")
    try:
        choice = input("confirm / abort [abort]: ").strip().lower() or "abort"
    except EOFError:
        choice = "abort"
    return {"action": "confirm" if choice.startswith("c") else "abort"}


def _write_run_stats(out: Path, settings, llm: LLM, timings: dict, total_s: float, outcome: dict, replay: bool) -> None:
    """Machine-readable record of the run (no secrets), used to compare providers and models."""
    state = outcome.get("state") or {}
    stats = {
        "provider": settings.llm_provider,
        "models": {role: settings.model_for(role) for role in ("extract", "generation", "revision", "critic")},
        "google_thinking_level": settings.google_thinking_level if settings.llm_provider == "google" else None,
        "effort": {role: settings.effort_for(role) for role in ("extract", "generation", "revision", "critic")}
        if settings.llm_provider == "anthropic" else None,
        "replay": replay,
        "max_run_cost_usd": settings.max_run_cost_usd,
        "stage_seconds": timings,
        "total_seconds": round(total_s, 1),
        "cost_usd": round(llm.cost.spent_usd, 6),
        "cost_by_stage": {k: {**v, "cost_usd": round(v["cost_usd"], 6)} for k, v in llm.cost.by_stage.items()},
        "cost_by_role": {k: {**v, "cost_usd": round(v["cost_usd"], 6)} for k, v in llm.cost.by_role.items()},
        "status": state["status"].value if state.get("status") else None,
        "churn": state.get("churn"),
        "publish": {"decision": state.get("publish_decision"),
                    "counts": {k: len(v) for k, v in (state.get("publish_result") or {}).items() if isinstance(v, list)},
                    "epic_issue": (state.get("publish_result") or {}).get("numbers", {}).get(
                        state["plan"].project.key) if state.get("plan") else None} if state.get("publish") else None,
        "requirement_rounds": state.get("req_rounds"),
        "plan_repair_rounds": state.get("plan_rounds"),
        "blocking_history": {"check_requirements": state.get("req_blocking_history"),
                             "check_plan": state.get("plan_blocking_history")},
        "api_calls": llm.cost.live_calls,
        "cache_hits": llm.cache.hits,
        "tokens": llm.cost.tokens,
        "rate_limit_waits": llm.cost.rate_limit_waits,
        "server_retries": llm.cost.server_retries,
        "reference_findings": len(state.get("reference_findings") or []),
        "exit_code": outcome["exit_code"],
        "error": outcome["error"],
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / "run_stats.json").write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")


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
