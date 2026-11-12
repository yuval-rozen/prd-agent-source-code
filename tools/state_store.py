"""Persisted plan state (out/plan.json). Its presence turns a run into an update run (SPEC §6 S1)."""

from __future__ import annotations

import logging
from pathlib import Path

from pydantic import ValidationError

from schemas import TicketPlan

log = logging.getLogger("prd_agent.state_store")

PLAN_FILE = "plan.json"


def plan_path(out_dir: Path) -> Path:
    return Path(out_dir) / PLAN_FILE


def load_plan(out_dir: Path) -> TicketPlan | None:
    """Return the previous plan, or None if there is none. An unreadable plan is reported, not fatal."""
    path = plan_path(out_dir)
    if not path.is_file():
        return None
    try:
        return TicketPlan.model_validate_json(path.read_text(encoding="utf-8"))
    except (ValidationError, ValueError) as exc:
        log.warning("ignoring unreadable previous plan %s: %s", path, type(exc).__name__)
        return None


def save_plan(plan: TicketPlan, out_dir: Path) -> Path:
    path = plan_path(out_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(plan.model_dump_json(indent=2) + "\n", encoding="utf-8")
    return path
