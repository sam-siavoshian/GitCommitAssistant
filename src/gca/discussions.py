"""Discussions flow - Galaxy Brain best-effort.

Note: as of 2024 GitHub adjusted Galaxy Brain to factor in upvotes from other users.
This module performs the underlying mechanics correctly (create Q&A discussion, add
a comment, mark it as the accepted answer) but the badge may not award without
external engagement. The README spells this out.
"""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass, field

from gca.github_api import DiscussionCategoryError, GitHubClient
from gca.repo_spec import RepoSpec

log = logging.getLogger("gca.discussions")

QUESTION_BANK = [
    ("How do I structure a small CLI in Python?", "I want subcommands, env-based config, and tests. What does a clean layout look like?"),
    ("What's the best way to handle GitHub rate limits?", "Looking for retry/backoff patterns and how to read the X-RateLimit-Reset header."),
    ("Idiomatic dependency injection without a framework?", "Looking for patterns that stay testable as the project grows."),
    ("How should I version a Python CLI distributed via pipx?", "Calver vs semver, and where to source the version string."),
    ("Best logging setup for a CLI?", "Want sensible defaults, --verbose, and color when TTY is detected."),
]

ANSWER_BANK = [
    "Use Typer for the surface, a dataclass for options, and a thin module per subcommand. Resolve config with: arg > env > keychain > prompt.",
    "Honor X-RateLimit-Reset on 429 and X-RateLimit-Remaining==0 on 403. Exponential backoff (1s/2s/4s) on 5xx, never retry hard 4xx.",
    "Pass dependencies through constructors. Build a small assemble() function at the entrypoint that wires them once. No framework required.",
    "Single source of truth in pyproject.toml; expose __version__ via importlib.metadata.version('your-pkg').",
    "stdlib logging with a RichHandler if stderr is a TTY, plain formatter otherwise. --verbose flips DEBUG.",
]


@dataclass
class DiscussionOptions:
    repos: list[RepoSpec]
    count: int
    dry_run: bool = False


@dataclass
class DiscussionSummary:
    repo: str
    created: int = 0
    answered: int = 0
    errors: list[str] = field(default_factory=list)


def run(client: GitHubClient, opts: DiscussionOptions) -> list[DiscussionSummary]:
    if opts.count < 1:
        raise ValueError("count must be >= 1")

    summaries: list[DiscussionSummary] = []
    for spec in opts.repos:
        summary = DiscussionSummary(repo=spec.full)
        try:
            if opts.dry_run:
                summary.created = opts.count
                summary.answered = opts.count
                summaries.append(summary)
                continue
            repo = client.get_repo(spec.owner, spec.name)
            try:
                repo_id, cat_id, cat_name = client.find_repo_and_qa_category(repo)
            except DiscussionCategoryError as e:
                summary.errors.append(str(e))
                summaries.append(summary)
                continue
            log.info("using discussion category %r (id=%s) on %s", cat_name, cat_id, spec.full)

            for i in range(opts.count):
                title, body = random.choice(QUESTION_BANK)
                title = f"{title} (#{i+1})"
                try:
                    discussion = client.create_discussion(repo_id, cat_id, title, body)
                    summary.created += 1
                    comment_id = client.add_discussion_comment(discussion["id"], random.choice(ANSWER_BANK))
                    client.mark_comment_as_answer(comment_id)
                    summary.answered += 1
                except Exception as e:
                    summary.errors.append(f"discussion {i+1}: {type(e).__name__}: {e}")
        except Exception as e:
            summary.errors.append(f"setup: {type(e).__name__}: {e}")
        summaries.append(summary)
    return summaries
