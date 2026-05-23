"""Typer CLI surface for gca."""

from __future__ import annotations

import datetime as dt
import json
import logging
import shutil
import sys

import typer
from rich.console import Console
from rich.logging import RichHandler
from rich.table import Table

from gca import __version__, coauthored, commits, config, discussions, prs, quickdraw
from gca.github_api import GitHubAuthError, GitHubClient, GitHubError
from gca.repo_spec import RepoSpec, parse_repo
from gca.utils import parse_date

app = typer.Typer(
    add_completion=False,
    no_args_is_help=False,
    rich_markup_mode="rich",
    help="gca - GitHub activity automation. See `gca <command> --help`.",
)
console = Console()


def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="%H:%M:%S",
        handlers=[RichHandler(console=console, show_path=False, rich_tracebacks=False)],
    )


def _print_version(value: bool) -> None:
    if value:
        console.print(f"gca {__version__}")
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def root(
    ctx: typer.Context,
    verbose: bool = typer.Option(False, "--verbose", "-V", help="DEBUG logging"),
    version: bool = typer.Option(
        False, "--version", callback=_print_version, is_eager=True, help="Print version and exit"
    ),
) -> None:
    _setup_logging(verbose)
    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())
        raise typer.Exit()


def _client(token_opt: str | None) -> GitHubClient:
    try:
        token = config.resolve_token(token_opt)
    except RuntimeError as e:
        console.print(f"[red]{e}[/]")
        raise typer.Exit(2) from e
    return GitHubClient(token)


def _parse_repos(values: list[str]) -> list[RepoSpec]:
    if not values:
        raise typer.BadParameter("at least one --repo required")
    specs: list[RepoSpec] = []
    for v in values:
        try:
            specs.append(parse_repo(v))
        except ValueError as e:
            raise typer.BadParameter(str(e)) from e
    return specs


def _emit(summary: object, json_out: bool) -> None:
    if json_out:
        console.print_json(data=_to_dict(summary))
    else:
        _render_table(summary)


def _to_dict(o):
    if isinstance(o, list):
        return [_to_dict(x) for x in o]
    if hasattr(o, "__dataclass_fields__"):
        return {k: _to_dict(getattr(o, k)) for k in o.__dataclass_fields__}
    return o


def _render_table(summary) -> None:
    if not isinstance(summary, list) or not summary:
        console.print(summary)
        return
    first = summary[0]
    if not hasattr(first, "__dataclass_fields__"):
        console.print(summary)
        return
    table = Table(show_header=True, header_style="bold")
    fields = list(first.__dataclass_fields__.keys())
    for f in fields:
        table.add_column(f)
    for row in summary:
        cells = []
        for f in fields:
            val = getattr(row, f)
            if isinstance(val, list):
                cells.append(", ".join(str(v) for v in val) if val else "-")
            else:
                cells.append(str(val) if val is not None else "-")
        table.add_row(*cells)
    console.print(table)


# ----- doctor -----


@app.command()
def doctor(token: str | None = typer.Option(None, "--token", "-t", help="GitHub PAT override")) -> None:
    """Verify token, scopes, git presence, and GitHub reachability."""
    console.print("[bold]gca doctor[/]")
    if not shutil.which("git"):
        console.print("[red]X[/] git not on PATH")
        raise typer.Exit(1)
    console.print("[green]ok[/] git on PATH")
    try:
        client = _client(token)
        login = client.whoami()
    except GitHubAuthError as e:
        console.print(f"[red]X[/] token rejected: {e}")
        raise typer.Exit(1) from e
    console.print(f"[green]ok[/] authenticated as [bold]{login}[/]")
    scopes = client.scopes()
    console.print(f"     scopes: {', '.join(sorted(scopes)) or '(none reported)'}")
    needed = {"repo"}
    missing = needed - scopes
    if missing:
        console.print(f"[yellow]![/] missing scopes for full feature set: {missing}")
    if "write:discussion" not in scopes:
        console.print("[yellow]![/] missing write:discussion - `gca discussions` will fail")
    if "delete_repo" not in scopes:
        console.print("[yellow]![/] missing delete_repo - the live smoke test cannot clean up")


# ----- init -----


@app.command()
def init() -> None:
    """Interactive setup wizard: store token in OS keychain."""
    console.print("[bold]gca init[/]")
    token = typer.prompt("Paste your GitHub PAT (input hidden)", hide_input=True).strip()
    if not config.looks_like_token(token):
        console.print(
            "[yellow]![/] this doesn't look like a GitHub token (expected ghp_/github_pat_/gho_/ghs_/ghu_ prefix). Storing anyway."
        )
    try:
        client = GitHubClient(token)
        login = client.whoami()
    except GitHubError as e:
        console.print(f"[red]token rejected by GitHub: {e}[/]")
        raise typer.Exit(1) from e
    console.print(f"[green]token works[/] as [bold]{login}[/]")
    if typer.confirm("Save to OS keychain (recommended)?", default=True):
        try:
            config.save_token_to_keyring(token)
            console.print("[green]saved to keychain[/]")
        except Exception as e:
            console.print(f"[red]keychain unavailable: {e}[/]")


# ----- commits -----


@app.command(name="commits")
def commits_cmd(
    repo: list[str] = typer.Option(..., "--repo", "-r", help="GitHub repo (owner/name or URL); repeatable"),
    start: str = typer.Option(..., "--start", help="YYYY-MM-DD"),
    end: str = typer.Option(..., "--end", help="YYYY-MM-DD"),
    strategy: str = typer.Option("every-day", "--strategy", help="every-day|random|weekdays|weekends"),
    per_day_min: int = typer.Option(1, "--min", help="Min commits per active day"),
    per_day_max: int = typer.Option(1, "--max", help="Max commits per active day"),
    token: str | None = typer.Option(None, "--token", "-t"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Generate backdated commits across a date range."""
    opts = commits.CommitOptions(
        repos=_parse_repos(repo),
        start=parse_date(start),
        end=parse_date(end),
        strategy=strategy,
        per_day_min=per_day_min,
        per_day_max=per_day_max,
        dry_run=dry_run,
    )
    client = _client(token)
    summaries = commits.run(client, opts)
    _emit(summaries, json_out)
    _exit_with_errors(summaries)


# ----- prs -----


@app.command(name="prs")
def prs_cmd(
    repo: list[str] = typer.Option(..., "--repo", "-r"),
    count: int = typer.Option(..., "--count", "-n"),
    start: str = typer.Option(..., "--start"),
    end: str = typer.Option(..., "--end"),
    merge_method: str = typer.Option("squash", "--merge-method", help="squash|merge|rebase"),
    token: str | None = typer.Option(None, "--token", "-t"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Open + merge `count` real backdated PRs per repo (Pull Shark / YOLO)."""
    opts = prs.PROptions(
        repos=_parse_repos(repo),
        count=count,
        start=parse_date(start),
        end=parse_date(end),
        merge_method=merge_method,
        dry_run=dry_run,
    )
    client = _client(token)
    summaries = prs.run(client, opts)
    _emit(summaries, json_out)
    _exit_with_errors(summaries)


# ----- discussions -----


@app.command(name="discussions")
def discussions_cmd(
    repo: list[str] = typer.Option(..., "--repo", "-r"),
    count: int = typer.Option(..., "--count", "-n"),
    token: str | None = typer.Option(None, "--token", "-t"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Create Q&A discussions and self-mark accepted answer (Galaxy Brain best-effort)."""
    opts = discussions.DiscussionOptions(repos=_parse_repos(repo), count=count, dry_run=dry_run)
    client = _client(token)
    summaries = discussions.run(client, opts)
    _emit(summaries, json_out)
    _exit_with_errors(summaries)


# ----- coauthored -----


@app.command(name="coauthored")
def coauthored_cmd(
    repo: list[str] = typer.Option(..., "--repo", "-r"),
    count: int = typer.Option(..., "--count", "-n"),
    start: str = typer.Option(..., "--start"),
    end: str = typer.Option(..., "--end"),
    coauthor: list[str] = typer.Option(
        ..., "--coauthor", "-c", help="'Name <email>' (repeatable)"
    ),
    merge_method: str = typer.Option("squash", "--merge-method"),
    token: str | None = typer.Option(None, "--token", "-t"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Coauthored PRs (mechanics correct; the Pair Extraordinaire badge was frozen Mar 2024)."""
    opts = prs.PROptions(
        repos=_parse_repos(repo),
        count=count,
        start=parse_date(start),
        end=parse_date(end),
        merge_method=merge_method,
        coauthors=coauthor,
        dry_run=dry_run,
    )
    client = _client(token)
    summaries = coauthored.run(client, opts)
    _emit(summaries, json_out)
    _exit_with_errors(summaries)


# ----- quickdraw -----


@app.command(name="quickdraw")
def quickdraw_cmd(
    repo: list[str] = typer.Option(..., "--repo", "-r"),
    count: int = typer.Option(..., "--count", "-n"),
    pause: float = typer.Option(1.0, "--pause", help="Seconds between open and close (must keep total <5min)"),
    token: str | None = typer.Option(None, "--token", "-t"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Open then close issues fast for the Quickdraw badge."""
    opts = quickdraw.QuickdrawOptions(
        repos=_parse_repos(repo), count=count, pause_seconds=pause, dry_run=dry_run
    )
    client = _client(token)
    summaries = quickdraw.run(client, opts)
    _emit(summaries, json_out)
    _exit_with_errors(summaries)


# ----- create-repos -----


@app.command(name="create-repos")
def create_repos_cmd(
    name: list[str] = typer.Argument(..., help="Repo names to create"),
    private: bool = typer.Option(True, "--private/--public"),
    description: str = typer.Option("", "--desc"),
    token: str | None = typer.Option(None, "--token", "-t"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Create one or more GitHub repos under the authenticated account."""
    client = _client(token)
    results = []
    for n in name:
        try:
            ref = client.create_repo(n, private=private, description=description)
            results.append({"name": n, "ok": True, "url": f"https://github.com/{ref.full}"})
        except GitHubError as e:
            results.append({"name": n, "ok": False, "error": str(e)})
    if json_out:
        console.print_json(data=results)
    else:
        for r in results:
            if r["ok"]:
                console.print(f"[green]ok[/] {r['name']}: {r['url']}")
            else:
                console.print(f"[red]X[/] {r['name']}: {r['error']}")
    if any(not r["ok"] for r in results):
        raise typer.Exit(1)


def _exit_with_errors(summaries) -> None:
    """Exit non-zero if any summary has errors."""
    for s in summaries:
        if getattr(s, "error", None) or getattr(s, "errors", None):
            raise typer.Exit(1)


# silence unused import warnings on dt
_ = dt
_ = json
_ = sys


if __name__ == "__main__":  # pragma: no cover
    app()
