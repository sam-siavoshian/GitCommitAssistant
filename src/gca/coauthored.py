"""Coauthored PR flow. Mechanics are correct; the Pair Extraordinaire badge itself
was frozen by GitHub in March 2024 and is no longer awarded to new earners.

We still write proper `Co-authored-by:` trailers because they are genuinely useful
for attribution, regardless of badge status.
"""

from __future__ import annotations

import logging

from gca import prs
from gca.github_api import GitHubClient
from gca.utils import parse_coauthor

log = logging.getLogger("gca.coauthored")


def validate_coauthors(client: GitHubClient, coauthors: list[str]) -> list[str]:
    """Normalize coauthors, reject ones equal to the actor's primary verified email.

    Returns the cleaned list. Raises ValueError on hard rejections.
    """
    if not coauthors:
        raise ValueError("at least one coauthor required")
    actor_email = client.primary_verified_email()
    cleaned: list[str] = []
    for raw in coauthors:
        name, email = parse_coauthor(raw)
        if actor_email and email.lower() == actor_email.lower():
            raise ValueError(
                f"coauthor email {email!r} matches your own primary email. "
                "Pair Extraordinaire (when it awarded) required a different account; pick another email."
            )
        cleaned.append(f"{name} <{email}>")
    return cleaned


def run(client: GitHubClient, opts: prs.PROptions) -> list[prs.PRSummary]:
    """Same flow as `prs.run` but enforces coauthor presence + emits a warning banner."""
    if not opts.coauthors:
        raise ValueError("coauthored requires --coauthor 'Name <email>' (repeatable)")
    if not opts.dry_run:
        opts = prs.PROptions(
            repos=opts.repos,
            count=opts.count,
            start=opts.start,
            end=opts.end,
            merge_method=opts.merge_method,
            coauthors=validate_coauthors(client, opts.coauthors),
            dry_run=opts.dry_run,
        )
    log.warning(
        "GitHub froze the Pair Extraordinaire badge in March 2024. "
        "These commits still get correct Co-authored-by trailers, "
        "but the achievement itself no longer awards to new earners."
    )
    return prs.run(client, opts)
