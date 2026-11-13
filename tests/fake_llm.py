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
    StoryUpdateDraft,
    StoryRepairDraft,
    StoryEditsDraft,
    CriterionEditDraft,
    LineEditDraft,
    PlainRewriteDraft,
    PlainRewriteItemDraft,
    FindingFixDraft,
    TaskRevisionDraft,
    AddedPlacementDraft,
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

    def __init__(self, critic_findings=None, drop_units=(), place_added_in=None, rogue_revise=False,
                 repair_mode="revise_allowed", unresolved_calls=()):
        """unresolved_calls: critic call numbers (0-based) that leave the open findings they are shown unconfirmed;
        every other critic call confirms them as resolved.
        place_added_in: put an ADDED requirement into this existing task (revise_existing) instead of a new task.
        rogue_revise: also return a "revision" of every KEEP task (code must ignore it)."""
        self.place_added_in = place_added_in
        self.rogue_revise = rogue_revise
        self.unresolved_calls = set(unresolved_calls)
        self.open_seen: list[list[str]] = []  # the open-finding IDs each critic call was asked to verify
        # repair_mode for StoryRepairDraft: revise_allowed | rogue (also edits a task it may not) | new_task | close_new
        self.repair_mode = repair_mode
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
            open_ids = re.findall(r"^\[(F-[0-9a-f]{6})\]", user, re.MULTILINE)
            self.open_seen.append(open_ids)
            keep = self._critic_calls in self.unresolved_calls
            self._critic_calls += 1
            return ReviewReport(stage="critic", round=0, verdict=Verdict.pass_, findings=findings,
                                resolved=[] if keep else open_ids, still_open=open_ids if keep else [])
        if schema is RequirementDraftList:
            return self._extract(user)
        if schema is StoryPlanDraft:
            return self._plan(user)
        if schema is StoryDetailDraft:
            return self._detail(user)
        if schema is StoryUpdateDraft:
            return self._update(user)
        if schema is StoryRepairDraft:
            return self._repair(user)
        if schema is PlainRewriteDraft:
            return self._plain(user)
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


def _words(key: str) -> str:
    """Plain words for a ticket key (ticket text must not contain keys)."""
    return key.split("-", 1)[1].replace("-", " ")


def _task_draft(key: str, track: str, reqs: list[str], suffix: str) -> TaskDraft:
    t = Track(track)
    prefix = {"frontend": "[FE]", "backend": "[BE]", "qa_general": "[QA]"}[track]
    area = {"frontend": TaskArea.frontend, "backend": TaskArea.backend, "qa_general": TaskArea.qa}[track]
    return TaskDraft(key_slug=key.split("-", 1)[1], title=f"{prefix} {_words(key)} {suffix}", track=t, area=area,
                     description=f"{suffix} {_words(key)}", size=Size.S, consumes_api=False, touches_db=False,
                     requirement_ids=reqs, derived_reason=None if reqs else "testing", is_spike=False,
                     definition_of_done=[f"{_words(key)} done"])


_TASK_LINE = re.compile(r"^(KEEP|REVISE|CLOSE) (\S+) \[(\w+), .*\| requirements: ([^|\n]*)", re.MULTILINE)


def _update(self, user: str) -> StoryUpdateDraft:
    key = re.search(r"^Story key: (\S+)", user, re.MULTILINE).group(1)
    revised, placements = [], []
    for mark, task_key, track, reqs in _TASK_LINE.findall(user):
        ids = [r.strip() for r in reqs.split(",") if r.strip().startswith("R-")]
        if mark == "REVISE" or (mark == "KEEP" and self.rogue_revise):
            revised.append(TaskRevisionDraft(task_key=task_key, task=_task_draft(task_key, track, ids, "revised")))
    for rid in re.findall(r"^ADDED \[(R-[0-9a-f-]+)\]", user, re.MULTILINE):
        if self.place_added_in:
            placements.append(AddedPlacementDraft(requirement_id=rid, mode="revise_existing", task_key=self.place_added_in,
                                                  task=_task_draft(self.place_added_in, "backend", [], "extended")))
        else:
            placements.append(AddedPlacementDraft(requirement_id=rid, mode="new_task",
                                                  task=_task_draft("BE-new-" + rid.lower(), "backend", [rid], "new")))
    ac = [AcceptanceCriterion(given="a member", when="they act", then=f"the change for {_words(key)} is visible"),
          AcceptanceCriterion(given="a member", when="the action fails", then="an error message is shown")]
    content = StoryContentDraft(as_a="user", i_want=f"updated {_words(key)}", so_that="it matches the PRD",
                                business_description="Updated.", business_value="Value.", acceptance_criteria=ac,
                                edge_cases=[], dependencies=[], definition_of_done=["Updated"])
    return StoryUpdateDraft(story=content, revised_tasks=revised, added_requirements=placements)


FakeLLM._update = _update


_FINDING = re.compile(r"^FINDING (\d+) .*\| may revise: ([^\n]+)$", re.MULTILINE)
_STORY_TASK = re.compile(r"^((?:FE|BE|QA)-\S+) \[(\w+), .*\| requirements: ([^|\n]*)(\| created in this run)?", re.MULTILINE)


def _repair(self, user: str) -> StoryRepairDraft:
    key = re.search(r"^Story key: (\S+)", user, re.MULTILINE).group(1)
    section = user.split("Current tasks of this story:")[1].split("Findings to fix:")[0]
    tasks = [(k, tr, [r.strip() for r in reqs.split(",") if r.strip().startswith("R-")], bool(new))
             for k, tr, reqs, new in _STORY_TASK.findall(section)]
    fixes = []
    for number, scope in _FINDING.findall(user):
        allowed = [k for k, *_ in tasks] if "any task of this story" in scope else [x.strip() for x in scope.split(",")]
        target = next(t for t in tasks if t[0] == allowed[0])
        chosen = [t for t in tasks if t[0] in allowed] if self.repair_mode == "revise_all" else [target]
        revised = [TaskRevisionDraft(task_key=t[0], task=_task_draft(t[0], t[1], t[2], "fixed")) for t in chosen]
        new_task, close = None, []
        if self.repair_mode == "rogue":
            other = next((t for t in tasks if t[0] not in allowed), None)
            if other:
                revised.append(TaskRevisionDraft(task_key=other[0], task=_task_draft(other[0], other[1], other[2], "rogue")))
        if self.repair_mode == "new_task":
            new_task = _task_draft("FE-fix-" + number, "frontend", target[2], "new")
        if self.repair_mode == "close_new":
            close = [t[0] for t in tasks if t[3]]
        fixes.append(FindingFixDraft(finding=int(number), revised_tasks=revised, new_task=new_task, close_tasks=close))
    # story-level edit: replace AC 1 and add one DoD line; everything else must stay byte-for-byte
    edits = StoryEditsDraft(
        acceptance_criteria=[CriterionEditDraft(op="replace", number=1, criterion=AcceptanceCriterion(
            given="a member", when="they act", then=f"{_words(key)} handles it"))],
        definition_of_done=[LineEditDraft(op="add", text="Fixed")])
    return StoryRepairDraft(story_edits=edits, fixes=fixes)


FakeLLM._repair = _repair

_NUMBERED = re.compile(r"^\[(\d+)\] \([^;]*; remove: [^)]*\) (.+)$", re.MULTILINE)
_NOTE = re.compile(r"\s*\(?\b(?:R-[0-9a-f]{8}(?:-\d+)?|(?:US|FE|BE|QA)-[a-z0-9]+(?:-[a-z0-9]+)*)\b\)?|"
                   r"\b(?:requirement ids?|reviewer decisions?|findings?|critic|the prd text)\b", re.IGNORECASE)


def _plain(self, user: str) -> PlainRewriteDraft:
    if getattr(self, "plain_sloppy_once", False):  # first rewrite leaves the notes in (code must retry)
        self.plain_sloppy_once = False
        return PlainRewriteDraft(rewrites=[PlainRewriteItemDraft(number=int(n), text=text)
                                           for n, text in _NUMBERED.findall(user)])
    return PlainRewriteDraft(rewrites=[PlainRewriteItemDraft(number=int(n), text=_NOTE.sub("", text).strip())
                                       for n, text in _NUMBERED.findall(user)])


FakeLLM._plain = _plain
