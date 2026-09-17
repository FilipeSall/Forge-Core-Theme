#!/usr/bin/env python3
"""Apply Forge Core icon names to launchers that use absolute icon paths."""

import argparse

from browser_icons import apply, refresh_active_icon_theme


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="force a GNOME Shell icon-theme transition when Forge-Core is active",
    )
    args = parser.parse_args()
    apply()
    if args.refresh:
        refresh_active_icon_theme()
