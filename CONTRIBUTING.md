# Contributing

PRs welcome, especially:

- Bugfixes for breakage when GitHub changes its API (the Discussions GraphQL surface drifts the most).
- Better default `src/gca/data/commit_messages.txt` / `repo_names.txt` pools.
- Quality-of-life flags (`--json`, `--dry-run`, additional merge methods, etc).
- New subcommands for activity that GitHub still awards badges for.

## Setup

```bash
git clone https://github.com/sam-siavoshian/GitCommitAssistant.git
cd GitCommitAssistant
python -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
```

Requires Python 3.10+ and `git` on `PATH`.

## Run locally

```bash
gca --help
gca doctor
gca commits --repo owner/name --start 2025-01-01 --end 2025-01-07 --strategy weekdays --dry-run
```

`--dry-run` exercises the entire flow except git/network calls. Use it as the default smoke check.

## Tests

```bash
pytest                                                  # 57 unit tests, ~2s
GCA_LIVE=1 GCA_GITHUB_TOKEN=ghp_... pytest -m live      # opt-in live smoke
ruff check src tests
```

The live smoke test creates a throwaway public repo `gca-smoke-<timestamp>` on the authenticated account, exercises every feature, then deletes it. If anything fails, the repo URL is printed and the repo is left for inspection (no silent cleanup).

## Style

- Keep modules single-purpose. `github_api.py` is the only place that talks to GitHub. `git_ops.py` is the only place that shells out to git.
- All subprocess calls use list form, never `shell=True`.
- Token never written to disk by default. Keychain storage is opt-in.
- Ruff config lives in `pyproject.toml`. Run `ruff check src tests --fix` before opening a PR.
- No co-author trailers on commits to this repo.

## Filing PRs

- Open a draft early for non-trivial changes.
- Include manual test steps: which PAT scopes, which feature, expected behavior.
- Keep PR descriptions short. What changed and why.

## Bugs

Use the templates under [.github/ISSUE_TEMPLATE/](.github/ISSUE_TEMPLATE/). Include:

- Python version, OS.
- Which subcommand broke (`gca commits` / `gca prs` / etc).
- The exact GitHub API response if one came back (redact your token).
- Whether the PAT scopes match the README.
