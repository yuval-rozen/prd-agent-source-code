"""Milestone 4: marker + content hash, sync_diff and publish against a FakeGitHub, the S9/G2/S10 graph path."""

import re

import pytest
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command
from rich.console import Console

from agent import build_graph
from schemas import Label, ReviewFinding, Severity, Size, Status, SyncActionType, TechnicalTask, Track
from tests.fake_github import REPO, FakeGitHub
from tests.fake_llm import FakeLLM
from tests.test_pipeline import GENERIC_PRD
from tools.github_tool import GitHubError, parse_marker, publish, publish_order, read_sub_issues, sync_diff, tree_links
from tools.renderer import build_payloads, content_hash


@pytest.fixture
def prd_file(tmp_path):
    f = tmp_path / "prd.md"
    f.write_text(GENERIC_PRD, encoding="utf-8")
    return f


@pytest.fixture
def plan(prd_file, tmp_path):
    graph = build_graph(FakeLLM(), console=Console(quiet=True))
    return graph.invoke({"prd_path": str(prd_file), "out_dir": str(tmp_path / "plan-out"), "auto_yes": True})["plan"]


def _sync(plan, gh):
    tool = gh.tool()
    listing = tool.list_marked_issues()
    actions = sync_diff(plan, listing, read_sub_issues(tool, plan, listing))
    return actions, tool


def _counts(actions):
    return {k.value: sum(a.action is k for a in actions) for k in SyncActionType}


def _by_key(actions):
    """Issue-level actions by ticket key (sub-issue link actions are counted separately)."""
    return {a.key: a.action for a in actions if a.action is not SyncActionType.link}


def _n_links(plan):
    return len(plan.stories) + len(plan.tasks)


# --------------------------------------------------------------------------- renderer: marker and hash


def test_every_payload_ends_with_the_marker(plan):
    for key, payload in build_payloads(plan).items():
        assert parse_marker(payload["body"]) == (key, content_hash(plan, key))
        assert payload["body"].rstrip().endswith("-->")


def test_hash_does_not_change_when_issue_numbers_change(plan):
    keys = [plan.project.key, *(s.key for s in plan.stories), *(t.key for t in plan.tasks)]
    a = build_payloads(plan, {k: i + 1 for i, k in enumerate(keys)})
    b = build_payloads(plan, {k: i + 500 for i, k in enumerate(keys)})
    for key in keys:
        assert parse_marker(a[key]["body"]) == parse_marker(b[key]["body"]) == parse_marker(build_payloads(plan)[key]["body"])
    assert a[plan.stories[0].key]["body"] != b[plan.stories[0].key]["body"]  # the references did change


def test_hash_tracks_content_and_children(plan):
    story = plan.stories[0]
    before = content_hash(plan, story.key)
    renamed = plan.model_copy(update={"stories": [story.model_copy(update={"title": "Another title"}), *plan.stories[1:]]})
    assert content_hash(renamed, story.key) != before
    extra = TechnicalTask(key="QA-extra-suite", story_key=story.key, title="[QA] Add extra suite", track=Track.qa_general,
                          description="d", size=Size.S, derived_reason="testing",
                          labels=[Label.type_task, Label.area_qa, Label.prd_agent])
    assert content_hash(plan.model_copy(update={"tasks": [*plan.tasks, extra]}), story.key) != before


def test_plan_md_has_no_marker(plan, tmp_path):
    from tools.renderer import render_plan_md

    assert "prd-agent:key=" not in render_plan_md(plan)


# --------------------------------------------------------------------------- sync_diff + publish


def test_publish_order_is_epic_stories_then_blockers_first(plan):
    order = publish_order(plan)
    assert order[0] == plan.project.key
    assert order[1:1 + len(plan.stories)] == [s.key for s in plan.stories]
    position = {k: i for i, k in enumerate(order)}
    for t in plan.tasks:
        assert all(position[b] < position[t.key] for b in t.blocked_by)


def test_first_publish_creates_everything_with_real_references(plan):
    gh = FakeGitHub()
    actions, tool = _sync(plan, gh)
    assert _counts(actions) == {"create": 1 + len(plan.stories) + len(plan.tasks), "update": 0, "close": 0,
                                "link": _n_links(plan), "unchanged": 0}
    result = publish(plan, actions, tool)
    assert {str(lb) for i in [plan.project, *plan.stories, *plan.tasks] for lb in i.labels} <= set(gh.labels)
    numbers = result.numbers
    created_order = [gh.issues[numbers[k]]["number"] for k in publish_order(plan)]
    assert created_order == sorted(created_order)  # created in publish order
    epic_body = gh.issues[numbers[plan.project.key]]["body"]
    for s in plan.stories:
        body = gh.issues[numbers[s.key]]["body"]
        assert f"**Parent:** #{numbers[plan.project.key]}" in body
        assert f"- [ ] #{numbers[s.key]}" in epic_body
        for t in (t for t in plan.tasks if t.story_key == s.key):
            assert f"- [ ] #{numbers[t.key]}" in body
    for t in plan.tasks:
        body = gh.issues[numbers[t.key]]["body"]
        assert f"**Parent:** #{numbers[t.story_key]}" in body
        for b in t.blocked_by:
            assert f"- #{numbers[b]}" in body
        assert not re.search(r"`(?:US|FE|BE|QA|EPIC)-[a-z0-9-]+`", body.split("## Requirements")[0])  # all refs resolved
        assert parse_marker(body) == (t.key, content_hash(plan, t.key))


def test_second_run_changes_nothing(plan):
    gh = FakeGitHub()
    actions, tool = _sync(plan, gh)
    publish(plan, actions, tool)
    writes_after_first = len(gh.writes())
    again, tool2 = _sync(plan, gh)
    assert _counts(again)["unchanged"] == len(again) and len(again) == 1 + len(plan.stories) + len(plan.tasks)
    assert _counts(again)["link"] == 0
    publish(plan, again, tool2)
    assert len(gh.writes()) == writes_after_first  # no labels, issues or comments written


def test_modified_plan_creates_updates_and_closes(plan):
    gh = FakeGitHub()
    actions, tool = _sync(plan, gh)
    first = publish(plan, actions, tool)
    removed, renamed = plan.tasks[-1], plan.tasks[0]
    extra = TechnicalTask(key="QA-extra-suite", story_key=plan.stories[0].key, title="[QA] Add extra regression suite",
                          track=Track.qa_general, description="d", size=Size.S, derived_reason="testing",
                          labels=[Label.type_task, Label.area_qa, Label.prd_agent])
    tasks = [renamed.model_copy(update={"title": renamed.title + " v2"}), *plan.tasks[1:-1], extra]
    tasks = [t.model_copy(update={"blocked_by": [b for b in t.blocked_by if b != removed.key]}) for t in tasks]
    v2 = plan.model_copy(update={"tasks": tasks})
    actions2, tool2 = _sync(v2, gh)
    by_key = _by_key(actions2)
    assert by_key["QA-extra-suite"] is SyncActionType.create
    assert by_key[renamed.key] is SyncActionType.update
    assert by_key[removed.key] is SyncActionType.close
    result = publish(v2, actions2, tool2)
    closed_number = first.numbers[removed.key]
    assert gh.issues[closed_number]["state"] == "closed"  # closed, never deleted
    assert any(n == closed_number and "no longer part of the plan" in c for n, c in gh.comments)
    assert not any(m == "DELETE" for m, _ in gh.requests)
    assert gh.issues[first.numbers[renamed.key]]["title"].endswith(" v2")
    assert result.numbers["QA-extra-suite"] not in first.numbers.values()
    third, _ = _sync(v2, gh)
    assert all(a.action is SyncActionType.unchanged for a in third)


def test_issues_without_marker_are_never_touched(plan):
    gh = FakeGitHub()
    unmarked = gh.add_issue(plan.tasks[0].title, "Written by a human.", labels=["prd-agent"])
    unlabelled = gh.add_issue("Unrelated bug", f"mentions {plan.tasks[0].key}")
    pr = gh.add_issue("A pull request", build_payloads(plan)[plan.tasks[1].key]["body"], labels=["prd-agent"], pr=True)
    tool = gh.tool()
    listing = tool.list_marked_issues()
    assert listing.ignored_unmarked == [unmarked] and listing.issues == {}
    publish(plan, sync_diff(plan, listing), tool)
    touched = {int(m.group(1)) for _, p in gh.writes() if (m := re.search(r"/issues/(\d+)", p))}
    assert not touched & {unmarked, unlabelled, pr}
    assert gh.issues[unmarked]["body"] == "Written by a human."


def test_closed_managed_issue_is_reopened_when_back_in_plan(plan):
    gh = FakeGitHub()
    actions, tool = _sync(plan, gh)
    numbers = publish(plan, actions, tool).numbers
    gh.issues[numbers[plan.tasks[0].key]]["state"] = "closed"
    again, tool2 = _sync(plan, gh)
    assert _by_key(again)[plan.tasks[0].key] is SyncActionType.update
    publish(plan, again, tool2)
    assert gh.issues[numbers[plan.tasks[0].key]]["state"] == "open"


def test_pagination_reads_every_page(plan):
    gh = FakeGitHub(page_size=3)
    actions, tool = _sync(plan, gh)
    publish(plan, actions, tool)
    listing = gh.tool().list_marked_issues()
    assert len(listing.issues) == 1 + len(plan.stories) + len(plan.tasks)


def test_dry_run_sends_no_writes(plan):
    gh = FakeGitHub()
    tool = gh.tool(dry_run=True)
    result = publish(plan, sync_diff(plan, tool.list_marked_issues()), tool)
    assert gh.writes() == [] and gh.issues == {}
    assert len(result.created) == 1 + len(plan.stories) + len(plan.tasks) and tool.writes


# --------------------------------------------------------------------------- errors and retries


def test_auth_error_is_clear_and_never_leaks_the_token():
    gh = FakeGitHub()
    gh.fail_once("GET", r"/repos/.*/issues", 401)
    with pytest.raises(GitHubError) as info:
        gh.tool().list_marked_issues()
    assert "HTTP 401" in str(info.value) and "GITHUB_TOKEN" in str(info.value)
    assert "fake-token-value" not in str(info.value)


def test_not_found_and_permission_errors_stop(plan):
    gh = FakeGitHub()
    gh.fail_once("POST", r"/repos/.*/issues", 403)
    actions, tool = _sync(plan, gh)
    with pytest.raises(GitHubError, match="Issues: read and write"):
        publish(plan, actions, tool)


def test_server_errors_and_rate_limits_are_retried(plan):
    gh = FakeGitHub()
    gh.fail_once("GET", r"/repos/.*/issues", 502)
    gh.fail_once("GET", r"/repos/.*/issues", 403, {"retry-after": "3", "x-ratelimit-remaining": "0"})
    sleeps = []
    tool = gh.tool()
    tool._sleep = sleeps.append
    assert tool.list_marked_issues().issues == {}
    assert 3.0 in sleeps


# --------------------------------------------------------------------------- graph: S9 / G2 / S10


def _graph(llm, gh, checkpointer=None):
    return build_graph(llm, console=Console(quiet=True), checkpointer=checkpointer, github=gh.tool())


def test_graph_publish_with_g2_confirmation_then_zero_changes(prd_file, tmp_path):
    gh = FakeGitHub()
    graph = _graph(FakeLLM(), gh, MemorySaver())
    config = {"configurable": {"thread_id": "p"}}
    initial = {"prd_path": str(prd_file), "out_dir": str(tmp_path / "out"), "publish": True}
    first = graph.invoke(initial, config)
    assert first["__interrupt__"][0].value["gate"] == "G1"
    second = graph.invoke(Command(resume={"action": "approve"}), config)
    g2 = second["__interrupt__"][0].value
    assert g2["gate"] == "G2" and g2["counts"]["create"] + g2["counts"]["link"] == len(g2["changes"]) and gh.writes() == []
    assert g2["counts"]["create"] > 0 and g2["counts"]["link"] > 0
    final = graph.invoke(Command(resume={"action": "confirm"}), config)
    assert len(final["publish_result"]["created"]) == g2["counts"]["create"]
    # Second run with --yes: G2 sees no changes and nothing is written.
    writes = len(gh.writes())
    again = _graph(FakeLLM(), gh).invoke({**initial, "out_dir": str(tmp_path / "out2"), "auto_yes": True})
    assert again["publish_decision"] == "confirm" and all(a.action is SyncActionType.unchanged for a in again["sync_actions"])
    assert len(gh.writes()) == writes


def test_g2_abort_writes_nothing(prd_file, tmp_path):
    gh = FakeGitHub()
    graph = _graph(FakeLLM(), gh, MemorySaver())
    config = {"configurable": {"thread_id": "a"}}
    graph.invoke({"prd_path": str(prd_file), "out_dir": str(tmp_path / "out"), "publish": True}, config)
    graph.invoke(Command(resume={"action": "approve"}), config)
    final = graph.invoke(Command(resume={"action": "abort"}), config)
    assert final["publish_decision"] == "abort" and gh.writes() == []


def test_g2_refuses_needs_review_unless_forced(prd_file, tmp_path):
    unroutable = [[ReviewFinding(check_id="CRIT-MISSING", severity=Severity.blocking, message="unroutable")]]
    for force, expected in ((False, "refused"), (True, "confirm")):
        gh = FakeGitHub()
        graph = _graph(FakeLLM(critic_findings=unroutable), gh, MemorySaver())
        config = {"configurable": {"thread_id": f"f{force}"}}
        first = graph.invoke({"prd_path": str(prd_file), "out_dir": str(tmp_path / f"o{force}"), "publish": True,
                              "auto_yes": True, "force": force}, config)
        assert first["status"] is Status.NEEDS_REVIEW and first["__interrupt__"][0].value["gate"] == "G1"
        final = graph.invoke(Command(resume={"action": "approve"}), config)
        assert final["publish_decision"] == expected
        assert (gh.writes() == []) is (not force)


def test_task_body_keeps_a_blank_line_before_each_heading(plan):
    for t in plan.tasks:
        body = build_payloads(plan)[t.key]["body"]
        assert not re.search(r"[^\n]\n## ", body), body[:200]


# --------------------------------------------------------------------------- native sub-issue tree


def _expected_tree(plan, numbers):
    tree = {numbers[plan.project.key]: [numbers[s.key] for s in plan.stories]}
    for s in plan.stories:
        kids = [numbers[k] for p, k in tree_links(plan) if p == s.key]
        if kids:
            tree[numbers[s.key]] = kids
    return tree


def test_first_publish_builds_the_native_tree_with_issue_ids(plan):
    gh = FakeGitHub()
    actions, tool = _sync(plan, gh)
    result = publish(plan, actions, tool)
    assert gh.tree() == _expected_tree(plan, result.numbers)  # the fake rejects numbers: links used issue ids
    assert len(result.linked) == _n_links(plan)
    epic_body = gh.issues[result.numbers[plan.project.key]]["body"]
    assert all(f"- [ ] #{result.numbers[s.key]}" in epic_body for s in plan.stories)  # checklist fallback kept


def test_second_run_adds_no_links(plan):
    gh = FakeGitHub()
    actions, tool = _sync(plan, gh)
    publish(plan, actions, tool)
    writes = len(gh.writes())
    again, tool2 = _sync(plan, gh)
    assert _counts(again)["link"] == 0
    publish(plan, again, tool2)
    assert len(gh.writes()) == writes
    assert not any("sub_issues" in p for m, p in gh.writes()[writes:])


def test_already_published_issues_get_only_the_missing_links(plan):
    """The upgrade path: issues published before sub-issue support, one link already made by hand."""
    gh = FakeGitHub()
    numbers = {}
    for key in publish_order(plan):
        payload = build_payloads(plan)[key]
        numbers[key] = gh.add_issue(payload["title"], payload["body"], payload["labels"])
    first_story = plan.stories[0].key
    gh.link(numbers[plan.project.key], numbers[first_story])
    actions, tool = _sync(plan, gh)
    counts = _counts(actions)
    assert counts["create"] == counts["update"] == counts["close"] == 0
    assert counts["link"] == _n_links(plan) - 1  # the existing link is skipped
    before = len(gh.writes())
    publish(plan, actions, tool)
    issue_writes = [p for m, p in gh.writes()[before:] if "sub_issues" not in p and "/labels" not in p]
    assert issue_writes == []  # only links (and missing labels) were written
    assert gh.tree() == _expected_tree(plan, numbers)
    again, _ = _sync(plan, gh)
    assert all(a.action is SyncActionType.unchanged for a in again)


def test_task_moved_to_another_story_is_re_parented(plan):
    gh = FakeGitHub()
    actions, tool = _sync(plan, gh)
    numbers = publish(plan, actions, tool).numbers
    task = next(t for t in plan.tasks if t.story_key == plan.stories[0].key)
    target = plan.stories[1].key
    moved = plan.model_copy(update={"tasks": [t.model_copy(update={"story_key": target}) if t.key == task.key else t
                                              for t in plan.tasks]})
    actions2, tool2 = _sync(moved, gh)
    links = [a for a in actions2 if a.action is SyncActionType.link]
    assert [(a.key, a.payload["parent"]) for a in links] == [(task.key, target)]
    publish(moved, actions2, tool2)
    assert numbers[task.key] in gh.tree()[numbers[target]]
    assert numbers[task.key] not in gh.tree().get(numbers[plan.stories[0].key], [])
    third, _ = _sync(moved, gh)
    assert _counts(third)["link"] == 0


def test_sub_issues_added_by_a_human_are_kept(plan):
    gh = FakeGitHub()
    actions, tool = _sync(plan, gh)
    numbers = publish(plan, actions, tool).numbers
    note = gh.add_issue("Human follow-up", "not managed")
    story = numbers[plan.stories[0].key]
    gh.link(story, note)
    again, tool2 = _sync(plan, gh)
    assert _counts(again)["link"] == 0
    publish(plan, again, tool2)
    assert note in gh.tree()[story]


def test_dry_run_adds_no_links(plan):
    gh = FakeGitHub()
    tool = gh.tool(dry_run=True)
    listing = tool.list_marked_issues()
    result = publish(plan, sync_diff(plan, listing, read_sub_issues(tool, plan, listing)), tool)
    assert gh.writes() == [] and gh.tree() == {} and len(result.linked) == _n_links(plan)
