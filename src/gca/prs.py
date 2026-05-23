"""Pull-request generation. Pull Shark + YOLO mechanics."""

from __future__ import annotations

import datetime as dt
import logging
import random
import uuid
from dataclasses import dataclass

from gca import git_ops
from gca.github_api import GitHubClient, MergeBlockedError, PRExistsError
from gca.repo_spec import RepoSpec
from gca.utils import load_commit_messages

log = logging.getLogger("gca.prs")


@dataclass
class PROptions:
    repos: list[RepoSpec]
    count: int
    start: dt.date
    end: dt.date
    merge_method: str = "squash"
    coauthors: list[str] | None = None
    dry_run: bool = False


@dataclass
class PRSummary:
    repo: str
    created: int
    merged: int
    errors: list[str]


def _pr_dates(start: dt.date, end: dt.date, count: int) -> list[dt.date]:
    """Spread `count` dates evenly between start..end inclusive."""
    if start > end:
        raise ValueError("start must be <= end")
    total = (end - start).days
    if total == 0:
        return [start] * count
    if count == 1:
        return [start + dt.timedelta(days=total // 2)]
    return [start + dt.timedelta(days=round(i * total / (count - 1))) for i in range(count)]


def run(client: GitHubClient, opts: PROptions) -> list[PRSummary]:
    if opts.count < 1:
        raise ValueError("count must be >= 1")
    messages = load_commit_messages()
    summaries: list[PRSummary] = []
    username = client.whoami() if not opts.dry_run else "dry-run-user"

    for spec in opts.repos:
        summary = PRSummary(repo=spec.full, created=0, merged=0, errors=[])
        try:
            if opts.dry_run:
                summary.created = opts.count
                summary.merged = opts.count
                summaries.append(summary)
                continue
            repo = client.get_repo(spec.owner, spec.name)
            with git_ops.temp_workdir(prefix=f"gca-prs-{spec.name}-") as base:
                repo_dir = git_ops.clone(spec.auth_clone_url(client.token), base / spec.name)
                default_branch = git_ops.detect_default_branch(repo_dir)

                dates = _pr_dates(opts.start, opts.end, opts.count)
                for i, when_date in enumerate(dates, start=1):
                    pr_msg = random.choice(messages)
                    slug = uuid.uuid4().hex[:8]
                    branch = f"gca/pr-{when_date.isoformat()}-{slug}"
                    try:
                        git_ops.checkout(repo_dir, default_branch)
                        git_ops.ensure_branch(repo_dir, branch, base=default_branch)
                        for k in range(random.randint(1, 3)):
                            when = dt.datetime.combine(
                                when_date,
                                dt.time(hour=10 + k, minute=random.randint(0, 59)),
                                tzinfo=dt.timezone.utc,
                            )
                            git_ops.backdated_commit(
                                repo_dir,
                                file_name=f".gca/prs/{when_date.isoformat()}-{slug}-{k+1}.md",
                                file_content=f"# {pr_msg}\n\nPR slot {i}, commit {k+1}\n",
                                message=f"{pr_msg} (part {k+1})",
                                when=when,
                                coauthors=opts.coauthors or (),
                            )
                        git_ops.push(repo_dir, branch, set_upstream=True)
                        try:
                            number = client.create_pull_request(
                                repo,
                                head=branch,
                                title=f"{pr_msg} ({when_date.isoformat()})",
                                body=f"Automated PR backdated to {when_date.isoformat()}.",
                            )
                        except PRExistsError as e:
                            summary.errors.append(f"PR {i}: already exists ({e})")
                            continue
                        summary.created += 1
                        try:
                            client.merge_pull_request(repo, number, method=opts.merge_method)
                            summary.merged += 1
                        except MergeBlockedError as e:
                            # try fallback to merge commit if user picked squash and squash is blocked
                            if opts.merge_method != "merge":
                                try:
                                    client.merge_pull_request(repo, number, method="merge")
                                    summary.merged += 1
                                except MergeBlockedError as e2:
                                    summary.errors.append(f"PR #{number}: merge blocked: {e2}")
                            else:
                                summary.errors.append(f"PR #{number}: merge blocked: {e}")
                    except Exception as e:
                        summary.errors.append(f"PR {i}: {type(e).__name__}: {e}")
                        log.exception("PR loop failed")
        except Exception as e:
            summary.errors.append(f"setup: {type(e).__name__}: {e}")
            log.exception("PR run failed for %s", spec.full)
        summaries.append(summary)
        _ = username
    return summaries
