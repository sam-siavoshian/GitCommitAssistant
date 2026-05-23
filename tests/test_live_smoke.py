"""Live smoke test, gated by GCA_LIVE=1 + a valid GCA_GITHUB_TOKEN.

Creates a throwaway public repo `gca-smoke-<timestamp>`, exercises every
feature, deletes the repo. On any failure inside the body the repo URL is
printed so the user can clean up manually.
"""

from __future__ import annotations

import datetime as dt
import os
import time

import pytest

from gca import commits, discussions, prs, quickdraw
from gca.config import looks_like_token
from gca.github_api import GitHubClient
from gca.repo_spec import RepoSpec

LIVE = os.environ.get("GCA_LIVE") == "1"
TOKEN = os.environ.get("GCA_GITHUB_TOKEN", "")

pytestmark = pytest.mark.live


@pytest.fixture(autouse=True)
def _restore_env(monkeypatch):
    """The outer conftest scrubs GCA_GITHUB_TOKEN. Restore it for live tests."""
    if TOKEN:
        monkeypatch.setenv("GCA_GITHUB_TOKEN", TOKEN)
    yield


@pytest.mark.skipif(not LIVE or not TOKEN, reason="set GCA_LIVE=1 and GCA_GITHUB_TOKEN to run")
def test_live_smoke():
    assert looks_like_token(TOKEN), "GCA_GITHUB_TOKEN doesn't look like a token"
    client = GitHubClient(TOKEN)
    login = client.whoami()
    scopes = client.scopes()
    print(f"\n[live] authenticated as {login}, scopes={sorted(scopes)}")

    stamp = int(time.time())
    name = f"gca-smoke-{stamp}"
    repo = client.create_repo(name, private=False, description="gca live smoke test - safe to delete")
    spec = RepoSpec(repo.owner, repo.name)
    url = f"https://github.com/{repo.full}"
    print(f"[live] created repo: {url}")

    failed = False
    try:
        # commits
        c_summaries = commits.run(
            client,
            commits.CommitOptions(
                repos=[spec],
                start=dt.date.today() - dt.timedelta(days=3),
                end=dt.date.today(),
                strategy="every-day",
                per_day_min=2,
                per_day_max=2,
            ),
        )
        print(f"[live] commits: {c_summaries[0]}")
        assert c_summaries[0].commits_made == 8 and c_summaries[0].pushed

        # quickdraw - opens + closes 1 issue
        q = quickdraw.run(
            client,
            quickdraw.QuickdrawOptions(repos=[spec], count=1, pause_seconds=1.0),
        )
        print(f"[live] quickdraw: {q[0]}")
        assert q[0].opened == 1 and q[0].closed == 1

        # one real PR (Pull Shark mechanics)
        p = prs.run(
            client,
            prs.PROptions(
                repos=[spec],
                count=1,
                start=dt.date.today() - dt.timedelta(days=2),
                end=dt.date.today(),
                merge_method="squash",
            ),
        )
        print(f"[live] pr: {p[0]}")
        assert p[0].created == 1 and p[0].merged == 1

        # discussions are off by default on new repos via API; this call should
        # surface a clear category error rather than crash.
        d = discussions.run(
            client,
            discussions.DiscussionOptions(repos=[spec], count=1),
        )
        print(f"[live] discussions: {d[0]}")
        assert d[0].errors or d[0].answered == 1
    except Exception:
        failed = True
        print(f"[live] FAILED, leaving repo for inspection: {url}")
        raise
    finally:
        if not failed and "delete_repo" in client.scopes():
            client.delete_repo(repo.owner, repo.name)
            print(f"[live] deleted repo {repo.full}")
        elif not failed:
            print(f"[live] token lacks delete_repo scope; leaving {url} for manual cleanup")
