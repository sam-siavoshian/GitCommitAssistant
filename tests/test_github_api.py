import pytest
import responses

from gca.github_api import (
    DiscussionCategoryError,
    GitHubClient,
    MergeBlockedError,
    PRExistsError,
    RepoRef,
)

REPO = RepoRef(owner="octo", name="hello", default_branch="main")


@responses.activate
def test_create_pr_201():
    responses.add(
        responses.POST,
        "https://api.github.com/repos/octo/hello/pulls",
        status=201,
        json={"number": 42},
    )
    client = GitHubClient("ghp_fake")
    n = client.create_pull_request(REPO, head="feat", title="t", body="b")
    assert n == 42


@responses.activate
def test_create_pr_already_exists():
    responses.add(
        responses.POST,
        "https://api.github.com/repos/octo/hello/pulls",
        status=422,
        json={"message": "Validation Failed", "errors": [{"message": "A pull request already exists for octo:feat."}]},
    )
    client = GitHubClient("ghp_fake")
    with pytest.raises(PRExistsError):
        client.create_pull_request(REPO, head="feat", title="t", body="b")


@responses.activate
def test_merge_pr_405_blocked():
    responses.add(
        responses.PUT,
        "https://api.github.com/repos/octo/hello/pulls/9/merge",
        status=405,
        json={"message": "Pull Request is not mergeable"},
    )
    client = GitHubClient("ghp_fake")
    with pytest.raises(MergeBlockedError):
        client.merge_pull_request(REPO, 9)


@responses.activate
def test_merge_pr_invalid_method():
    client = GitHubClient("ghp_fake")
    with pytest.raises(ValueError):
        client.merge_pull_request(REPO, 1, method="lol")


@responses.activate
def test_create_issue_then_close():
    responses.add(
        responses.POST,
        "https://api.github.com/repos/octo/hello/issues",
        status=201,
        json={"number": 7},
    )
    responses.add(
        responses.PATCH,
        "https://api.github.com/repos/octo/hello/issues/7",
        status=200,
        json={"state": "closed"},
    )
    client = GitHubClient("ghp_fake")
    n = client.create_issue(REPO, title="t")
    assert n == 7
    client.close_issue(REPO, 7)


@responses.activate
def test_find_qa_category_picks_q_a_slug():
    responses.add(
        responses.POST,
        "https://api.github.com/graphql",
        status=200,
        json={
            "data": {
                "repository": {
                    "id": "REPO_ID",
                    "discussionCategories": {
                        "nodes": [
                            {"id": "C_GEN", "name": "General", "slug": "general", "isAnswerable": False},
                            {"id": "C_QA", "name": "Q&A", "slug": "q-a", "isAnswerable": True},
                            {"id": "C_IDEAS", "name": "Ideas", "slug": "ideas", "isAnswerable": True},
                        ]
                    },
                }
            }
        },
    )
    client = GitHubClient("ghp_fake")
    rid, cid, cname = client.find_repo_and_qa_category(REPO)
    assert (rid, cid, cname) == ("REPO_ID", "C_QA", "Q&A")


@responses.activate
def test_find_qa_category_fallback_to_any_answerable():
    responses.add(
        responses.POST,
        "https://api.github.com/graphql",
        status=200,
        json={
            "data": {
                "repository": {
                    "id": "REPO_ID",
                    "discussionCategories": {
                        "nodes": [
                            {"id": "C_IDEAS", "name": "Ideas", "slug": "ideas", "isAnswerable": True},
                        ]
                    },
                }
            }
        },
    )
    client = GitHubClient("ghp_fake")
    _, cid, _ = client.find_repo_and_qa_category(REPO)
    assert cid == "C_IDEAS"


@responses.activate
def test_find_qa_category_raises_when_none():
    responses.add(
        responses.POST,
        "https://api.github.com/graphql",
        status=200,
        json={
            "data": {
                "repository": {
                    "id": "REPO_ID",
                    "discussionCategories": {
                        "nodes": [
                            {"id": "C_GEN", "name": "General", "slug": "general", "isAnswerable": False}
                        ]
                    },
                }
            }
        },
    )
    client = GitHubClient("ghp_fake")
    with pytest.raises(DiscussionCategoryError):
        client.find_repo_and_qa_category(REPO)


@responses.activate
def test_mark_comment_as_answer_sends_correct_input():
    captured = {}

    def cb(request):
        captured["body"] = request.body
        return (200, {}, '{"data": {"markDiscussionCommentAsAnswer": {"discussion": {"id": "D"}}}}')

    responses.add_callback(responses.POST, "https://api.github.com/graphql", callback=cb)
    client = GitHubClient("ghp_fake")
    client.mark_comment_as_answer("C_123")
    body = captured["body"]
    assert b"markDiscussionCommentAsAnswer" in body
    assert b'"id": "C_123"' in body


@responses.activate
def test_whoami_caches_scopes():
    responses.add(
        responses.GET,
        "https://api.github.com/user",
        status=200,
        json={"login": "octocat"},
        headers={"x-oauth-scopes": "repo, write:discussion, delete_repo"},
    )
    client = GitHubClient("ghp_fake")
    assert client.whoami() == "octocat"
    assert "repo" in client.scopes()
    assert "write:discussion" in client.scopes()
    assert "delete_repo" in client.scopes()
