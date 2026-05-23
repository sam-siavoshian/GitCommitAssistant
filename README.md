# gca - GitCommitAssistant

A Python CLI for automating GitHub activity: backdated commits, real pull requests, Q&A discussions, coauthored PRs, and Quickdraw issues. Honest about what each GitHub achievement actually requires in 2026, including the ones GitHub has frozen.

This is the v2 rewrite. The old `GitCommitAssistant.py` interactive script has been replaced by a proper Python package with subcommands, real tests, and no hardcoded `main` branch.

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)

## What changed in v2

- Single 1850-line script split into a clean package (`gca commits`, `gca prs`, `gca discussions`, `gca coauthored`, `gca quickdraw`, `gca doctor`, `gca init`).
- Default branch is detected per repo, not hardcoded to `main`.
- Commit dates use the git internal `<unix-ts> +HHMM` format, the only fully unambiguous one.
- Coauthored commits validate that the coauthor email is not your own primary verified email (a hard requirement when Pair Extraordinaire still awarded).
- Galaxy Brain flow prefers the `q-a` slug category and falls back cleanly when none exists.
- GitHub client honors `X-RateLimit-Reset` on 429, retries 5xx with backoff, never retries hard 4xx.
- Token resolved from `--token` > `GCA_GITHUB_TOKEN` env > `.env` > OS keychain > prompt. Never written to disk by default.
- 57 unit tests + 1 gated live smoke. No fake progress, no fake stats.

## Install

Requires Python 3.10 or newer and `git` on PATH.

```bash
# from a clone
pip install -e .

# or once published
pipx install gca
```

## Quickstart

```bash
# one-time: save your PAT in the OS keychain
gca init

# verify everything is wired
gca doctor

# 30 days of backdated commits, 2-5 commits on each weekday
gca commits \
  --repo sam-siavoshian/playground \
  --start 2025-04-01 --end 2025-04-30 \
  --strategy weekdays --min 2 --max 5

# 5 real merged PRs spread across April
gca prs --repo sam-siavoshian/playground -n 5 --start 2025-04-01 --end 2025-04-30

# open + close 3 issues fast (Quickdraw)
gca quickdraw --repo sam-siavoshian/playground -n 3

# Q&A discussion with self-marked accepted answer (Galaxy Brain best-effort)
gca discussions --repo sam-siavoshian/playground -n 1

# coauthored PR (mechanics correct; Pair Extraordinaire badge frozen)
gca coauthored --repo sam-siavoshian/playground -n 1 \
  --start 2025-04-01 --end 2025-04-30 \
  -c "Ada Lovelace <ada@example.org>"

# bulk-create empty repos
gca create-repos demo-1 demo-2 demo-3 --private
```

Every command accepts `--dry-run` to print what would happen without touching GitHub, and `--json` for machine-readable output.

## Subcommand reference

| Command | What it does |
|---|---|
| `gca init` | Wizard: verifies your PAT and offers to save it to the OS keychain. |
| `gca doctor` | Checks token, scopes, git on PATH, and GitHub reachability. |
| `gca commits` | Walks a date range and drops `N` backdated commits per active day on the default branch. |
| `gca prs` | Creates `--count` real branches per repo with backdated commits, opens PRs, merges them (`--merge-method squash\|merge\|rebase`). |
| `gca discussions` | Creates `--count` Q&A discussions per repo and self-marks an accepted answer. |
| `gca coauthored` | Like `prs` but with `Co-authored-by:` trailers on every commit. Validates the coauthor is not you. |
| `gca quickdraw` | Opens then closes `--count` issues, with `--pause` seconds between (kept under 5 minutes). |
| `gca create-repos` | Bulk-create empty private/public repos. |

## GitHub achievements: what actually works in 2026

| Badge | Status | What this tool does | What you also need |
|---|---|---|---|
| **Pull Shark** | Active | Opens real backdated PRs and merges them (`gca prs`). | A repo you own and write to. |
| **Galaxy Brain** | Active but changed in 2024 | Creates Q&A discussions and marks your own comment as the accepted answer (`gca discussions`). | GitHub now factors in upvotes from other users. Self-marking alone may not award the badge. |
| **Pair Extraordinaire** | **Frozen by GitHub in Mar 2024** | Emits commits with correct `Co-authored-by:` trailers (`gca coauthored`). | The badge no longer awards to new earners. Existing badges remain. The trailers are still useful for attribution. |
| **YOLO** | Active | Side effect of `gca prs` since the PRs merge without a review. | Repo not protected by required reviews. |
| **Quickdraw** | Active | Opens then closes an issue within 5 minutes (`gca quickdraw`). | First close must be inside the 5-minute window. |
| **Starstruck** | Active | Not automated. | Real stars from real accounts. Buying stars is a ToS violation. |
| **Public Sponsor** | Active | Not automated. | Sponsor someone publicly via GitHub Sponsors. |
| **Heart On Your Sleeve** | Active | Not automated. | Add a reaction to any GitHub entity. |

Achievements only count for activity on **public** repositories. Set `--public` on `gca create-repos` if you are starting fresh.

## Tokens and scopes

Generate a classic PAT at <https://github.com/settings/tokens> or a fine-grained PAT under <https://github.com/settings/personal-access-tokens>.

| Scope | Needed for |
|---|---|
| `repo` | Everything except discussions. |
| `write:discussion` | `gca discussions`. |
| `delete_repo` | Only the live smoke test, which deletes its own throwaway repo at the end. |

Resolution order at runtime:

1. `--token` flag.
2. `GCA_GITHUB_TOKEN` environment variable.
3. `.env` file in the current directory (see `.env.example`).
4. OS keychain entry (`service=gca`, `username=github`). Opt-in via `gca init`.
5. Interactive prompt.

Tokens are sent only to GitHub over HTTPS. They are not written to logs or to disk unless you opt into the keychain.

## Testing

```bash
pip install -e ".[dev]"
pytest                    # 57 unit tests, ~2 seconds
GCA_LIVE=1 GCA_GITHUB_TOKEN=ghp_... pytest -m live    # 1 live smoke test
```

The live smoke test creates a public repo named `gca-smoke-<timestamp>` on your account, runs commits / PRs / discussions / quickdraw against it, then deletes it. If anything fails, the repo URL is printed and the repo is left for forensics.

## Security notes

- All subprocess calls use list form. No `shell=True`. No string interpolation into commands.
- Repo names are validated against a strict regex (no path separators, no `..`).
- Clone URLs embed the token inline (`https://x-access-token:TOKEN@github.com/...`) but the temp directory is wiped on every exit, success or failure.
- GraphQL discussions use `Authorization: Bearer ...` consistently; REST and GraphQL both go through the same authenticated session.

## Limitations and ToS

GitHub's terms of service prohibit creating fake activity to mislead other users about your work history. This tool is most useful for:

- Filling your contribution graph for repos that you legitimately worked on offline.
- Practicing CI / git workflows on throwaway repos.
- Earning the achievements that GitHub still awards for activity (Pull Shark, Quickdraw, YOLO).

It does not, and cannot, help with badges GitHub has frozen (Pair Extraordinaire) or that require real third-party action (Starstruck, Galaxy Brain post-2024 upvote requirement).

Use responsibly.

## License

[MIT](LICENSE) (c) [@sam-siavoshian](https://github.com/sam-siavoshian).
