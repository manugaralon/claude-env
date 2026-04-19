"""Tests for sentinel merge module."""
from __future__ import annotations

import pytest

from claude_env.generator.sentinel import (
    has_sentinel,
    merge_sentinel_block,
    wrap_with_sentinel,
)

_BEGIN = "# BEGIN CLAUDE-ENV MANAGED"
_END = "# END CLAUDE-ENV MANAGED"


def test_wrap_with_sentinel_format() -> None:
    result = wrap_with_sentinel("hello")
    assert result.startswith(f"{_BEGIN} — do not edit this block manually\n")
    assert "hello" in result
    assert result.rstrip("\n").endswith(_END)


def test_has_sentinel_true() -> None:
    wrapped = wrap_with_sentinel("some content")
    assert has_sentinel(wrapped) is True


def test_has_sentinel_false() -> None:
    assert has_sentinel("plain text without markers") is False


def test_has_sentinel_partial() -> None:
    # Only BEGIN without END — should return False
    assert has_sentinel(f"{_BEGIN}\nsome content") is False


def test_merge_replaces_existing_block() -> None:
    old_managed = wrap_with_sentinel("old managed content")
    existing = "user header\n" + old_managed + "user footer\n"
    result = merge_sentinel_block(existing, "new managed content")
    assert "user header" in result
    assert "user footer" in result
    assert "old managed content" not in result
    assert "new managed content" in result


def test_merge_appends_when_no_block() -> None:
    existing = "just user content"
    result = merge_sentinel_block(existing, "managed block content")
    assert "just user content" in result
    assert "managed block content" in result
    assert has_sentinel(result) is True


def test_merge_idempotent() -> None:
    existing = "user preamble\n"
    content = "managed content"
    first = merge_sentinel_block(existing, content)
    second = merge_sentinel_block(first, content)
    assert first == second


def test_merge_preserves_user_edits_outside_block() -> None:
    # Simulate first merge: managed block appended
    existing = "initial content\n"
    first_merge = merge_sentinel_block(existing, "managed v1")
    # User adds content after the managed block
    user_addition = "\n# User added this after the block\n"
    with_user_edit = first_merge + user_addition
    # Re-merge with new managed content
    result = merge_sentinel_block(with_user_edit, "managed v2")
    assert "initial content" in result
    assert "# User added this after the block" in result
    assert "managed v2" in result
    assert "managed v1" not in result
