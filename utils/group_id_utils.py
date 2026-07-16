"""Helpers for cross-platform group identifiers."""

from __future__ import annotations

import hashlib
import re
from typing import Any


_NUMERIC_ID_RE = re.compile(r"-?\d+")
_SAFE_FILENAME_RE = re.compile(r"[^A-Za-z0-9._-]")
_LEGACY_NUMERIC_GROUP_ID_RE = re.compile(r"-?\d+")


def normalize_group_id(group_id: Any) -> str:
    """Return a stable string group id accepted by all supported adapters.

    AstrBot adapters do not all expose pure numeric group ids. Some use
    unified origins such as ``adapter:GroupMessage:123456`` and some use
    platform-native ids such as ``xxx@chatroom``. Preserve the original id for
    display and API lookups, but trim surrounding whitespace.
    """
    if group_id is None:
        return ""
    return str(group_id).strip()


def is_valid_group_id(group_id: Any) -> bool:
    """Return whether ``group_id`` is usable as a non-empty group key."""
    return bool(normalize_group_id(group_id))


def normalize_user_id(user_id: Any) -> str:
    """Return a stable string user id accepted by all supported adapters."""
    return normalize_group_id(user_id)


def is_valid_user_id(user_id: Any) -> bool:
    """Return whether ``user_id`` is usable as a non-empty user key."""
    return bool(normalize_user_id(user_id))


def extract_numeric_group_id(group_id: Any) -> str:
    """Extract the last numeric id from compound origins when one exists."""
    group_id_str = normalize_group_id(group_id)
    matches = _NUMERIC_ID_RE.findall(group_id_str)
    return matches[-1] if matches else ""


def group_id_to_filename_stem(group_id: Any) -> str:
    """Convert any group id into a safe, deterministic JSON filename stem."""
    group_id_str = normalize_group_id(group_id)
    if not group_id_str:
        return "unknown"
    if _LEGACY_NUMERIC_GROUP_ID_RE.fullmatch(group_id_str):
        return group_id_str

    safe = _SAFE_FILENAME_RE.sub("_", group_id_str).strip("._ ")
    digest = hashlib.sha1(group_id_str.encode("utf-8")).hexdigest()[:10]

    if not safe:
        safe = "group"
    if len(safe) > 80:
        safe = safe[:80].rstrip("._-") or "group"

    return f"{safe}-{digest}"
