# Contributing

PRs welcome, especially:

- Bugfixes for breakage when GitHub changes its API (the Discussions GraphQL surface drifts the most)
- Better default `commit_messages.txt` / `repo_names.txt` pools
- Quality-of-life flags (non-interactive mode, `--dry-run`, etc)

## Setup

```bash
git clone https://github.com/sam-siavoshian/GitCommitAssistant.git
cd GitCommitAssistant
pip install -r requirements.txt
```

Python 3.6+ and `git` on `PATH`.

## Run locally

```bash
python GitCommitAssistant.py
```

The script is interactive. To smoke test without hitting GitHub, run with no PAT and stop at the first prompt.

## Style

- Single file by design. Don't split into modules unless there's a real reason.
- Match the existing function-docstring shape (Args, Returns, Raises blocks).
- Keep `requests` as the only runtime dependency. Resist adding `httpx`, `gh`, `PyGithub`.
- Don't add commit messages that look obviously fake ("Did a thing", "asdf"). The pool should pass casual inspection.

## Filing PRs

- Open a draft early for non-trivial changes.
- Include manual test steps: which PAT scopes, which feature, expected behavior.
- Match the README's voice: lowercase, no fluff, no AI slop ("powerful", "designed to help", etc).

## Bugs

Use the templates under [.github/ISSUE_TEMPLATE/](.github/ISSUE_TEMPLATE/). Include:

- Python version, OS
- Which feature broke (commits / PRs / discussions / coauthored)
- The exact GitHub API response if one came back
- Whether the PAT scopes match the README
