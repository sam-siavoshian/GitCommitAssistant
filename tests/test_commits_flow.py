"""Integration test: commits.run against a local bare remote (no network)."""

import datetime as dt
import subprocess
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from gca import commits
from gca.repo_spec import RepoSpec


def _make_remote_with_seed(tmp_path: Path) -> Path:
    remote = tmp_path / "remote.git"
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(remote)], check=True)
    seed = tmp_path / "seed"
    subprocess.run(["git", "init", "-q", "-b", "main", str(seed)], check=True)
    subprocess.run(["git", "-C", str(seed), "config", "user.email", "x@x"], check=True)
    subprocess.run(["git", "-C", str(seed), "config", "user.name", "x"], check=True)
    (seed / "README.md").write_text("hello")
    subprocess.run(["git", "-C", str(seed), "add", "README.md"], check=True)
    subprocess.run(["git", "-C", str(seed), "commit", "-q", "-m", "init"], check=True)
    subprocess.run(
        ["git", "-C", str(seed), "remote", "add", "origin", str(remote)], check=True
    )
    subprocess.run(["git", "-C", str(seed), "push", "-q", "-u", "origin", "main"], check=True)
    return remote


def test_commits_run_against_local_remote(tmp_path: Path, monkeypatch):
    remote = _make_remote_with_seed(tmp_path)

    # build a fake RepoSpec whose auth_clone_url returns the local path
    class LocalSpec(RepoSpec):
        def auth_clone_url(self, token: str) -> str:  # type: ignore[override]
            return str(remote)

    spec = LocalSpec("local", "remote")
    client = MagicMock()
    client.token = "ghp_fake"
    client.whoami.return_value = "octocat"

    opts = commits.CommitOptions(
        repos=[spec],
        start=dt.date(2024, 1, 1),
        end=dt.date(2024, 1, 3),
        strategy="every-day",
        per_day_min=2,
        per_day_max=2,
    )
    summaries = commits.run(client, opts)
    s = summaries[0]
    assert s.error is None, s.error
    assert s.commits_made == 6
    assert s.pushed is True

    # verify commits actually landed on origin/main with backdated dates
    clone = tmp_path / "verify"
    subprocess.run(["git", "clone", "-q", str(remote), str(clone)], check=True)
    log = subprocess.check_output(
        ["git", "-C", str(clone), "log", "--format=%aI", "main"], text=True
    ).strip().splitlines()
    # the 6 backdated + 1 seed = 7 commits
    assert len(log) == 7
    dates = sorted({ln[:10] for ln in log if ln})
    # at least one commit per requested day
    for d in ("2024-01-01", "2024-01-02", "2024-01-03"):
        assert d in dates


def test_commits_dry_run_emits_no_network():
    spec = RepoSpec("octo", "x")
    client = MagicMock()
    client.token = "tok"
    client.whoami.return_value = "octocat"

    opts = commits.CommitOptions(
        repos=[spec],
        start=dt.date(2024, 1, 1),
        end=dt.date(2024, 1, 1),
        strategy="every-day",
        per_day_min=3,
        per_day_max=3,
        dry_run=True,
    )
    summaries = commits.run(client, opts)
    assert summaries[0].commits_made == 3
    assert summaries[0].pushed is False
    client.whoami.assert_not_called()


def test_invalid_strategy_raises():
    spec = RepoSpec("octo", "x")
    client = MagicMock()
    opts = commits.CommitOptions(
        repos=[spec],
        start=dt.date(2024, 1, 1),
        end=dt.date(2024, 1, 1),
        strategy="wrong",
        dry_run=True,
    )
    with pytest.raises(ValueError):
        commits.run(client, opts)
