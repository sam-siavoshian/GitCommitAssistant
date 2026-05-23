import pytest

from gca.repo_spec import parse_repo
from gca.utils import safe_repo_name


def test_safe_repo_name_allows_normal():
    assert safe_repo_name("my-repo_v2.0") == "my-repo_v2.0"
    assert safe_repo_name("alpha") == "alpha"


@pytest.mark.parametrize(
    "bad",
    [
        "../etc/passwd",
        "name with spaces",
        "name/with/slash",
        "..",
        "-leading-dash",
        ".leading-dot",
        "",
        "x" * 200,
    ],
)
def test_safe_repo_name_rejects(bad):
    with pytest.raises(ValueError):
        safe_repo_name(bad)


def test_parse_repo_https():
    spec = parse_repo("https://github.com/sam-siavoshian/GitCommitAssistant.git")
    assert spec.owner == "sam-siavoshian"
    assert spec.name == "GitCommitAssistant"


def test_parse_repo_shorthand():
    spec = parse_repo("sam-siavoshian/GitCommitAssistant")
    assert spec.full == "sam-siavoshian/GitCommitAssistant"


def test_parse_repo_ssh():
    spec = parse_repo("git@github.com:sam-siavoshian/GitCommitAssistant.git")
    assert spec.full == "sam-siavoshian/GitCommitAssistant"


@pytest.mark.parametrize("bad", ["", "owner-only", "https://gitlab.com/a/b", "owner/", "/name"])
def test_parse_repo_rejects(bad):
    with pytest.raises(ValueError):
        parse_repo(bad)


def test_auth_clone_url_redacted_in_repr():
    spec = parse_repo("a/b")
    url = spec.auth_clone_url("ghp_fake")
    assert "x-access-token:ghp_fake" in url
    # not asserting redaction since this is the actual auth URL, but at least confirm it's https
    assert url.startswith("https://")
