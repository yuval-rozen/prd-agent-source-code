"""GitHub REST access (SPEC §6 S9/S10, §10, §11). Deterministic code only: the LLM never calls GitHub.

- Every call goes through one httpx client with retries (tenacity) for network errors, 5xx and rate limits
  (primary: x-ratelimit-reset; secondary: retry-after). Any other 4xx/5xx raises GitHubError and stops the
  run: a clear message, never a silent partial failure. Because publishing is idempotent, re-running after
  a failure resumes safely.
- dry_run=True (the default) performs reads normally but never sends a write: writes are logged and
  return placeholder results.
- Only issues that carry the prd-agent label AND the marker are ever touched. The token never appears in
  messages, logs or outputs.
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field

import httpx
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

log = logging.getLogger("prd_agent.github")

API = "https://api.github.com"
MARKER_RE = re.compile(r"<!-- prd-agent:key=([A-Z]+-[a-z0-9-]+);hash=([0-9a-f]+) -->")
AGENT_LABEL = "prd-agent"
WRITE_INTERVAL_S = 1.0  # GitHub asks integrators to space content-creating requests (secondary rate limits)
MAX_RATE_LIMIT_WAIT_S = 120.0

LABEL_COLORS = {"type:": "5319e7", "area:": "0e8a16", AGENT_LABEL: "ededed"}


class GitHubError(Exception):
    """A GitHub API call failed. The message never contains the token."""


class _Retryable(Exception):
    def __init__(self, message: str, wait_s: float = 0.0):
        super().__init__(message)
        self.wait_s = wait_s


@dataclass
class ExistingIssue:
    number: int
    title: str
    body: str
    labels: list[str]
    state: str
    key: str
    hash: str
    url: str = ""


@dataclass
class ListResult:
    issues: dict[str, ExistingIssue] = field(default_factory=dict)  # key -> issue
    ignored_unmarked: list[int] = field(default_factory=list)  # labelled prd-agent but no marker: never touched
    duplicate_keys: list[tuple[str, int]] = field(default_factory=list)  # second issue with an already-seen key


def parse_marker(body: str | None) -> tuple[str, str] | None:
    match = MARKER_RE.search(body or "")
    return (match.group(1), match.group(2)) if match else None


def _wait_for(response: httpx.Response) -> float:
    if response.headers.get("retry-after"):
        try:
            return float(response.headers["retry-after"])
        except ValueError:
            return 60.0
    if response.headers.get("x-ratelimit-remaining") == "0" and response.headers.get("x-ratelimit-reset"):
        return max(float(response.headers["x-ratelimit-reset"]) - time.time(), 1.0)
    return 0.0


def _is_rate_limited(response: httpx.Response) -> bool:
    if response.status_code == 429:
        return True
    if response.status_code == 403:
        text = response.text.lower()
        return response.headers.get("x-ratelimit-remaining") == "0" or "rate limit" in text
    return False


def _describe(response: httpx.Response, what: str) -> str:
    try:
        message = response.json().get("message", "")
    except ValueError:
        message = response.text[:200]
    hints = {
        401: "the token was rejected (expired or wrong); check GITHUB_TOKEN",
        403: "the token lacks permission; it needs Issues: read and write on this repository",
        404: "repository not found, or the token has no access to it; check GITHUB_REPO / --repo",
        410: "issues are disabled for this repository",
        422: "GitHub rejected the request as invalid",
    }
    hint = hints.get(response.status_code, "unexpected response")
    return f"GitHub {what} failed (HTTP {response.status_code}): {hint}. GitHub said: {message!r}"


class GitHubTool:
    def __init__(self, token: str, repo: str, *, dry_run: bool = True, client: httpx.Client | None = None,
                 write_interval_s: float = WRITE_INTERVAL_S, sleep=time.sleep):
        self.repo = repo
        self.dry_run = dry_run
        self.write_interval_s = write_interval_s
        self._sleep = sleep
        self._last_write = 0.0
        self._fake_number = 0
        self.writes: list[tuple[str, str]] = []  # (method, path) of writes sent (or skipped in dry run)
        self._client = client or httpx.Client(base_url=API, timeout=30.0)
        self._headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "prd-agent",
        }

    # ------------------------------------------------------------------ transport
    def _request(self, method: str, path: str, what: str, **kwargs) -> httpx.Response:
        @retry(retry=retry_if_exception(lambda e: isinstance(e, (_Retryable, httpx.TransportError))),
               stop=stop_after_attempt(4), wait=wait_exponential(multiplier=2, max=30), reraise=True)
        def send() -> httpx.Response:
            response = self._client.request(method, path, headers=self._headers, **kwargs)
            if _is_rate_limited(response):
                wait = min(_wait_for(response) or 30.0, MAX_RATE_LIMIT_WAIT_S)
                log.warning("GitHub rate limit on %s; waiting %.0fs", what, wait)
                self._sleep(wait)
                raise _Retryable(_describe(response, what))
            if response.status_code >= 500:
                raise _Retryable(_describe(response, what))
            return response

        try:
            response = send()
        except _Retryable as exc:
            raise GitHubError(f"{exc} (gave up after retries)") from None
        except httpx.TransportError as exc:
            raise GitHubError(f"GitHub {what} failed: network error {type(exc).__name__}") from None
        if response.status_code >= 400:
            raise GitHubError(_describe(response, what))
        return response

    def _paginate(self, path: str, what: str, params: dict) -> list[dict]:
        items, page = [], 1
        while True:
            response = self._request("GET", path, what, params={**params, "per_page": 100, "page": page})
            batch = response.json()
            items += batch
            if not batch or 'rel="next"' not in response.headers.get("link", ""):
                return items
            page += 1

    def _write(self, method: str, path: str, what: str, json: dict) -> dict | None:
        self.writes.append((method, path))
        if self.dry_run:
            log.info("dry run: %s %s (%s) not sent", method, path, what)
            return None
        wait = self.write_interval_s - (time.monotonic() - self._last_write)
        if wait > 0:
            self._sleep(wait)
        try:
            return self._request(method, path, what, json=json).json()
        finally:
            self._last_write = time.monotonic()

    # ------------------------------------------------------------------ reads
    def list_marked_issues(self) -> ListResult:
        """All issues (open and closed) with the prd-agent label, keyed by their marker key."""
        raw = self._paginate(f"/repos/{self.repo}/issues", "listing issues",
                             {"state": "all", "labels": AGENT_LABEL, "sort": "created", "direction": "asc"})
        result = ListResult()
        for item in raw:
            if "pull_request" in item:
                continue
            marker = parse_marker(item.get("body"))
            if marker is None:
                result.ignored_unmarked.append(item["number"])
                continue
            key, digest = marker
            if key in result.issues:
                result.duplicate_keys.append((key, item["number"]))
                continue
            result.issues[key] = ExistingIssue(
                number=item["number"], title=item.get("title", ""), body=item.get("body") or "",
                labels=[lb["name"] if isinstance(lb, dict) else lb for lb in item.get("labels", [])],
                state=item.get("state", "open"), key=key, hash=digest, url=item.get("html_url", ""),
            )
        return result

    def list_label_names(self) -> set[str]:
        return {lb["name"] for lb in self._paginate(f"/repos/{self.repo}/labels", "listing labels", {})}

    # ------------------------------------------------------------------ writes
    def ensure_labels(self, names: set[str]) -> list[str]:
        missing = sorted(set(names) - self.list_label_names())
        for name in missing:
            color = next((c for prefix, c in LABEL_COLORS.items() if name.startswith(prefix)), "ededed")
            self._write("POST", f"/repos/{self.repo}/labels", f"creating label {name}",
                        {"name": name, "color": color, "description": "Managed by prd-agent"})
        return missing

    def create_issue(self, title: str, body: str, labels: list[str]) -> int:
        data = self._write("POST", f"/repos/{self.repo}/issues", f"creating issue {title[:40]!r}",
                           {"title": title, "body": body, "labels": labels})
        if data is None:  # dry run: placeholder numbers never collide with real ones
            self._fake_number -= 1
            return self._fake_number
        return int(data["number"])

    def update_issue(self, number: int, **fields) -> None:
        self._write("PATCH", f"/repos/{self.repo}/issues/{number}", f"updating issue #{number}",
                    {k: v for k, v in fields.items() if v is not None})

    def comment(self, number: int, body: str) -> None:
        self._write("POST", f"/repos/{self.repo}/issues/{number}/comments", f"commenting on issue #{number}",
                    {"body": body})

    def issue_url(self, number: int) -> str:
        return f"https://github.com/{self.repo}/issues/{number}"


# --------------------------------------------------------------------------- plan <-> GitHub sync (S9 / S10)

from graphlib import TopologicalSorter  # noqa: E402

from schemas import SyncAction, SyncActionType, TicketPlan  # noqa: E402
from tools.renderer import build_payloads, content_hash  # noqa: E402

CLOSE_COMMENT = ("Closed by prd-agent: this ticket is no longer part of the plan generated from the current PRD. "
                 "The issue is kept (never deleted) for history.")


def publish_order(plan: TicketPlan) -> list[str]:
    """Epic -> stories (plan order) -> tasks with blockers first (ties in plan order)."""
    order = [plan.project.key, *(s.key for s in plan.stories)]
    position = {t.key: i for i, t in enumerate(plan.tasks)}
    sorter = TopologicalSorter({t.key: [b for b in t.blocked_by if b in position] for t in plan.tasks})
    sorter.prepare()
    tasks: list[str] = []
    while sorter.is_active():
        ready = sorted(sorter.get_ready(), key=position.__getitem__)
        tasks += ready
        sorter.done(*ready)
    return order + tasks


def sync_diff(plan: TicketPlan, listing: ListResult) -> list[SyncAction]:
    """SPEC §10: key missing -> create; hash differs (or issue closed) -> update; key not in plan -> close;
    same -> unchanged. Payload bodies use the issue numbers already known."""
    numbers = {k: i.number for k, i in listing.issues.items()}
    payloads = build_payloads(plan, numbers)
    actions = []
    for key in publish_order(plan):
        issue = listing.issues.get(key)
        if issue is None:
            actions.append(SyncAction(key=key, action=SyncActionType.create, payload=payloads[key]))
        elif issue.hash != content_hash(plan, key) or issue.state != "open":
            actions.append(SyncAction(key=key, action=SyncActionType.update, issue_number=issue.number,
                                      payload=payloads[key]))
        else:
            actions.append(SyncAction(key=key, action=SyncActionType.unchanged, issue_number=issue.number))
    plan_keys = {a.key for a in actions}
    for key, issue in sorted(listing.issues.items(), key=lambda kv: kv[1].number):
        if key not in plan_keys and issue.state == "open":
            actions.append(SyncAction(key=key, action=SyncActionType.close, issue_number=issue.number))
    return actions


@dataclass
class PublishResult:
    numbers: dict[str, int] = field(default_factory=dict)
    created: list[str] = field(default_factory=list)
    updated: list[str] = field(default_factory=list)
    closed: list[str] = field(default_factory=list)
    unchanged: list[str] = field(default_factory=list)
    relinked: list[str] = field(default_factory=list)  # pass 2 body refreshes with real issue numbers
    labels_created: list[str] = field(default_factory=list)


def publish(plan: TicketPlan, actions: list[SyncAction], gh: GitHubTool) -> PublishResult:
    """S10. Pass 1: labels, then create/update in publish order (blockers first). Pass 2: re-render the bodies
    of the issues written in pass 1 with the real issue numbers ("Parent: #N", "Blocked by: #N", child
    checklists) and patch the ones that changed. Removed tickets are closed with a comment, never deleted."""
    result = PublishResult()
    result.numbers = {a.key: a.issue_number for a in actions if a.issue_number is not None}
    labels = {str(lb) for item in [plan.project, *plan.stories, *plan.tasks] for lb in item.labels}
    result.labels_created = gh.ensure_labels(labels | {AGENT_LABEL})
    sent: dict[str, str] = {}
    for action in actions:  # pass 1, already in publish order
        if action.action not in (SyncActionType.create, SyncActionType.update):
            if action.action is SyncActionType.unchanged:
                result.unchanged.append(action.key)
            continue
        payload = build_payloads(plan, result.numbers)[action.key]
        if action.action is SyncActionType.create:
            result.numbers[action.key] = gh.create_issue(payload["title"], payload["body"], payload["labels"])
            result.created.append(action.key)
        else:
            gh.update_issue(action.issue_number, title=payload["title"], body=payload["body"],
                            labels=payload["labels"], state="open")
            result.updated.append(action.key)
        sent[action.key] = payload["body"]
    final = build_payloads(plan, result.numbers)  # pass 2
    for key, body in sent.items():
        if final[key]["body"] != body:
            gh.update_issue(result.numbers[key], body=final[key]["body"])
            result.relinked.append(key)
    for action in actions:
        if action.action is SyncActionType.close:
            gh.comment(action.issue_number, CLOSE_COMMENT)
            gh.update_issue(action.issue_number, state="closed", state_reason="not_planned")
            result.closed.append(action.key)
    return result
