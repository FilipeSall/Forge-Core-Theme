#!/usr/bin/env python3
"""Restore Material Icon Theme manifests changed by apply-vscode-folder-icons.py."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path


VSCODE_EXTENSIONS = Path.home() / ".vscode" / "extensions"
BACKUP_ROOT = Path.home() / ".local" / "share" / "forge-core" / "backups" / "vscode-material-icon-theme"
PREFIX = "forge-core-"


def main() -> None:
    restored = 0
    for theme_dir in sorted(path for path in VSCODE_EXTENSIONS.glob("pkief.material-icon-theme-*") if path.is_dir()):
        backup = BACKUP_ROOT / theme_dir.name / "material-icons.json"
        manifest = theme_dir / "dist" / "material-icons.json"
        if not backup.is_file():
            continue
        shutil.copy2(backup, manifest)
        for icon in (theme_dir / "icons").glob(f"{PREFIX}*.png"):
            icon.unlink()
        restored += 1
        print(f"restaurado: {theme_dir}")
    if not restored:
        print("Nenhuma sobreposicao Forge Core encontrada.")
    else:
        print("Concluido. No VS Code, execute 'Developer: Reload Window'.")


if __name__ == "__main__":
    main()
