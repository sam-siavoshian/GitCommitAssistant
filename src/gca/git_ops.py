"""Git operations: subprocess calls, default-branch detection, backdated commits.

All commands use list form (no `shell=True`). Author and committer dates use the
git-internal '<unix-ts> +HHMM' format which is the only fully unambiguous one.
"""

from __future__ import annotations

import datetime as dt
import logging
import os
import shutil
import subprocess
import tempfile
from collections.abc import Iterable
from contextlib import contextmanager
from pathlib import Path

from gca.utils import git_date_string, parse_coauthor

log = logging.getLogger("gca.git_ops")


class GitError(RuntimeError):
    pass


def run_git(args: list[str], *, cwd: str | os.PathLike, env: dict | None = None, capture: bool = False) -> str:
    """Run `git <args>` in cwd. Raises GitError on non-zero exit."""
    cmd = ["git", *args]
    full_env = os.environ.copy()
    if env:
        full_env.update(env)
    try:
        out = subprocess.run(
            cmd,
            cwd=str(cwd),
            env=full_env,
            check=True,
            stdout=subprocess.PIPE if capture else subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        stderr = (e.stderr or "").strip()
        raise GitError(f"git {' '.join(args)} failed: {stderr}") from e
    return out.stdout if capture else ""


def clone(url: str, dest: str | os.PathLike) -> Path:
    """Clone url into dest. If dest exists, wipe and re-clone."""
    dest_p = Path(dest)
    if dest_p.exists():
        shutil.rmtree(dest_p)
    dest_p.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "clone", "--quiet", url, str(dest_p)],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    return dest_p


def detect_default_branch(repo_dir: str | os.PathLike) -> str:
    """Return the remote default branch name. Tries symbolic-ref, then a remote-show fallback."""
    try:
        out = run_git(
            ["symbolic-ref", "--short", "refs/remotes/origin/HEAD"],
            cwd=repo_dir,
            capture=True,
        ).strip()
        if out and "/" in out:
            return out.split("/", 1)[1]
        if out:
            return out
    except GitError:
        pass
    try:
        out = run_git(["remote", "show", "origin"], cwd=repo_dir, capture=True)
        for line in out.splitlines():
            line = line.strip()
            if line.startswith("HEAD branch:"):
                return line.split(":", 1)[1].strip()
    except GitError:
        pass
    # last-resort: whatever local branch we are on
    try:
        return run_git(["branch", "--show-current"], cwd=repo_dir, capture=True).strip() or "main"
    except GitError:
        return "main"


def ensure_branch(repo_dir: str | os.PathLike, branch: str, *, base: str | None = None) -> None:
    """Create+checkout `branch` from `base` if it doesn't exist; otherwise checkout."""
    try:
        run_git(["rev-parse", "--verify", f"refs/heads/{branch}"], cwd=repo_dir, capture=True)
        run_git(["checkout", branch], cwd=repo_dir)
    except GitError:
        if base:
            run_git(["checkout", base], cwd=repo_dir)
        run_git(["checkout", "-b", branch], cwd=repo_dir)


def checkout(repo_dir: str | os.PathLike, ref: str) -> None:
    run_git(["checkout", ref], cwd=repo_dir)


def configure_identity(repo_dir: str | os.PathLike, name: str, email: str) -> None:
    """Set local user.name/user.email so commits in this repo use the supplied identity."""
    run_git(["config", "user.name", name], cwd=repo_dir)
    run_git(["config", "user.email", email], cwd=repo_dir)


def build_commit_message(subject: str, body: str = "", coauthors: Iterable[str] = ()) -> str:
    """Standard git commit format: subject, blank, body, blank, trailer block."""
    parts: list[str] = [subject.strip()]
    if body:
        parts.append("")
        parts.append(body.strip())
    trailers = []
    for raw in coauthors:
        name, email = parse_coauthor(raw)
        trailers.append(f"Co-authored-by: {name} <{email}>")
    if trailers:
        parts.append("")
        parts.extend(trailers)
    return "\n".join(parts) + "\n"


def backdated_commit(
    repo_dir: str | os.PathLike,
    *,
    file_name: str,
    file_content: str,
    message: str,
    when: dt.datetime,
    coauthors: Iterable[str] = (),
    body: str = "",
) -> str:
    """Write file_name into repo_dir, stage, commit with backdated env vars.

    Returns the resulting commit SHA.
    """
    repo_p = Path(repo_dir)
    f = repo_p / file_name
    f.write_text(file_content, encoding="utf-8")
    run_git(["add", "--", file_name], cwd=repo_dir)

    full_msg = build_commit_message(message, body=body, coauthors=coauthors)
    date_str = git_date_string(when)
    env = {"GIT_AUTHOR_DATE": date_str, "GIT_COMMITTER_DATE": date_str}
    run_git(["commit", "-m", full_msg], cwd=repo_dir, env=env)
    sha = run_git(["rev-parse", "HEAD"], cwd=repo_dir, capture=True).strip()
    return sha


def push(repo_dir: str | os.PathLike, ref: str, *, set_upstream: bool = False) -> None:
    args = ["push"]
    if set_upstream:
        args.extend(["-u", "origin", ref])
    else:
        args.extend(["origin", ref])
    run_git(args, cwd=repo_dir)


@contextmanager
def temp_workdir(prefix: str = "gca-"):
    """Create+cd into a tempdir that is always torn down on exit."""
    base = Path(tempfile.mkdtemp(prefix=prefix))
    try:
        yield base
    finally:
        shutil.rmtree(base, ignore_errors=True)
