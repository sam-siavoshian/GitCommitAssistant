import subprocess
from pathlib import Path

import pytest

from gca import git_ops


def _make_local_clone(remote: Path, dest: Path, default_branch: str = "trunk") -> Path:
    # populate the bare remote with an initial commit on `default_branch`
    seed = dest.parent / "seed"
    subprocess.run(["git", "init", "-q", "-b", default_branch, str(seed)], check=True)
    subprocess.run(["git", "-C", str(seed), "config", "user.email", "x@x"], check=True)
    subprocess.run(["git", "-C", str(seed), "config", "user.name", "x"], check=True)
    (seed / "README.md").write_text("hi")
    subprocess.run(["git", "-C", str(seed), "add", "README.md"], check=True)
    subprocess.run(["git", "-C", str(seed), "commit", "-q", "-m", "init"], check=True)
    subprocess.run(
        ["git", "-C", str(seed), "remote", "add", "origin", str(remote)], check=True
    )
    subprocess.run(["git", "-C", str(seed), "push", "-q", "-u", "origin", default_branch], check=True)

    subprocess.run(["git", "clone", "-q", str(remote), str(dest)], check=True)
    return dest


def test_detect_trunk(bare_remote, tmp_path):
    dest = tmp_path / "clone"
    _make_local_clone(bare_remote, dest, default_branch="trunk")
    assert git_ops.detect_default_branch(dest) == "trunk"


@pytest.mark.parametrize("branch", ["main", "master", "release/2025"])
def test_detect_various_default_branches(tmp_path_factory, branch):
    remote = tmp_path_factory.mktemp("remote")
    subprocess.run(["git", "init", "-q", "--bare", "-b", branch, str(remote)], check=True)
    dest = tmp_path_factory.mktemp("clone-dest") / "clone"
    _make_local_clone(remote, dest, default_branch=branch)
    assert git_ops.detect_default_branch(dest) == branch
