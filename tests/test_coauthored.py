from unittest.mock import MagicMock

import pytest

from gca import coauthored
from gca.git_ops import build_commit_message
from gca.utils import parse_coauthor


def test_trailer_block_has_one_blank_line():
    msg = build_commit_message(
        "Add login",
        body="It now supports SSO.",
        coauthors=["Ada Lovelace <ada@example.org>"],
    )
    assert "\n\nCo-authored-by: Ada Lovelace <ada@example.org>\n" in msg
    # exactly one blank line between body and trailer
    pre, _, post = msg.partition("Co-authored-by:")
    assert pre.endswith("\n\n")
    assert not pre.endswith("\n\n\n")
    assert post.startswith(" Ada Lovelace")


def test_multiple_coauthors():
    msg = build_commit_message(
        "feat: x",
        coauthors=[
            "Ada Lovelace <ada@example.org>",
            "Grace Hopper <grace@example.org>",
        ],
    )
    assert msg.count("Co-authored-by:") == 2


def test_parse_coauthor_rejects_garbage():
    with pytest.raises(ValueError):
        parse_coauthor("Ada Lovelace")
    with pytest.raises(ValueError):
        parse_coauthor("Ada <not-an-email>")
    with pytest.raises(ValueError):
        parse_coauthor("<ada@x.com>")


def test_validate_coauthors_rejects_actor_email():
    client = MagicMock()
    client.primary_verified_email.return_value = "sam@example.com"
    with pytest.raises(ValueError, match="matches your own primary email"):
        coauthored.validate_coauthors(client, ["Sam Self <sam@example.com>"])


def test_validate_coauthors_passes_when_different():
    client = MagicMock()
    client.primary_verified_email.return_value = "sam@example.com"
    out = coauthored.validate_coauthors(client, ["Ada <ada@example.org>"])
    assert out == ["Ada <ada@example.org>"]


def test_validate_coauthors_no_email_check_when_unverified():
    """If we can't fetch the actor's email, we should not block."""
    client = MagicMock()
    client.primary_verified_email.return_value = None
    out = coauthored.validate_coauthors(client, ["Ada <ada@example.org>"])
    assert out == ["Ada <ada@example.org>"]
