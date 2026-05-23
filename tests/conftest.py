"""Shared pytest fixtures."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest


@pytest.fixture
def git_repo(tmp_path: Path) -> Path:
    """An empty initialized git repo with identity set."""
    subprocess.run(["git", "init", "-q", "-b", "main", str(tmp_path)], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "config", "user.name", "gca-test"], check=True)
    subprocess.run(
        ["git", "-C", str(tmp_path), "config", "user.email", "test@gca.local"], check=True
    )
    return tmp_path


@pytest.fixture
def bare_remote(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A bare repo that can act as an `origin` for default-branch detection tests."""
    p = tmp_path_factory.mktemp("remote")
    subprocess.run(["git", "init", "-q", "--bare", "-b", "trunk", str(p)], check=True)
    return p


@pytest.fixture(autouse=True)
def _no_real_keyring(monkeypatch):
    """Don't let tests touch the user's actual macOS Keychain."""
    monkeypatch.setenv("PYTHON_KEYRING_BACKEND", "keyring.backends.null.Keyring")
    yield


@pytest.fixture(autouse=True)
def _isolate_env(monkeypatch, tmp_path):
    """Tests must never read the user's real GCA_GITHUB_TOKEN or .env."""
    monkeypatch.delenv("GCA_GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GCA_GITHUB_API", raising=False)
    monkeypatch.chdir(tmp_path)
    yield


def have_cmd(name: str) -> bool:
    return shutil.which(name) is not None


@pytest.fixture
def have_git() -> bool:
    return have_cmd("git")


_ = os  # silence imports
