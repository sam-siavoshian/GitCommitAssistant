"""Thin GitHub REST + GraphQL client.

Design rules:
- One `requests.Session` per client, consistent headers.
- `Authorization: Bearer ...` everywhere (PATs and OAuth tokens both accept Bearer).
- `X-GitHub-Api-Version: 2022-11-28` on REST.
- Honors `X-RateLimit-Reset` / `Retry-After` on 429.
- Exponential backoff (3 tries: 1s, 2s, 4s) on 5xx.
- Permanent 4xx never retried.
- Errors raise typed exceptions; callers decide policy.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any

import requests

from gca.config import api_base

log = logging.getLogger("gca.github_api")

USER_AGENT = "gca/2.0 (+https://github.com/sam-siavoshian/GitCommitAssistant)"
GRAPHQL_URL = "https://api.github.com/graphql"
DEFAULT_TIMEOUT = 30
RATE_SLEEP_CAP = 300  # never sleep more than 5 min waiting for rate-limit reset


class GitHubError(RuntimeError):
    def __init__(self, message: str, status: int | None = None, body: Any = None):
        super().__init__(message)
        self.status = status
        self.body = body


class GitHubAuthError(GitHubError):
    pass


class GitHubNotFound(GitHubError):
    pass


class PRExistsError(GitHubError):
    pass


class MergeBlockedError(GitHubError):
    pass


class DiscussionCategoryError(GitHubError):
    pass


@dataclass
class RepoRef:
    owner: str
    name: str
    default_branch: str

    @property
    def full(self) -> str:
        return f"{self.owner}/{self.name}"


class GitHubClient:
    def __init__(self, token: str, *, base_url: str | None = None, timeout: int = DEFAULT_TIMEOUT):
        if not token:
            raise GitHubAuthError("missing GitHub token")
        self.token = token
        self.base = (base_url or api_base()).rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": USER_AGENT,
            }
        )
        self._username: str | None = None
        self._primary_email: str | None = None
        self._scopes: set[str] | None = None

    # ---- low-level ----

    def _request(self, method: str, url: str, **kwargs) -> requests.Response:
        """Send with retries. URL may be relative ('/user') or absolute."""
        if url.startswith("/"):
            url = f"{self.base}{url}"
        kwargs.setdefault("timeout", self.timeout)
        last: requests.Response | None = None
        for attempt in range(4):
            resp = self.session.request(method, url, **kwargs)
            last = resp
            # Rate limit primary: x-ratelimit-remaining = 0
            remaining = resp.headers.get("x-ratelimit-remaining")
            if resp.status_code in (403, 429) and remaining == "0":
                self._sleep_for_reset(resp)
                continue
            if resp.status_code == 429:
                retry_after = float(resp.headers.get("retry-after", "2"))
                time.sleep(min(retry_after, RATE_SLEEP_CAP))
                continue
            if 500 <= resp.status_code < 600 and attempt < 3:
                time.sleep(2**attempt)
                continue
            return resp
        assert last is not None
        return last

    @staticmethod
    def _sleep_for_reset(resp: requests.Response) -> None:
        reset = resp.headers.get("x-ratelimit-reset")
        if reset and reset.isdigit():
            wait = max(0, int(reset) - int(time.time())) + 1
            time.sleep(min(wait, RATE_SLEEP_CAP))
        else:
            time.sleep(2)

    def _check(self, resp: requests.Response, *, allow_404: bool = False) -> Any:
        if resp.status_code == 404 and allow_404:
            return None
        if 200 <= resp.status_code < 300:
            if not resp.content:
                return None
            return resp.json()
        body: Any
        try:
            body = resp.json()
        except Exception:
            body = resp.text
        if resp.status_code in (401, 403) and self._is_auth_error(body):
            raise GitHubAuthError(self._msg(body), status=resp.status_code, body=body)
        if resp.status_code == 404:
            raise GitHubNotFound(self._msg(body), status=resp.status_code, body=body)
        raise GitHubError(self._msg(body), status=resp.status_code, body=body)

    @staticmethod
    def _is_auth_error(body: Any) -> bool:
        if isinstance(body, dict):
            msg = (body.get("message") or "").lower()
            return "bad credentials" in msg or "requires authentication" in msg
        return False

    @staticmethod
    def _msg(body: Any) -> str:
        if isinstance(body, dict):
            base_msg = body.get("message") or "unknown error"
            errors = body.get("errors")
            if errors:
                base_msg = f"{base_msg}: {errors}"
            return str(base_msg)
        return str(body)[:500]

    # ---- identity / scopes ----

    def whoami(self) -> str:
        if self._username:
            return self._username
        resp = self._request("GET", "/user")
        data = self._check(resp)
        self._username = data["login"]
        # cache scopes from headers
        scopes = resp.headers.get("x-oauth-scopes", "")
        self._scopes = {s.strip() for s in scopes.split(",") if s.strip()}
        return self._username

    def scopes(self) -> set[str]:
        if self._scopes is None:
            self.whoami()
        return self._scopes or set()

    def primary_verified_email(self) -> str | None:
        if self._primary_email:
            return self._primary_email
        resp = self._request("GET", "/user/emails")
        if resp.status_code == 404:
            return None
        try:
            data = self._check(resp)
        except GitHubError:
            return None
        for entry in data or []:
            if entry.get("primary") and entry.get("verified"):
                self._primary_email = entry.get("email")
                return self._primary_email
        return None

    # ---- repos ----

    def get_repo(self, owner: str, repo: str) -> RepoRef:
        data = self._check(self._request("GET", f"/repos/{owner}/{repo}"))
        return RepoRef(owner=data["owner"]["login"], name=data["name"], default_branch=data["default_branch"])

    def create_repo(self, name: str, *, private: bool = True, description: str = "") -> RepoRef:
        payload = {"name": name, "auto_init": True, "private": private, "description": description}
        resp = self._request("POST", "/user/repos", json=payload)
        if resp.status_code == 422:
            # already exists
            owner = self.whoami()
            return self.get_repo(owner, name)
        data = self._check(resp)
        return RepoRef(owner=data["owner"]["login"], name=data["name"], default_branch=data["default_branch"])

    def delete_repo(self, owner: str, repo: str) -> None:
        resp = self._request("DELETE", f"/repos/{owner}/{repo}")
        self._check(resp, allow_404=True)

    # ---- pull requests ----

    def create_pull_request(
        self, repo: RepoRef, *, head: str, title: str, body: str = "", base: str | None = None
    ) -> int:
        payload = {"title": title, "body": body, "head": head, "base": base or repo.default_branch}
        resp = self._request("POST", f"/repos/{repo.full}/pulls", json=payload)
        if resp.status_code == 422:
            data = resp.json() if resp.content else {}
            msg = self._msg(data)
            if "already exists" in msg.lower() or "a pull request already exists" in msg.lower():
                raise PRExistsError(msg, status=422, body=data)
            raise GitHubError(msg, status=422, body=data)
        data = self._check(resp)
        return int(data["number"])

    def merge_pull_request(
        self, repo: RepoRef, number: int, *, method: str = "squash"
    ) -> bool:
        if method not in ("merge", "squash", "rebase"):
            raise ValueError(f"invalid merge method: {method!r}")
        payload = {"merge_method": method}
        resp = self._request("PUT", f"/repos/{repo.full}/pulls/{number}/merge", json=payload)
        if resp.status_code == 405:
            data = resp.json() if resp.content else {}
            raise MergeBlockedError(self._msg(data), status=405, body=data)
        if resp.status_code == 409:
            data = resp.json() if resp.content else {}
            raise MergeBlockedError(self._msg(data), status=409, body=data)
        self._check(resp)
        return True

    def close_pull_request(self, repo: RepoRef, number: int) -> None:
        resp = self._request("PATCH", f"/repos/{repo.full}/pulls/{number}", json={"state": "closed"})
        self._check(resp)

    # ---- issues (for Quickdraw) ----

    def create_issue(self, repo: RepoRef, *, title: str, body: str = "") -> int:
        resp = self._request("POST", f"/repos/{repo.full}/issues", json={"title": title, "body": body})
        data = self._check(resp)
        return int(data["number"])

    def close_issue(self, repo: RepoRef, number: int) -> None:
        resp = self._request("PATCH", f"/repos/{repo.full}/issues/{number}", json={"state": "closed"})
        self._check(resp)

    # ---- GraphQL ----

    def graphql(self, query: str, variables: dict | None = None) -> dict:
        resp = self._request(
            "POST",
            GRAPHQL_URL,
            json={"query": query, "variables": variables or {}},
        )
        if resp.status_code >= 400:
            raise GitHubError(f"graphql HTTP {resp.status_code}: {resp.text[:300]}", status=resp.status_code)
        data = resp.json()
        if data.get("errors"):
            raise GitHubError(f"graphql errors: {data['errors']}", status=resp.status_code, body=data)
        return data["data"]

    # ---- discussions ----

    _Q_REPO_AND_CATS = """
    query($owner: String!, $name: String!) {
      repository(owner: $owner, name: $name) {
        id
        discussionCategories(first: 25) {
          nodes { id name slug isAnswerable }
        }
      }
    }
    """

    _M_CREATE_DISCUSSION = """
    mutation($repositoryId: ID!, $categoryId: ID!, $title: String!, $body: String!) {
      createDiscussion(input: {repositoryId: $repositoryId, categoryId: $categoryId, title: $title, body: $body}) {
        discussion { id number url }
      }
    }
    """

    _M_ADD_COMMENT = """
    mutation($discussionId: ID!, $body: String!) {
      addDiscussionComment(input: {discussionId: $discussionId, body: $body}) {
        comment { id }
      }
    }
    """

    _M_MARK_ANSWER = """
    mutation($id: ID!) {
      markDiscussionCommentAsAnswer(input: {id: $id}) {
        discussion { id }
      }
    }
    """

    def find_repo_and_qa_category(self, repo: RepoRef) -> tuple[str, str, str]:
        """Return (repository_id, category_id, category_name).

        Prefers a category whose slug is 'q-a'. Falls back to any isAnswerable category.
        Raises DiscussionCategoryError if Discussions are off or no answerable category exists.
        """
        data = self.graphql(self._Q_REPO_AND_CATS, {"owner": repo.owner, "name": repo.name})
        repo_node = data.get("repository")
        if not repo_node:
            raise DiscussionCategoryError(
                f"discussions appear to be disabled on {repo.full}. Enable in repo Settings > Features."
            )
        cats = (repo_node.get("discussionCategories") or {}).get("nodes") or []
        # exact 'q-a' slug first
        for c in cats:
            if c.get("slug") == "q-a" and c.get("isAnswerable"):
                return repo_node["id"], c["id"], c["name"]
        for c in cats:
            if c.get("isAnswerable"):
                return repo_node["id"], c["id"], c["name"]
        raise DiscussionCategoryError(
            f"{repo.full} has no answerable discussion category. Enable Discussions and add a Q&A category."
        )

    def create_discussion(self, repository_id: str, category_id: str, title: str, body: str) -> dict:
        data = self.graphql(
            self._M_CREATE_DISCUSSION,
            {"repositoryId": repository_id, "categoryId": category_id, "title": title, "body": body},
        )
        return data["createDiscussion"]["discussion"]

    def add_discussion_comment(self, discussion_id: str, body: str) -> str:
        data = self.graphql(self._M_ADD_COMMENT, {"discussionId": discussion_id, "body": body})
        return data["addDiscussionComment"]["comment"]["id"]

    def mark_comment_as_answer(self, comment_id: str) -> None:
        self.graphql(self._M_MARK_ANSWER, {"id": comment_id})
