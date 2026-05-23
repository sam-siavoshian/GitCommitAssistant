# GitCommitAssistant

Farms GitHub achievements via backdated commits, coauthored PRs, and seeded discussions on repos you own.

For your own GitHub account, on repos you control. Uses a Personal Access Token you provide. No mass-account creation, no impersonation, no commits attributed to other users.

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.6+](https://img.shields.io/badge/python-3.6%2B-blue.svg)](https://www.python.org/)

## What it does

- **Commits**. Generates N commits per day across the repos you point it at, on any date you pick (today, last week, a year ago). Spoofs `GIT_AUTHOR_DATE` and `GIT_COMMITTER_DATE` so the contribution graph reflects the chosen dates.
- **Repos**. Auto-creates private repos via `POST /user/repos` if you don't have enough to commit to.
- **Pull requests**. Opens PRs and self-merges them via `POST /repos/{user}/{repo}/pulls` + `PUT /merge`. Drives Pull Shark + YOLO.
- **Coauthored PRs**. Multi-line commit messages with `Co-authored-by: Name <email>` footers. Unlocks Pair Extraordinaire.
- **Discussions**. Creates Discussions via GraphQL, posts a comment, marks the comment as the accepted answer via `markDiscussionCommentAsAnswer`. Unlocks Galaxy Brain.
- **Interactive**. Prompts walk you through PAT entry, repo selection, message pool, date range, and feature picks.

## Install

```bash
git clone https://github.com/sam-siavoshian/GitCommitAssistant.git
cd GitCommitAssistant
pip install -r requirements.txt
```

Requires Python 3.6+ and `git` on `PATH`. One dependency: `requests`.

## Run

```bash
python GitCommitAssistant.py
```

The script prompts for:

- **GitHub Personal Access Token** (classic, with `repo` + `write:discussion` scopes, or fine-grained equivalents)
- **Repo URLs** (or it pulls from `repo_names.txt` and auto-creates)
- **Commit message source** (defaults to `commit_messages.txt`)
- **Date range + commit frequency**
- **Which features to run** (commits / PRs / coauthored / discussions / all)

## Achievements covered

| Achievement | Mechanism |
|---|---|
| **Pull Shark** | PR created via REST API, self-merged via `PUT /merge` |
| **YOLO** | Self-merged PR without review |
| **Pair Extraordinaire** | `Co-authored-by: Name <email>` commit footers (multi-line) |
| **Galaxy Brain** | Discussion + comment + `markDiscussionCommentAsAnswer` GraphQL mutation |
| **Quickdraw** | Manual. Open and close an issue/PR within ~5 min yourself. |

## Files

| Path | Purpose |
|---|---|
| `GitCommitAssistant.py` | The whole script. 1850 lines, single-file by design. |
| `commit_messages.txt` | Pool of commit subjects to sample. Edit to fit your project vocabulary. |
| `repo_names.txt` | Names used when auto-creating repos. Edit before running. |
| `requirements.txt` | `requests` only. |

## Token scopes

Classic PAT:

- `repo`. Create repos, push, open + merge PRs.
- `write:discussion`. Create discussions, mark answers.

Generate at [github.com/settings/tokens](https://github.com/settings/tokens). Don't commit the token. The script reads it from stdin and keeps it in memory only.

## Notes

- Coauthor emails in `Co-authored-by:` footers are plaintext. They don't notify or attribute to the named person unless that email matches a real GitHub account.
- Backdated commits show on the contribution graph in the date bucket of `GIT_AUTHOR_DATE`. GitHub renders the graph from authored-on dates, not pushed-on.
- The script uses a `ThreadPoolExecutor` (10 workers) to prepare backdated commit metadata in parallel, then runs `git commit` serially per repo to avoid index races.

## License

[MIT](LICENSE) © [@sam-siavoshian](https://github.com/sam-siavoshian).
