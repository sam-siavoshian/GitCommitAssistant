"""Token + settings resolution.

Order: explicit arg > GCA_GITHUB_TOKEN env > .env in CWD > keyring > interactive prompt.
Tokens are never written to disk by default; keychain storage is opt-in.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

try:
    import keyring  # type: ignore
except Exception:  # pragma: no cover - optional surface
    keyring = None  # type: ignore

KEYRING_SERVICE = "gca"
KEYRING_USER = "github"
TOKEN_ENV = "GCA_GITHUB_TOKEN"
API_ENV = "GCA_GITHUB_API"
DEFAULT_API = "https://api.github.com"

CLASSIC_PAT_RE = re.compile(r"^ghp_[A-Za-z0-9]{36,}$")
FINE_PAT_RE = re.compile(r"^github_pat_[A-Za-z0-9_]{40,}$")
OAUTH_RE = re.compile(r"^gho_[A-Za-z0-9]{36,}$")
APP_RE = re.compile(r"^(ghs_|ghu_)[A-Za-z0-9]{36,}$")


def looks_like_token(value: str) -> bool:
    return any(p.match(value) for p in (CLASSIC_PAT_RE, FINE_PAT_RE, OAUTH_RE, APP_RE))


def _load_dotenv() -> None:
    """Hydrate os.environ from a .env file in CWD, without overwriting existing vars."""
    p = Path.cwd() / ".env"
    if not p.exists():
        return
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        if k and k not in os.environ:
            os.environ[k] = v


def resolve_token(explicit: str | None = None, *, allow_prompt: bool = True) -> str:
    """Return a GitHub token, searching every supported source in order.

    Raises RuntimeError if no token could be resolved and prompting is disabled.
    """
    if explicit:
        return explicit.strip()

    _load_dotenv()
    if v := os.environ.get(TOKEN_ENV):
        return v.strip()

    if keyring is not None:
        try:
            v = keyring.get_password(KEYRING_SERVICE, KEYRING_USER)
            if v:
                return v.strip()
        except Exception:
            pass

    if not allow_prompt:
        raise RuntimeError(
            f"no GitHub token found. Set {TOKEN_ENV}, run `gca init`, or pass --token."
        )

    import typer

    token = typer.prompt(
        "GitHub personal access token (input hidden)",
        hide_input=True,
    ).strip()
    if not token:
        raise RuntimeError("empty token")
    if typer.confirm("Save this token to your OS keychain for next time?", default=False):
        save_token_to_keyring(token)
    return token


def save_token_to_keyring(token: str) -> None:
    if keyring is None:
        raise RuntimeError("keyring backend unavailable on this system")
    keyring.set_password(KEYRING_SERVICE, KEYRING_USER, token)


def delete_token_from_keyring() -> None:
    if keyring is None:
        return
    import contextlib

    with contextlib.suppress(Exception):
        keyring.delete_password(KEYRING_SERVICE, KEYRING_USER)


def api_base() -> str:
    return os.environ.get(API_ENV, DEFAULT_API).rstrip("/")
