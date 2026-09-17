"""Serialize the Forge Core folder-icon writers across processes."""

from __future__ import annotations

import fcntl
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


DATA_HOME = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share")
STATE_DIR = DATA_HOME / "forge-core"
FOLDER_ICONS_LOCK = STATE_DIR / "folder-icons.lock"

_depth = 0
_handle = None


@contextmanager
def folder_icons_lock(path: Path = FOLDER_ICONS_LOCK) -> Iterator[None]:
    """Serialize thumbnail/metadata reconciliation between Forge processes.

    Re-entrant: ``flock`` is tied to the open file description, so a nested
    call in the same process would otherwise deadlock against itself.
    """
    global _depth, _handle

    if _depth:
        _depth += 1
        try:
            yield
        finally:
            _depth -= 1
        return

    path.parent.mkdir(parents=True, exist_ok=True)
    _handle = path.open("a+", encoding="utf-8")
    try:
        fcntl.flock(_handle.fileno(), fcntl.LOCK_EX)
        _depth = 1
        try:
            yield
        finally:
            _depth = 0
            fcntl.flock(_handle.fileno(), fcntl.LOCK_UN)
    finally:
        _handle.close()
        _handle = None
