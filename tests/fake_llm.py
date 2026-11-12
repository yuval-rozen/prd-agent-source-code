"""A deterministic stand-in for the LLM, used to test pipeline wiring without network or cache.

It answers from the user message only (no PRD-specific knowledge) and records every call.
"""

from __future__ import annotations

import re

from schemas import (
    AcceptanceCriterion,
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

_UNIT = re.compile(r"^\[(U-[0-9a-f-]+)\] (.+)$", re.MULTILINE)
_REQ = re.compile(r"^\[(R-[0-9a-f-]+)\] \((\w+)\) (.+?): ", re.MULTILINE)


class FakeLLM:
    def __init__(self):
        self.calls: list[tuple[str, str]] = []

    def structured(self, schema, system, user, *, role="generation"):
        self.calls.append((schema.__name__, user))
        if schema is RequirementDraftList:
            return self._extract(user)
        if schema is StoryPlanDraft:
            return self._plan(user)
        if schema is StoryDetailDraft:
            return self._detail(user)
        raise AssertionError(f"unexpected schema {schema}")

    @staticmethod
    def _extract(user: str) -> RequirementDraftList:
        reqs = []
        for uid, text in _UNIT.findall(user):
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
