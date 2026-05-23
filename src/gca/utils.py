"""Shared helpers: date parsing, data-file loaders, repo-name validation."""

from __future__ import annotations

import datetime as dt
import re
from importlib import resources
from pathlib import Path

REPO_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.\-]{0,99}$")
EMAIL_RE = re.compile(r"^[^\s<>@]+@[^\s<>@]+\.[^\s<>@]+$")
COAUTHOR_RE = re.compile(r"^(?P<name>[^<]+?)\s*<(?P<email>[^<>@\s]+@[^<>@\s]+)>$")


def git_date_string(when: dt.datetime) -> str:
    """Return the git-internal date string '<unix-ts> +HHMM'.

    Always pins to UTC if `when` is naive, so callers get reproducible output.
    """
    if when.tzinfo is None:
        when = when.replace(tzinfo=dt.timezone.utc)
    epoch = int(when.timestamp())
    offset = when.utcoffset() or dt.timedelta(0)
    total_minutes = int(offset.total_seconds() // 60)
    sign = "+" if total_minutes >= 0 else "-"
    total_minutes = abs(total_minutes)
    return f"{epoch} {sign}{total_minutes // 60:02d}{total_minutes % 60:02d}"


DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def parse_date(value: str) -> dt.date:
    """Parse YYYY-MM-DD strictly (zero-padded)."""
    if not DATE_RE.match(value):
        raise ValueError(f"date must be YYYY-MM-DD, got {value!r}")
    return dt.datetime.strptime(value, "%Y-%m-%d").date()


def safe_repo_name(name: str) -> str:
    """Reject path-traversal / shell-active / multi-segment names.

    Returns the name unchanged if valid; raises `ValueError` otherwise.
    """
    if not name or not REPO_NAME_RE.match(name):
        raise ValueError(f"invalid repo name: {name!r}")
    if ".." in name:
        raise ValueError(f"invalid repo name: {name!r}")
    return name


def parse_coauthor(value: str) -> tuple[str, str]:
    """Parse 'Name <email>' into (name, email). Raises ValueError on bad format."""
    m = COAUTHOR_RE.match(value.strip())
    if not m:
        raise ValueError(f"coauthor must be 'Name <email>', got: {value!r}")
    name = m.group("name").strip()
    email = m.group("email").strip()
    if not EMAIL_RE.match(email):
        raise ValueError(f"coauthor email malformed: {email!r}")
    return name, email


def _data_path(name: str) -> Path:
    """Resolve a packaged data file."""
    pkg_local = Path(__file__).resolve().parent / "data" / name
    if pkg_local.exists():
        return pkg_local
    with resources.as_file(resources.files("gca").joinpath("data", name)) as p:
        return p


def load_commit_messages() -> list[str]:
    path = _data_path("commit_messages.txt")
    return [ln.strip() for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]


def load_default_repo_names() -> list[str]:
    path = _data_path("repo_names.txt")
    return [ln.strip() for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
