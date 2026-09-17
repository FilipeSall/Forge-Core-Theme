#!/usr/bin/env python3
"""Show GVfs folder icons in GTK/portal "Open Folder" dialogs via thumbnails."""

from __future__ import annotations

import argparse
from pathlib import Path

import folder_chooser_icons as icons


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("roots", nargs="*", type=Path, help="raizes da varredura (padrao: $HOME)")
    parser.add_argument("--depth", type=int, default=icons.DEFAULT_DEPTH, help="profundidade maxima")
    parser.add_argument("--dry-run", action="store_true", help="lista o que seria feito, sem gravar")
    parser.add_argument("--timer", action="store_true", help="instala timer systemd --user semanal")
    parser.add_argument(
        "--deactivate",
        action="store_true",
        help="remove as miniaturas geradas e o CSS do Forge Core",
    )
    args = parser.parse_args()

    if args.deactivate:
        if args.roots or args.dry_run or args.timer:
            parser.error("--deactivate nao pode ser combinado com raizes, --dry-run ou --timer")
        icons.deactivate()
        return

    roots = [root.expanduser().resolve() for root in args.roots] or [Path.home()]
    explicit_roots = [str(root) for root in roots] if args.roots else []
    timer_arguments = [*explicit_roots, "--depth", str(args.depth)] if args.timer else None
    icons.apply(roots, args.depth, args.dry_run, timer_arguments)


if __name__ == "__main__":
    main()
