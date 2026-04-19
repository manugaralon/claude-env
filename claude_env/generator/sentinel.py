"""Sentinel merge utility for safe idempotent file updates.

Managed blocks are wrapped with sentinel markers so that re-runs replace only
the managed section while preserving user content before and after it.
"""
from __future__ import annotations

_BEGIN = "# BEGIN CLAUDE-ENV MANAGED"
_END = "# END CLAUDE-ENV MANAGED"

SENTINEL_HEADER = f"{_BEGIN} — do not edit this block manually\n"
SENTINEL_FOOTER = f"{_END}\n"


def wrap_with_sentinel(content: str) -> str:
    """Wrap *content* between the sentinel header and footer."""
    return f"{SENTINEL_HEADER}{content}\n{SENTINEL_FOOTER}"


def has_sentinel(content: str) -> bool:
    """Return True if *content* contains both BEGIN and END sentinel markers."""
    return _BEGIN in content and _END in content


def merge_sentinel_block(existing: str, new_managed_content: str) -> str:
    """Merge *new_managed_content* into *existing*, respecting sentinel markers.

    - If *existing* contains a sentinel block, replace it in-place, preserving
      any content before and after the block.
    - If *existing* has no sentinel block, append the new block after the
      existing content.
    """
    wrapped = wrap_with_sentinel(new_managed_content)

    if not has_sentinel(existing):
        return existing.rstrip("\n") + "\n\n" + wrapped

    begin_idx = existing.index(_BEGIN)
    end_idx = existing.index(_END)
    # Find the newline that terminates the END line
    newline_after_end = existing.find("\n", end_idx)
    if newline_after_end == -1:
        end_of_block = len(existing)
    else:
        end_of_block = newline_after_end + 1

    before = existing[:begin_idx]
    after = existing[end_of_block:]

    return before + wrapped + after
