#!/usr/bin/env python3
"""Apply Forge Core folder assets to the installed Material Icon Theme.

VS Code does not use GVfs/Nautilus ``metadata::custom-icon`` values.  Its
Explorer renders its own icon theme, so this script makes a minimal,
reversible overlay in the user's installed Material Icon Theme.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE_DIR = REPO_ROOT / "assets" / "icons" / "folders"
VSCODE_EXTENSIONS = Path.home() / ".vscode" / "extensions"
BACKUP_ROOT = Path.home() / ".local" / "share" / "forge-core" / "backups" / "vscode-material-icon-theme"
ASSETS = {
    ".claude": "claude.png",
    ".codex": "codex.png",
    ".gemini": "gemini.png",
}
PREFIX = "forge-core-"


def abort(message: str) -> None:
    print(f"erro: {message}", file=sys.stderr)
    raise SystemExit(1)


def theme_directories() -> list[Path]:
    return sorted(path for path in VSCODE_EXTENSIONS.glob("pkief.material-icon-theme-*") if path.is_dir())


def patch_theme(theme_dir: Path) -> None:
    manifest = theme_dir / "dist" / "material-icons.json"
    icons_dir = theme_dir / "icons"
    if not manifest.is_file() or not icons_dir.is_dir():
        print(f"ignorado: estrutura inesperada em {theme_dir}")
        return

    backup = BACKUP_ROOT / theme_dir.name / "material-icons.json"
    backup.parent.mkdir(parents=True, exist_ok=True)
    if not backup.exists():
        shutil.copy2(manifest, backup)
        print(f"backup: {backup}")

    data = json.loads(manifest.read_text(encoding="utf-8"))
    definitions = data.setdefault("iconDefinitions", {})
    closed = data.setdefault("folderNames", {})
    opened = data.setdefault("folderNamesExpanded", {})

    for folder_name, filename in ASSETS.items():
        source = SOURCE_DIR / filename
        if not source.is_file():
            abort(f"asset ausente: {source}")
        icon_name = f"{PREFIX}{folder_name[1:]}"
        destination = icons_dir / f"{icon_name}.png"
        shutil.copy2(source, destination)
        definitions[icon_name] = {"iconPath": f"./../icons/{destination.name}"}
        closed[folder_name] = icon_name
        opened[folder_name] = icon_name

    manifest.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"aplicado: {theme_dir}")


def main() -> None:
    if not SOURCE_DIR.is_dir():
        abort(f"assets Forge Core nao encontrados: {SOURCE_DIR}")
    themes = theme_directories()
    if not themes:
        abort("Material Icon Theme nao esta instalado no VS Code deste usuario")
    for theme in themes:
        patch_theme(theme)
    print("Concluido. No VS Code, execute 'Developer: Reload Window' para recarregar os icones.")


if __name__ == "__main__":
    main()
