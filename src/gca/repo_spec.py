"""Parsing GitHub URLs / shorthand into (owner, name, clone_url)."""

from __future__ import annotations

import re
from dataclasses import dataclass

GITHUB_HTTPS = re.compile(r"^https?://github\.com/([^/\s]+)/([^/\s]+?)(?:\.git)?/?$")
GITHUB_SSH = re.compile(r"^git@github\.com:([^/\s]+)/([^/\s]+?)(?:\.git)?$")
SHORTHAND = re.compile(r"^([A-Za-z0-9][A-Za-z0-9_.\-]*)/([A-Za-z0-9][A-Za-z0-9_.\-]*)$")


@dataclass(frozen=True)
class RepoSpec:
    owner: str
    name: str

    @property
    def full(self) -> str:
        return f"{self.owner}/{self.name}"

    @property
    def https_url(self) -> str:
        return f"https://github.com/{self.full}.git"

    def auth_clone_url(self, token: str) -> str:
        return f"https://x-access-token:{token}@github.com/{self.full}.git"


def parse_repo(value: str) -> RepoSpec:
    """Accept https URL, ssh URL, or 'owner/name' shorthand."""
    v = value.strip()
    if m := GITHUB_HTTPS.match(v):
        return RepoSpec(m.group(1), m.group(2))
    if m := GITHUB_SSH.match(v):
        return RepoSpec(m.group(1), m.group(2))
    if m := SHORTHAND.match(v):
        return RepoSpec(m.group(1), m.group(2))
    raise ValueError(
        f"can't parse {value!r} as a GitHub repo. Use 'owner/name' or 'https://github.com/owner/name'."
    )
