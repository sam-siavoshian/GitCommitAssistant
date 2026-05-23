"""End-to-end git_ops tests using real `git` against tmp_path. No network."""

import datetime as dt
import subprocess
from pathlib import Path

import pytest

from gca import git_ops


def _git(cwd: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(cwd), *args], text=True).strip()


def test_backdated_commit_lands_exact_iso_date(git_repo: Path):
    when = dt.datetime(2022, 3, 15, 14, 30, 0, tzinfo=dt.timezone.utc)
    sha = git_ops.backdated_commit(
        git_repo,
        file_name="note.md",
        file_content="hi",
        message="Add note",
        when=when,
    )
    assert len(sha) == 40
    iso = _git(git_repo, "log", "-1", "--format=%aI")
    assert iso.startswith("2022-03-15T14:30:00")
    # committer date too
    ciso = _git(git_repo, "log", "-1", "--format=%cI")
    assert ciso.startswith("2022-03-15T14:30:00")


def test_backdated_commit_with_coauthors_trailer(git_repo: Path):
    when = dt.datetime(2024, 1, 1, 12, 0, 0, tzinfo=dt.timezone.utc)
    git_ops.backdated_commit(
        git_repo,
        file_name="x.txt",
        file_content="x",
        message="feat: thing",
        when=when,
        coauthors=["Ada Lovelace <ada@example.org>", "Grace Hopper <grace@example.org>"],
    )
    body = _git(git_repo, "log", "-1", "--format=%B")
    assert "Co-authored-by: Ada Lovelace <ada@example.org>" in body
    assert "Co-authored-by: Grace Hopper <grace@example.org>" in body
    # `git interpret-trailers` will only parse trailers when they are correctly formatted
    trailers = subprocess.check_output(
        ["git", "-C", str(git_repo), "log", "-1", "--format=%(trailers:key=Co-authored-by)"],
        text=True,
    )
    assert "Ada Lovelace" in trailers
    assert "Grace Hopper" in trailers


def test_ensure_branch_creates_and_reuses(git_repo: Path):
    # need a commit first so checkout works
    when = dt.datetime(2024, 1, 1, tzinfo=dt.timezone.utc)
    git_ops.backdated_commit(
        git_repo, file_name="a", file_content="a", message="init", when=when
    )
    git_ops.ensure_branch(git_repo, "feature/foo", base="main")
    git_ops.backdated_commit(
        git_repo, file_name="b", file_content="b", message="feat", when=when
    )
    # branch must exist locally
    branches = _git(git_repo, "branch", "--list")
    assert "feature/foo" in branches
    # reusing the same branch should not throw
    git_ops.checkout(git_repo, "main")
    git_ops.ensure_branch(git_repo, "feature/foo", base="main")


def test_temp_workdir_cleans_up_on_exception():
    captured: list[Path] = []
    try:
        with git_ops.temp_workdir("gca-test-") as p:
            captured.append(p)
            assert p.exists()
            raise RuntimeError("boom")
    except RuntimeError:
        pass
    assert captured
    assert not captured[0].exists()


def test_clone_wipes_existing_dest(tmp_path):
    # build a tiny source repo
    src = tmp_path / "src"
    subprocess.run(["git", "init", "-q", "-b", "main", str(src)], check=True)
    subprocess.run(["git", "-C", str(src), "config", "user.email", "x@x"], check=True)
    subprocess.run(["git", "-C", str(src), "config", "user.name", "x"], check=True)
    (src / "f").write_text("v1")
    subprocess.run(["git", "-C", str(src), "add", "f"], check=True)
    subprocess.run(["git", "-C", str(src), "commit", "-q", "-m", "init"], check=True)

    dest = tmp_path / "dest"
    git_ops.clone(str(src), dest)
    assert (dest / "f").read_text() == "v1"
    # mess with the dest, re-clone, the mess should be gone
    (dest / "junk").write_text("garbage")
    git_ops.clone(str(src), dest)
    assert not (dest / "junk").exists()


def test_run_git_raises_on_bad_cmd(git_repo: Path):
    with pytest.raises(git_ops.GitError):
        git_ops.run_git(["this-is-not-a-real-subcommand"], cwd=git_repo, capture=True)
