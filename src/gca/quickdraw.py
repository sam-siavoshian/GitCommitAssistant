"""Quickdraw - open an issue, close it within 5 minutes. Pure REST."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field

from gca.github_api import GitHubClient
from gca.repo_spec import RepoSpec

log = logging.getLogger("gca.quickdraw")

ISSUE_TITLES = [
    "Tracking: chore - housekeeping",
    "Note: refresh dependencies next sprint",
    "Spike: explore upgrading CI image",
    "Doc: clarify install steps for new contributors",
    "Idea: surface CLI flags in README",
]


@dataclass
class QuickdrawOptions:
    repos: list[RepoSpec]
    count: int
    pause_seconds: float = 1.0
    dry_run: bool = False


@dataclass
class QuickdrawSummary:
    repo: str
    opened: int = 0
    closed: int = 0
    errors: list[str] = field(default_factory=list)


def run(client: GitHubClient, opts: QuickdrawOptions) -> list[QuickdrawSummary]:
    if opts.count < 1:
        raise ValueError("count must be >= 1")
    if opts.pause_seconds < 0 or opts.pause_seconds > 280:
        raise ValueError("pause_seconds must be in [0, 280]; Quickdraw requires <5 min total")

    summaries: list[QuickdrawSummary] = []
    for spec in opts.repos:
        summary = QuickdrawSummary(repo=spec.full)
        try:
            if opts.dry_run:
                summary.opened = opts.count
                summary.closed = opts.count
                summaries.append(summary)
                continue
            repo = client.get_repo(spec.owner, spec.name)
            for i in range(opts.count):
                title = f"{ISSUE_TITLES[i % len(ISSUE_TITLES)]} (#{i+1})"
                try:
                    number = client.create_issue(repo, title=title, body="opened by gca quickdraw")
                    summary.opened += 1
                    if opts.pause_seconds:
                        time.sleep(opts.pause_seconds)
                    client.close_issue(repo, number)
                    summary.closed += 1
                except Exception as e:
                    summary.errors.append(f"quickdraw {i+1}: {type(e).__name__}: {e}")
        except Exception as e:
            summary.errors.append(f"setup: {type(e).__name__}: {e}")
        summaries.append(summary)
    return summaries
