import time

import responses

from gca.github_api import GitHubAuthError, GitHubClient, GitHubError, GitHubNotFound


@responses.activate
def test_429_with_reset_waits_then_retries(monkeypatch):
    sleeps: list[float] = []
    monkeypatch.setattr(time, "sleep", lambda s: sleeps.append(s))
    monkeypatch.setattr(time, "time", lambda: 1_000_000)

    responses.add(
        responses.GET,
        "https://api.github.com/user",
        status=429,
        headers={"x-ratelimit-remaining": "0", "x-ratelimit-reset": "1000003"},
        json={"message": "rate limited"},
    )
    responses.add(
        responses.GET,
        "https://api.github.com/user",
        status=200,
        json={"login": "octocat"},
        headers={"x-oauth-scopes": "repo, write:discussion"},
    )

    client = GitHubClient("ghp_fake")
    assert client.whoami() == "octocat"
    # we should have slept ~ (1000003 - 1000000 + 1) = 4 seconds
    assert sleeps and sleeps[0] >= 3


@responses.activate
def test_5xx_backoff_three_tries(monkeypatch):
    sleeps: list[float] = []
    monkeypatch.setattr(time, "sleep", lambda s: sleeps.append(s))
    for _ in range(3):
        responses.add(
            responses.GET,
            "https://api.github.com/user",
            status=500,
            json={"message": "boom"},
        )
    responses.add(
        responses.GET,
        "https://api.github.com/user",
        status=200,
        json={"login": "octocat"},
    )
    client = GitHubClient("ghp_fake")
    assert client.whoami() == "octocat"
    # exponential backoff: 1, 2, 4
    assert sleeps == [1, 2, 4]


@responses.activate
def test_401_does_not_retry():
    responses.add(
        responses.GET,
        "https://api.github.com/user",
        status=401,
        json={"message": "Bad credentials"},
    )
    client = GitHubClient("ghp_fake")
    try:
        client.whoami()
    except GitHubAuthError:
        pass
    else:
        raise AssertionError("expected GitHubAuthError")
    assert len(responses.calls) == 1


@responses.activate
def test_404_raises_notfound():
    responses.add(
        responses.GET,
        "https://api.github.com/repos/x/y",
        status=404,
        json={"message": "Not Found"},
    )
    client = GitHubClient("ghp_fake")
    try:
        client.get_repo("x", "y")
    except GitHubNotFound:
        pass
    else:
        raise AssertionError("expected GitHubNotFound")


@responses.activate
def test_422_generic_raises_error():
    responses.add(
        responses.POST,
        "https://api.github.com/user/repos",
        status=400,
        json={"message": "bad"},
    )
    client = GitHubClient("ghp_fake")
    try:
        client.create_repo("x")
    except GitHubError:
        pass
    else:
        raise AssertionError("expected GitHubError")
