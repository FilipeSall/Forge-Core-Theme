"""Keep the system cursor inside Google Chrome while Forge-Core-Cursor stays active elsewhere.

Chrome on X11 resolves cursors by the GTK theme name and ignores XCURSOR_THEME,
but honours XCURSOR_PATH. Its launchers get a path without the user icon
directories, where a ``default`` theme inherits the cursor theme used before
Forge Core.
"""

from __future__ import annotations

import os
import shutil
import stat
import sys
import tempfile
from pathlib import Path


APPLICATIONS = Path.home() / ".local" / "share" / "applications"
SYSTEM_APPLICATIONS = Path("/usr/share/applications")
SYSTEM_LAUNCHERS = ("google-chrome.desktop", "com.google.Chrome.desktop")
STATE_DIR = Path.home() / ".local" / "share" / "forge-core"
CURSOR_PATH_ROOT = STATE_DIR / "browser-cursors"
DEFAULT_THEME_INDEX = CURSOR_PATH_ROOT / "default" / "index.theme"
PREVIOUS_THEME_FILE = STATE_DIR / "previous-cursor-theme"
SYSTEM_ICONS = Path("/usr/share/icons")
FORGE_THEME = "Forge-Core-Cursor"
FALLBACK_THEME = "Yaru"
EXEC_PREFIX = f"Exec=env XCURSOR_PATH={CURSOR_PATH_ROOT}:{SYSTEM_ICONS}:/usr/share/pixmaps "
COPIED_MARKER = "X-Forge-Core-Browser-Cursors=copied"


def abort(message: str) -> None:
    print(f"erro: {message}", file=sys.stderr)
    raise SystemExit(1)


def is_regular_file(path: Path) -> bool:
    try:
        return not path.is_symlink() and path.is_file() and stat.S_ISREG(path.stat().st_mode)
    except OSError:
        return False


def atomic_write(path: Path, content: str) -> None:
    """Write a launcher atomically, refusing to follow a symlink."""
    if path.is_symlink():
        raise OSError(f"recusado escrever em symlink: {path}")
    mode = stat.S_IMODE(path.stat().st_mode) if is_regular_file(path) else 0o644
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def entry_index(lines: list[str]) -> int | None:
    for index, line in enumerate(lines):
        if line.strip() == "[Desktop Entry]":
            return index
    return None


def system_theme() -> str:
    theme = PREVIOUS_THEME_FILE.read_text(encoding="utf-8").strip() if PREVIOUS_THEME_FILE.is_file() else ""
    if theme and theme != FORGE_THEME and (SYSTEM_ICONS / theme).is_dir():
        return theme
    return FALLBACK_THEME


def is_chrome_exec(line: str) -> bool:
    return line.startswith("Exec=") and "google-chrome" in line


def chrome_launchers() -> list[Path]:
    found: list[Path] = []
    for path in APPLICATIONS.glob("*.desktop"):
        if not is_regular_file(path):
            continue
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError):
            continue
        if any(is_chrome_exec(line) for line in lines):
            found.append(path)
    return sorted(found)


def copy_system_launchers() -> None:
    for name in SYSTEM_LAUNCHERS:
        source = SYSTEM_APPLICATIONS / name
        target = APPLICATIONS / name
        if not is_regular_file(source) or target.exists() or target.is_symlink():
            continue
        lines = source.read_text(encoding="utf-8").splitlines(keepends=True)
        index = entry_index(lines)
        if index is None:
            print(f"ignorado: {source} sem [Desktop Entry]", file=sys.stderr)
            continue
        lines.insert(index + 1, f"{COPIED_MARKER}\n")
        atomic_write(target, "".join(lines))
        print(f"copiado: {source} -> {target}")


def patch_launcher(path: Path, add: bool) -> bool:
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    changed = False
    for index, line in enumerate(lines):
        if add and is_chrome_exec(line) and not line.startswith(EXEC_PREFIX):
            lines[index] = EXEC_PREFIX + line[len("Exec="):]
            changed = True
        elif not add and line.startswith(EXEC_PREFIX):
            lines[index] = "Exec=" + line[len(EXEC_PREFIX):]
            changed = True
    if changed:
        atomic_write(path, "".join(lines))
    return changed


def apply() -> None:
    theme = system_theme()
    APPLICATIONS.mkdir(parents=True, exist_ok=True)
    copy_system_launchers()
    launchers = chrome_launchers()
    if not launchers:
        abort("nenhum atalho do Google Chrome encontrado")
    DEFAULT_THEME_INDEX.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_THEME_INDEX.write_text(f"[Icon Theme]\nName=Default\nInherits={theme}\n", encoding="utf-8")
    for launcher in launchers:
        print(f"{'aplicado' if patch_launcher(launcher, True) else 'ja aplicado'}: {launcher}")
    print(f"Concluido. Cursor do Chrome: {theme}. Feche o Chrome por completo (Ctrl+Shift+Q) e abra de novo.")


def restore() -> None:
    restored = 0
    for launcher in chrome_launchers():
        if COPIED_MARKER in launcher.read_text(encoding="utf-8").splitlines():
            launcher.unlink()
            print(f"removido: {launcher}")
            restored += 1
        elif patch_launcher(launcher, False):
            print(f"restaurado: {launcher}")
            restored += 1
    if CURSOR_PATH_ROOT.is_dir():
        shutil.rmtree(CURSOR_PATH_ROOT)
    if not restored:
        print("Nenhum atalho do Chrome com a excecao de cursor encontrado.")
    else:
        print("Concluido. Feche o Chrome por completo (Ctrl+Shift+Q) e abra de novo.")
