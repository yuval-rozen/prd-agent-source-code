"""An in-memory GitHub Issues API behind httpx.MockTransport, so GitHubTool's real HTTP code is exercised."""

from __future__ import annotations

import json
import re

import httpx

from tools.github_tool import GitHubTool

REPO = "owner/test-repo"


class FakeGitHub:
    def __init__(self, page_size: int = 100):
        self.issues: dict[int, dict] = {}
        self.labels: dict[str, dict] = {}
        self.comments: list[tuple[int, str]] = []
        self.parent_of: dict[int, int] = {}  # child issue id -> parent issue number (native sub-issues)
        self.children: dict[int, list[int]] = {}  # parent issue number -> child issue ids, in link order
        self.requests: list[tuple[str, str]] = []
        self.failures: list[tuple[str, str, int, dict]] = []  # (method, path regex, status, headers), used once each
        self.page_size = page_size
        self._next = 1

    # ------------------------------------------------------------------ test helpers
    def add_issue(self, title: str, body: str = "", labels: list[str] = (), state: str = "open", pr: bool = False) -> int:
        number = self._next
        self._next += 1
        issue = {"id": 900000 + number, "number": number, "title": title, "body": body, "state": state,
                 "labels": [{"name": n} for n in labels], "html_url": f"https://github.com/{REPO}/issues/{number}"}
        if pr:
            issue["pull_request"] = {"url": "x"}
        self.issues[number] = issue
        return number

    def link(self, parent_number: int, child_number: int) -> None:
        child_id = self.issues[child_number]["id"]
        self.parent_of[child_id] = parent_number
        self.children.setdefault(parent_number, []).append(child_id)

    def tree(self) -> dict[int, list[int]]:
        """parent number -> child numbers, from the native sub-issue links."""
        by_id = {i["id"]: n for n, i in self.issues.items()}
        return {p: [by_id[c] for c in kids] for p, kids in self.children.items() if kids}

    def fail_once(self, method: str, path_regex: str, status: int, headers: dict | None = None) -> None:
        self.failures.append((method, path_regex, status, headers or {}))

    def writes(self) -> list[tuple[str, str]]:
        return [r for r in self.requests if r[0] != "GET"]

    def tool(self, *, dry_run: bool = False) -> GitHubTool:
        client = httpx.Client(base_url="https://api.github.com", transport=httpx.MockTransport(self.handle))
        return GitHubTool("fake-token-value", REPO, dry_run=dry_run, client=client, write_interval_s=0,
                          sleep=lambda s: None)

    # ------------------------------------------------------------------ server
    def handle(self, request: httpx.Request) -> httpx.Response:
        method, path = request.method, request.url.path
        self.requests.append((method, path))
        assert request.headers["Authorization"] == "Bearer fake-token-value"
        for i, (m, rx, status, headers) in enumerate(self.failures):
            if m == method and re.fullmatch(rx, path):
                del self.failures[i]
                return httpx.Response(status, json={"message": f"injected {status}"}, headers=headers)
        base = f"/repos/{REPO}"
        body = json.loads(request.content) if request.content else {}
        if method == "GET" and path == f"{base}/issues":
            params = request.url.params
            wanted = params.get("labels")
            items = [i for i in sorted(self.issues.values(), key=lambda x: x["number"])
                     if not wanted or wanted in {lb["name"] for lb in i["labels"]}]
            return self._page(items, params)
        if method == "GET" and path == f"{base}/labels":
            return self._page(list(self.labels.values()), request.url.params)
        if method == "POST" and path == f"{base}/labels":
            self.labels[body["name"]] = {"name": body["name"], "color": body.get("color")}
            return httpx.Response(201, json=self.labels[body["name"]])
        if method == "POST" and path == f"{base}/issues":
            for name in body.get("labels", []):
                self.labels.setdefault(name, {"name": name})
            number = self.add_issue(body["title"], body.get("body", ""), body.get("labels", []))
            return httpx.Response(201, json=self.issues[number])
        sub = re.fullmatch(rf"{re.escape(base)}/issues/(\d+)/sub_issues", path)
        if sub:
            parent = int(sub.group(1))
            if parent not in self.issues:
                return httpx.Response(404, json={"message": "Not Found"})
            if method == "GET":
                kids = [i for i in self.issues.values() if i["id"] in self.children.get(parent, [])]
                return self._page(kids, request.url.params)
            child_id = body["sub_issue_id"]
            if child_id not in {i["id"] for i in self.issues.values()}:
                return httpx.Response(422, json={"message": "sub_issue_id is not a valid issue id"})
            current = self.parent_of.get(child_id)
            if current == parent:
                return httpx.Response(422, json={"message": "Issue may not contain duplicate sub-issues"})
            if current is not None and not body.get("replace_parent"):
                return httpx.Response(422, json={"message": "Issue may not have more than one parent"})
            if current is not None:
                self.children[current].remove(child_id)
            self.parent_of[child_id] = parent
            self.children.setdefault(parent, []).append(child_id)
            return httpx.Response(201, json=self.issues[parent])
        match = re.fullmatch(rf"{re.escape(base)}/issues/(\d+)(/comments)?", path)
        if match:
            number = int(match.group(1))
            if number not in self.issues:
                return httpx.Response(404, json={"message": "Not Found"})
            if match.group(2) and method == "POST":
                self.comments.append((number, body["body"]))
                return httpx.Response(201, json={"id": len(self.comments)})
            if method == "PATCH":
                issue = self.issues[number]
                for field in ("title", "body", "state"):
                    if field in body:
                        issue[field] = body[field]
                if "labels" in body:
                    issue["labels"] = [{"name": n} for n in body["labels"]]
                return httpx.Response(200, json=issue)
        return httpx.Response(404, json={"message": f"no route {method} {path}"})

    def _page(self, items: list, params) -> httpx.Response:
        per_page = min(int(params.get("per_page", 30)), self.page_size)
        page = int(params.get("page", 1))
        chunk = items[(page - 1) * per_page: page * per_page]
        headers = {"link": f'<https://api.github.com/x?page={page + 1}>; rel="next"'} if page * per_page < len(items) else {}
        return httpx.Response(200, json=chunk, headers=headers)
