"""Commit-generation flow. Walks a date range, drops backdated commits, pushes."""

from __future__ import annotations

import datetime as dt
import logging
import random
from dataclasses import dataclass

from gca import git_ops
from gca.github_api import GitHubClient
from gca.repo_spec import RepoSpec
from gca.utils import load_commit_messages

log = logging.getLogger("gca.commits")


@dataclass
class CommitOptions:
    repos: list[RepoSpec]
    start: dt.date
    end: dt.date
    strategy: str = "every-day"  # every-day | random | weekdays | weekends
    per_day_min: int = 1
    per_day_max: int = 1
    messages: list[str] | None = None
    dry_run: bool = False


@dataclass
class CommitSummary:
    repo: str
    commits_made: int
    pushed: bool
    error: str | None = None


def _should_commit_on(date: dt.date, strategy: str) -> bool:
    if strategy == "every-day":
        return True
    if strategy == "weekdays":
        return date.weekday() < 5
    if strategy == "weekends":
        return date.weekday() >= 5
    if strategy == "random":
        return random.random() < 0.7
    raise ValueError(f"unknown strategy: {strategy!r}")


def _per_day(opts: CommitOptions) -> int:
    if opts.per_day_min == opts.per_day_max:
        return opts.per_day_min
    return random.randint(opts.per_day_min, opts.per_day_max)


def run(client: GitHubClient, opts: CommitOptions) -> list[CommitSummary]:
    if opts.start > opts.end:
        raise ValueError("start date must be <= end date")
    if opts.per_day_min < 1 or opts.per_day_max < opts.per_day_min:
        raise ValueError("invalid per-day commit range")
    if opts.strategy not in {"every-day", "random", "weekdays", "weekends"}:
        raise ValueError(f"unknown strategy: {opts.strategy!r}")

    messages = opts.messages or load_commit_messages()
    summaries: list[CommitSummary] = []

    username = client.whoami() if not opts.dry_run else "dry-run-user"

    for spec in opts.repos:
        summary = CommitSummary(repo=spec.full, commits_made=0, pushed=False)
        try:
            with git_ops.temp_workdir(prefix=f"gca-commits-{spec.name}-") as base:
                if opts.dry_run:
                    log.info("[dry-run] would clone %s", spec.full)
                    summary.pushed = False
                else:
                    repo_dir = git_ops.clone(spec.auth_clone_url(client.token), base / spec.name)
                    default_branch = git_ops.detect_default_branch(repo_dir)
                    git_ops.checkout(repo_dir, default_branch)

                cursor = opts.start
                idx = 0
                while cursor <= opts.end:
                    if _should_commit_on(cursor, opts.strategy):
                        for _ in range(_per_day(opts)):
                            idx += 1
                            msg = random.choice(messages)
                            file_name = f".gca/log/{cursor.isoformat()}-{idx}.md"
                            when = dt.datetime.combine(
                                cursor,
                                dt.time(
                                    hour=random.randint(9, 17),
                                    minute=random.randint(0, 59),
                                    second=random.randint(0, 59),
                                ),
                                tzinfo=dt.timezone.utc,
                            )
                            content = (
                                f"# {msg}\n\nDate: {cursor.isoformat()}\nCommit #{idx}\n"
                            )
                            if opts.dry_run:
                                summary.commits_made += 1
                            else:
                                # ensure parent dir exists
                                (repo_dir / ".gca" / "log").mkdir(parents=True, exist_ok=True)
                                git_ops.backdated_commit(
                                    repo_dir,
                                    file_name=file_name,
                                    file_content=content,
                                    message=msg,
                                    when=when,
                                )
                                summary.commits_made += 1
                    cursor += dt.timedelta(days=1)

                if not opts.dry_run and summary.commits_made > 0:
                    git_ops.push(repo_dir, default_branch)
                    summary.pushed = True
        except Exception as e:
            summary.error = f"{type(e).__name__}: {e}"
            log.error("commits failed for %s: %s", spec.full, e)
        summaries.append(summary)
        _ = username  # silence linter when dry-run
    return summaries
