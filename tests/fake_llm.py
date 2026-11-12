"""A deterministic stand-in for the LLM, used to test pipeline wiring without network or cache.

It answers from the user message only (no PRD-specific knowledge) and records every call.
"""

from __future__ import annotations

import re

from schemas import (
    AcceptanceCriterion,
    DependencyEdgeDraft,
    DependencyPlanDraft,
    ReviewFinding,
    ReviewReport,
    Severity,
    Verdict,
    ConstraintScopeDraft,
    EpicDraft,
    ReqKind,
    RequirementDraft,
    RequirementDraftList,
    Size,
    StoryContentDraft,
    StoryDetailDraft,
    StoryPlanDraft,
    StorySkeletonDraft,
    TaskArea,
    TaskDraft,
    Track,
    slugify,
)

_UNIT = re.compile(r"^\[(u\d+)\] (.+)$", re.MULTILINE)
_REQ = re.compile(r"^\[(R-[0-9a-f-]+)\] \((\w+)\) (.+?): ", re.MULTILINE)


class FakeLLM:
    """critic_findings: list of ReviewFinding lists, one per critic call (missing entries = no findings).
    drop_units: unit references the first extraction of a section silently skips (to exercise S3 repair)."""

    def __init__(self, critic_findings=None, drop_units=()):
        self.calls: list[tuple[str, str]] = []
        self.roles: list[str] = []
        self.critic_findings = list(critic_findings or [])
        self.drop_units = set(drop_units)
        self._critic_calls = 0

    def structured(self, schema, system, user, *, role="generation"):
        if isinstance(user, list):  # content blocks (the critic marks a cache breakpoint)
            user = "".join(block["text"] for block in user)
        self.calls.append((schema.__name__, user))
        self.roles.append(role)
        if schema is DependencyPlanDraft:
            return self._dependencies(user)
        if schema is ReviewReport:
            findings = self.critic_findings[self._critic_calls] if self._critic_calls < len(self.critic_findings) else []
            self._critic_calls += 1
            return ReviewReport(stage="critic", round=0, verdict=Verdict.pass_, findings=findings)
        if schema is RequirementDraftList:
            return self._extract(user)
        if schema is StoryPlanDraft:
            return self._plan(user)
        if schema is StoryDetailDraft:
            return self._detail(user)
        raise AssertionError(f"unexpected schema {schema}")

    def _extract(self, user: str) -> RequirementDraftList:
        reqs = []
        repairing = "had these problems" in user
        for uid, text in _UNIT.findall(user.split("A previous extraction")[0]):
            if uid in self.drop_units and not repairing:
                continue
            if text.rstrip().endswith(":"):
                kind, reason = ReqKind.context_only, "lead-in sentence"
            elif text.lower().startswith("all "):
                kind, reason = ReqKind.constraint, None
            else:
                kind, reason = ReqKind.functional, None
            reqs.append(RequirementDraft(unit_ids=[uid], source_quote=text, kind=kind, statement=text, context_reason=reason))
        return RequirementDraftList(requirements=reqs)

    @staticmethod
    def _plan(user: str) -> StoryPlanDraft:
        by_section: dict[str, list[str]] = {}
        constraints = []
        for rid, kind, section in _REQ.findall(user):
            if kind == "context_only":
                continue
            if kind == "constraint":
                constraints.append(rid)
            by_section.setdefault(section.split(" > ")[-1], []).append(rid)
        stories = [
            StorySkeletonDraft(key=f"US-{slugify(sec)}", title=f"Manage {sec.lower()}", requirement_ids=ids)
            for sec, ids in by_section.items()
        ]
        return StoryPlanDraft(
            epic=EpicDraft(title="Sample Product", scope="Everything in the PRD.", business_goals=["Ship it"]),
            stories=stories,
            constraint_scopes=[ConstraintScopeDraft(constraint_id=c, applies_to_requirement_ids=[]) for c in constraints],
        )

    @staticmethod
    def _dependencies(user: str) -> DependencyPlanDraft:
        keys = re.findall(r"^(\S+) \[(\w+), .*\(story (\S+)\)$", user, re.MULTILINE)
        edges = []
        for key, track, story in keys:
            if track != "backend":
                blockers = [k for k, t, s in keys if s == story and t == "backend"]
                edges.append(DependencyEdgeDraft(task_key=key, blocked_by=blockers + ["BE-unknown-task"]))
        return DependencyPlanDraft(edges=edges)

    @staticmethod
    def _detail(user: str) -> StoryDetailDraft:
        key = re.search(r"^Story key: (\S+)", user, re.MULTILINE).group(1)
        req_ids = re.findall(r"^\[(R-[0-9a-f-]+)\]", user.split("Constraints that apply")[0], re.MULTILINE)
        ac = [
            AcceptanceCriterion(given="a signed-in user", when="they submit valid input", then="the item is saved"),
            AcceptanceCriterion(given="a signed-in user", when="they submit an empty title", then="an error is shown"),
        ]
        slug = key[3:]
        tasks = [
            TaskDraft(key_slug=f"{slug} api", title=f"[BE] Add {slug} endpoint", track=Track.backend, area=TaskArea.backend,
                      description="Endpoint.", size=Size.M, consumes_api=False, touches_db=True, requirement_ids=req_ids,
                      is_spike=False, definition_of_done=["Endpoint merged"]),
            TaskDraft(key_slug=f"{slug} view", title=f"[FE] Build {slug} view", track=Track.frontend, area=TaskArea.db,
                      description="View.", size=Size.S, consumes_api=True, touches_db=False, requirement_ids=req_ids,
                      is_spike=False, definition_of_done=["View merged"]),
            TaskDraft(key_slug="tests", title=f"[QA] Test suite for {slug}", track=Track.qa_general, area=TaskArea.qa,
                      description="Tests.", size=Size.S, consumes_api=True, touches_db=False, requirement_ids=[],
                      derived_reason="testing", is_spike=False, definition_of_done=["Suite green"]),
        ]
        content = StoryContentDraft(
            as_a="user", i_want=f"to use {slug}", so_that="I get value", business_description="Desc.",
            business_value="Value.", acceptance_criteria=ac, edge_cases=["Empty input"], dependencies=["US-does-not-exist"],
            definition_of_done=["All ACs pass"],
        )
        return StoryDetailDraft(story=content, tasks=tasks)
