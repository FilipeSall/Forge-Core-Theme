#!/usr/bin/env python3
"""Watch application directories and refresh Forge Core launcher overrides."""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import browser_icons as icons


DEFAULT_INTERVAL = 2.0


def watch_roots() -> tuple[Path, ...]:
    """Return existing and future application roots without creating any."""
    return (icons.APPLICATIONS, *icons.SYSTEM_APPLICATION_ROOTS)


def snapshot(roots: tuple[Path, ...]) -> dict[str, tuple[int, int, int]]:
    """Capture desktop-file identity, size, and nanosecond mtime."""
    result: dict[str, tuple[int, int, int]] = {}
    for root in roots:
        if not root.is_dir():
            continue
        try:
            entries = root.glob("*.desktop")
        except OSError:
            continue
        for path in entries:
            try:
                stat = path.stat()
            except OSError:
                continue
            result[str(path)] = (stat.st_ino, stat.st_size, stat.st_mtime_ns)
    return result


def reconcile() -> None:
    changed = icons.apply(icons.APPLICATIONS, icons.SYSTEM_APPLICATION_ROOTS)
    if changed:
        icons.refresh_active_icon_theme()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--interval", type=float, default=DEFAULT_INTERVAL)
    args = parser.parse_args()
    if args.interval <= 0:
        raise SystemExit("--interval deve ser maior que zero")

    roots = watch_roots()
    print("watcher Forge Core ativo", flush=True)
    reconcile()
    previous = snapshot(roots)
    while True:
        time.sleep(args.interval)
        current = snapshot(roots)
        if current == previous:
            continue
        reconcile()
        previous = snapshot(roots)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("watcher Forge Core encerrado", flush=True)
