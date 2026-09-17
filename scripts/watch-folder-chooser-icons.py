#!/usr/bin/env python3
"""Keep GTK folder-chooser thumbnails synchronized with the active icon theme."""

from __future__ import annotations

import os
import select
import subprocess
import sys
from pathlib import Path

import browser_icons
import folder_chooser_icons as icons


DEBOUNCE_SECONDS = 2.0
TERMINATE_TIMEOUT = 5


def reconcile(depth: int, purge: bool = False) -> None:
    if purge:
        icons.purge_asset_caches()
    try:
        browser_icons.reconcile_for_theme()
    except OSError as error:
        print(f"aviso: overrides de launcher nao reconciliados: {error}")
    if icons.forge_core_active():
        icons.apply([Path.home()], depth, False, None)
        # A theme change during the scan must not leave Forge thumbnails behind.
        if not icons.forge_core_active():
            icons.deactivate()
    else:
        icons.deactivate()


def watch(monitor: subprocess.Popen, depth: int) -> None:
    """Reconcile once per burst of icon-theme changes."""
    assert monitor.stdout is not None
    descriptor = monitor.stdout.fileno()
    pending = False

    while True:
        timeout = DEBOUNCE_SECONDS if pending else None
        readable, _, _ = select.select([descriptor], [], [], timeout)

        if readable:
            try:
                chunk = os.read(descriptor, 4096)
            except OSError:
                return
            if not chunk:
                return
            if chunk.strip():
                pending = True
            continue

        if pending:
            pending = False
            reconcile(depth, purge=True)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--depth", type=int, default=icons.DEFAULT_DEPTH)
    args = parser.parse_args()
    if args.depth < 1:
        parser.error("--depth deve ser maior que zero")

    reconcile(args.depth)
    monitor = subprocess.Popen(
        ["gsettings", "monitor", icons.ICON_THEME_SCHEMA, "icon-theme"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    try:
        watch(monitor, args.depth)
    finally:
        monitor.terminate()
        try:
            monitor.wait(timeout=TERMINATE_TIMEOUT)
        except subprocess.TimeoutExpired:
            monitor.kill()
            monitor.wait()

    raise SystemExit("gsettings monitor encerrou; reiniciando")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
