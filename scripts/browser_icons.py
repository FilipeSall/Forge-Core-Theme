"""Manage Forge Core overrides for launchers with absolute icons."""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
import shlex
import shutil
import stat
import subprocess
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


DATA_HOME = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
APPLICATIONS = DATA_HOME / "applications"
HICOLOR = DATA_HOME / "icons" / "hicolor"
SYSTEM_HICOLOR_INDEX = Path("/usr/share/icons/hicolor/index.theme")
STANDARD_SIZES = (16, 22, 24, 32, 48, 64, 96, 128, 256, 512)
STATE_DIR = DATA_HOME / "forge-core"
STATE_FILE = STATE_DIR / "browser-icon-overrides.json"
LOCK_FILE = STATE_DIR / "browser-icon-overrides.lock"
OVERRIDE_MARKER = "X-Forge-Core-Icon-Overrides=desktop-launcher"
LEGACY_OVERRIDE_MARKERS = {
    "X-Forge-Core-Icon-Overrides=browser",
    OVERRIDE_MARKER,
}
THEME_NAME = "Forge-Core"

MANAGED_ICONS = {
    "firefox": "firefox",
    "brave": "brave",
    "safari": "safari",
    "app-center": "snap-store_snap-store",
    "beekeeper-studio": "beekeeper-studio",
    "filezilla": "filezilla",
    "hubstaff": "hubstaff",
    "orca-stably": "orca-stably",
    "postman": "postman",
}

MANAGED_DESKTOP_IDS = {
    "firefox": {
        "firefox.desktop",
        "firefox_firefox.desktop",
        "firefox-esr.desktop",
        "org.mozilla.firefox.desktop",
        "org.mozilla.Firefox.desktop",
    },
    "brave": {
        "brave.desktop",
        "brave-browser.desktop",
        "brave_brave.desktop",
        "com.brave.Browser.desktop",
    },
    "safari": {
        "safari.desktop",
        "safari-browser.desktop",
        "com.apple.Safari.desktop",
    },
    "app-center": {
        "snap-store_snap-store.desktop",
        "snap-store_show-updates.desktop",
        "snap-store_packagekit-session-installer.desktop",
    },
    "beekeeper-studio": {
        "beekeeper-studio_beekeeper-studio.desktop",
        "beekeeper-studio.desktop",
    },
    "filezilla": {
        "filezilla.desktop",
        "org.filezillaproject.Filezilla.desktop",
    },
    "hubstaff": {
        "netsoft-com.netsoft.hubstaff.desktop",
        "hubstaff.desktop",
    },
    "orca-stably": {
        "orca-stably.desktop",
    },
    "postman": {
        "postman_postman.desktop",
        "postman.desktop",
    },
}


def xdg_data_dirs() -> tuple[Path, ...]:
    raw = os.environ.get("XDG_DATA_DIRS", "/usr/local/share:/usr/share")
    return tuple(Path(entry) for entry in raw.split(":") if entry)


def unique_paths(paths: list[Path]) -> tuple[Path, ...]:
    return tuple(dict.fromkeys(paths))


SYSTEM_APPLICATION_ROOTS = unique_paths(
    [
        *(data_dir / "applications" for data_dir in xdg_data_dirs()),
        Path("/var/lib/snapd/desktop/applications"),
        Path("/var/lib/flatpak/exports/share/applications"),
        DATA_HOME / "flatpak" / "exports" / "share" / "applications",
    ]
)


def read_lines(path: Path) -> list[str]:
    """Read a desktop entry while preserving line endings."""
    return path.read_text(encoding="utf-8").splitlines(keepends=True)


def is_regular_file(path: Path) -> bool:
    try:
        return not path.is_symlink() and path.is_file() and stat.S_ISREG(path.stat().st_mode)
    except OSError:
        return False


def main_section(lines: list[str]) -> list[tuple[int, str]]:
    """Return lines belonging to the primary Desktop Entry group."""
    result: list[tuple[int, str]] = []
    in_main = False
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            in_main = stripped == "[Desktop Entry]"
        elif in_main:
            result.append((index, line))
    return result


def desktop_value(lines: list[str], key: str) -> str:
    """Return the unlocalized value of a key in the main desktop group."""
    prefix = f"{key}="
    for _, line in main_section(lines):
        if line.startswith(prefix):
            return line[len(prefix):].strip()
    return ""


def managed_icon(lines: list[str], filename: str = "") -> str | None:
    """Resolve the Forge icon name for a managed desktop entry."""
    if not any(line.strip() == "[Desktop Entry]" for line in lines):
        return None

    filename = Path(filename).name
    for app, desktop_ids in MANAGED_DESKTOP_IDS.items():
        if filename in desktop_ids:
            return MANAGED_ICONS[app]

    name = re.sub(r"[^a-z0-9]+", " ", desktop_value(lines, "Name").lower()).strip()
    known_names = {
        "firefox": "firefox",
        "mozilla firefox": "firefox",
        "firefox esr": "firefox",
        "brave": "brave",
        "brave browser": "brave",
        "safari": "safari",
        "safari browser": "safari",
        "app center": "snap-store_snap-store",
        "app center updates": "snap-store_snap-store",
    }
    if name in known_names:
        return known_names[name]

    executable_names = {
        "firefox": "firefox",
        "firefox-esr": "firefox",
        "brave": "brave",
        "brave-browser": "brave",
        "safari": "safari",
        "safari-browser": "safari",
        "snap-store": "snap-store_snap-store",
        "show-updates": "snap-store_snap-store",
        "packagekit-session-installer": "snap-store_snap-store",
    }
    for key in ("Exec", "TryExec"):
        try:
            tokens = shlex.split(desktop_value(lines, key))
        except ValueError:
            tokens = []
        for token in tokens:
            executable = Path(token).name.lower()
            if executable in executable_names:
                return executable_names[executable]

    for key in ("X-SnapAppName", "X-SnapInstanceName"):
        value = re.sub(r"[^a-z0-9]+", " ", desktop_value(lines, key).lower()).strip()
        for app in MANAGED_ICONS:
            if value == app:
                return MANAGED_ICONS[app]
        if value in {"snap store", "show updates", "packagekit session installer"}:
            return "snap-store_snap-store"

    flatpak_id = desktop_value(lines, "X-Flatpak").strip()
    for app, desktop_ids in MANAGED_DESKTOP_IDS.items():
        if f"{flatpak_id}.desktop" in desktop_ids:
            return MANAGED_ICONS[app]
    return None


def browser_icon(lines: list[str], filename: str = "") -> str | None:
    """Backward-compatible alias for callers using the old browser name."""
    return managed_icon(lines, filename)


def icon_value_index(lines: list[str]) -> int | None:
    """Find the main desktop-entry Icon line, excluding action groups."""
    for index, line in main_section(lines):
        if line.startswith("Icon="):
            return index
    return None


def has_marker(lines: list[str]) -> bool:
    return any(line.strip() in LEGACY_OVERRIDE_MARKERS for line in lines)


def patch_icon(lines: list[str], icon_name: str) -> tuple[list[str], bool]:
    """Replace an absolute icon path with a Forge Core icon name."""
    index = icon_value_index(lines)
    if index is None:
        return lines, False
    current = lines[index][len("Icon="):].strip()
    if current == icon_name or not current.startswith("/"):
        return lines, False
    newline = "\n" if lines[index].endswith("\n") else ""
    lines[index] = f"Icon={icon_name}{newline}"
    return lines, True


def add_marker(lines: list[str]) -> list[str]:
    """Mark a generated user-local desktop override."""
    if has_marker(lines):
        return lines
    entry_index = next(index for index, line in enumerate(lines) if line.strip() == "[Desktop Entry]")
    lines.insert(entry_index + 1, f"{OVERRIDE_MARKER}\n")
    return lines


def candidate_groups(
    applications: Path = APPLICATIONS,
    system_roots: tuple[Path, ...] = SYSTEM_APPLICATION_ROOTS,
) -> dict[str, list[Path]]:
    """Group managed launchers by basename, preserving XDG priority."""
    groups: dict[str, list[Path]] = {}
    for root in (applications, *system_roots):
        if not root.is_dir():
            continue
        for path in sorted(root.glob("*.desktop")):
            if not is_regular_file(path):
                continue
            try:
                lines = read_lines(path)
            except (OSError, UnicodeDecodeError):
                continue
            if managed_icon(lines, path.name) is None or icon_value_index(lines) is None:
                continue
            groups.setdefault(path.name, []).append(path)
    return groups


def desktop_candidates(
    applications: Path = APPLICATIONS,
    system_roots: tuple[Path, ...] = SYSTEM_APPLICATION_ROOTS,
) -> list[Path]:
    """Find browser launchers, preferring the user copy for each basename."""
    return [paths[0] for paths in candidate_groups(applications, system_roots).values()]


def update_desktop_database(applications: Path = APPLICATIONS) -> None:
    """Refresh the user desktop-entry cache when the utility is available."""
    executable = shutil.which("update-desktop-database")
    if executable:
        subprocess.run(
            [executable, str(applications)],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


def ensure_hicolor_index() -> None:
    """A user hicolor tree without index.theme is ignored by GTK."""
    index = HICOLOR / "index.theme"
    if index.is_file():
        return
    HICOLOR.mkdir(parents=True, exist_ok=True)
    if SYSTEM_HICOLOR_INDEX.is_file():
        shutil.copyfile(SYSTEM_HICOLOR_INDEX, index)
        return
    directories = ",".join(f"{size}x{size}/apps" for size in STANDARD_SIZES)
    body = [f"[Icon Theme]\nName=Hicolor\nComment=Fallback\nDirectories={directories}\n"]
    for size in STANDARD_SIZES:
        body.append(f"\n[{size}x{size}/apps]\nSize={size}\nContext=Applications\nType=Threshold\n")
    index.write_text("".join(body), encoding="utf-8")


def icon_size_dir(source: Path) -> str:
    """Pick the standard hicolor directory closest to the artwork size."""
    try:
        from PIL import Image

        with Image.open(source) as image:
            largest = max(image.size)
    except Exception:
        largest = 256
    return min(STANDARD_SIZES, key=lambda size: abs(size - largest))


def install_icon_fallback(name: str, source: Path) -> str | None:
    """Publish the launcher's own artwork under ``name`` in the user hicolor tree.

    Keeps the Forge icon name resolvable under every theme, so the launcher
    never has to be rewritten when the theme changes.
    """
    if not is_regular_file(source) or source.suffix.lower() != ".png":
        return None
    ensure_hicolor_index()
    size = icon_size_dir(source)
    target = HICOLOR / f"{size}x{size}" / "apps" / f"{name}.png"
    if is_regular_file(target) and file_digest(target) == file_digest(source):
        return str(target)
    atomic_copy(source, target)
    return str(target)


@contextmanager
def state_lock() -> Iterator[None]:
    """Serialize apply/restore between installer, uninstall, and watcher."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with LOCK_FILE.open("a+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def load_state() -> dict[str, object]:
    """Load prior overrides, including state written by the previous version."""
    empty: dict[str, object] = {"created": [], "backups": {}, "managed": {}, "fallbacks": {}}
    if not STATE_FILE.is_file():
        return empty
    try:
        state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return empty
    if not isinstance(state, dict):
        return empty
    created = state.get("created")
    backups = state.get("backups")
    managed = state.get("managed")
    fallbacks = state.get("fallbacks")
    return {
        "created": created if isinstance(created, list) else [],
        "backups": backups if isinstance(backups, dict) else {},
        "managed": managed if isinstance(managed, dict) else {},
        "fallbacks": fallbacks if isinstance(fallbacks, dict) else {},
    }


def atomic_write(path: Path, content: str, mode: int | None = None) -> None:
    """Write a regular user file atomically without following a symlink."""
    if path.is_symlink():
        raise OSError(f"recusado escrever em symlink: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    if mode is None and is_regular_file(path):
        mode = stat.S_IMODE(path.stat().st_mode)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        if mode is not None:
            os.chmod(temporary, mode)
        os.replace(temporary, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        temporary.unlink(missing_ok=True)


def atomic_copy(source: Path, target: Path) -> None:
    """Copy a regular file atomically while preserving metadata."""
    if not is_regular_file(source) or target.is_symlink():
        raise OSError(f"arquivo inseguro para copia: {source} -> {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{target.name}.", dir=target.parent)
    temporary = Path(temporary_name)
    os.close(descriptor)
    try:
        shutil.copy2(source, temporary)
        os.replace(temporary, target)
        directory_fd = os.open(target.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        temporary.unlink(missing_ok=True)


def save_state(state: dict[str, object]) -> None:
    """Persist state atomically; callers hold state_lock()."""
    save_content = json.dumps(state, indent=2) + "\n"
    atomic_write(STATE_FILE, save_content, mode=0o600)


def file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def backup_path(target: Path) -> Path:
    destination = STATE_DIR / "browser-icon-backups" / target.name
    destination.parent.mkdir(parents=True, exist_ok=True)
    return destination


def valid_target_path(path: Path, applications: Path = APPLICATIONS) -> bool:
    return path.parent == applications and path.name.endswith(".desktop")


def valid_backup_path(path: Path) -> bool:
    return path.parent == STATE_DIR / "browser-icon-backups" and path.name.endswith(".desktop")


def remove_stale_created_overrides(
    state: dict[str, object],
    groups: dict[str, list[Path]],
    applications: Path,
) -> int:
    """Remove generated overrides whose installed system launcher disappeared."""
    created = state["created"]
    managed = state["managed"]
    assert isinstance(created, list)
    assert isinstance(managed, dict)
    active_basenames = {
        basename
        for basename, paths in groups.items()
        if any(path.parent != applications for path in paths)
    }
    removed = 0
    remaining: list[str] = []
    for path_name in created:
        path = Path(path_name)
        if not valid_target_path(path, applications):
            print(f"aviso: estado aponta para destino inseguro, ignorado: {path}")
            remaining.append(path_name)
            continue
        if path.name in active_basenames:
            remaining.append(path_name)
            continue
        if not is_regular_file(path):
            if path.is_symlink():
                print(f"aviso: override symlink mantido: {path}")
                remaining.append(path_name)
            else:
                managed.pop(path_name, None)
            continue
        try:
            lines = read_lines(path)
        except (OSError, UnicodeDecodeError):
            remaining.append(path_name)
            continue
        if not has_marker(lines):
            remaining.append(path_name)
            continue
        expected = managed.get(path_name)
        if expected and file_digest(path) != expected:
            print(f"aviso: override alterado pelo usuario, mantido: {path}")
            remaining.append(path_name)
            continue
        path.unlink()
        managed.pop(path_name, None)
        removed += 1
        print(f"removido override orfao: {path}")
    if remaining != created:
        state["created"] = remaining
    return removed


def _apply(
    applications: Path,
    system_roots: tuple[Path, ...],
) -> int:
    applications.mkdir(parents=True, exist_ok=True)
    state = load_state()
    created = state["created"]
    backups = state["backups"]
    managed = state["managed"]
    fallbacks = state["fallbacks"]
    assert isinstance(created, list)
    assert isinstance(backups, dict)
    assert isinstance(managed, dict)
    assert isinstance(fallbacks, dict)
    groups = candidate_groups(applications, system_roots)
    removed = remove_stale_created_overrides(state, groups, applications)
    if removed:
        groups = candidate_groups(applications, system_roots)
    applied = 0
    state_dirty = removed > 0

    for basename, paths in groups.items():
        source = paths[0]
        source_lines = read_lines(source)
        icon_name = managed_icon(source_lines, basename)
        if icon_name is None:
            continue
        target = source if source.parent == applications else applications / basename
        if target.is_symlink():
            print(f"aviso: override symlink recusado: {target}")
            continue
        if target.exists() and not is_regular_file(target):
            print(f"aviso: destino nao e arquivo regular, mantido: {target}")
            continue
        target_exists = is_regular_file(target)
        target_lines = read_lines(target) if target_exists else source_lines.copy()
        original_lines = target_lines.copy()
        previous_icon = ""
        index = icon_value_index(target_lines)
        if index is not None:
            previous_icon = target_lines[index][len("Icon="):].strip()
        target_lines, changed = patch_icon(target_lines, icon_name)

        if changed and previous_icon.startswith("/"):
            fallback = install_icon_fallback(icon_name, Path(previous_icon))
            if fallback:
                fallbacks[icon_name] = fallback
                print(f"fallback publicado: {icon_name} -> {fallback}")

        if not changed:
            if target_exists and has_marker(original_lines) and str(target) not in managed:
                managed[str(target)] = file_digest(target)
                state_dirty = True
            continue

        target_had_marker = has_marker(original_lines)
        if target_exists and not target_had_marker:
            backup = backup_path(target)
            if str(target) not in backups:
                if backup.exists() or backup.is_symlink():
                    print(f"aviso: backup existente sem estado, launcher mantido: {target}")
                    continue
                atomic_copy(target, backup)
                backups[str(target)] = str(backup)
        if not target_exists and str(target) not in created:
            created.append(str(target))

        # Journal the backup/creation before changing the launcher itself.
        save_state(state)
        target_lines = add_marker(target_lines)
        atomic_write(target, "".join(target_lines))
        managed[str(target)] = file_digest(target)
        save_state(state)
        state_dirty = False
        applied += 1
        print(f"aplicado: {target} -> Icon={icon_name}")

    if state_dirty:
        save_state(state)
    if applied or removed:
        update_desktop_database(applications)
    if not applied and not removed:
        print("nenhum launcher gerenciado com Icon absoluto encontrado")
    return applied


def apply(
    applications: Path = APPLICATIONS,
    system_roots: tuple[Path, ...] = SYSTEM_APPLICATION_ROOTS,
) -> int:
    """Create or update user-local overrides for managed applications."""
    with state_lock():
        return _apply(applications, system_roots)


def reconcile_for_theme() -> int:
    """Keep launchers valid under every theme.

    The original artwork is published in the user hicolor tree under the same
    name, so the launcher stays untouched and GNOME resolves the icon through
    the active theme instead.
    """
    return apply()


def icon_theme_value() -> str:
    try:
        result = subprocess.run(
            ["gsettings", "get", "org.gnome.desktop.interface", "icon-theme"],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return ""
    return result.stdout.strip().strip("'\"")


def refresh_active_icon_theme() -> bool:
    """Refresh launcher icons without touching the user's icon-theme setting.

    Cycling ``icon-theme`` away from Forge Core and back would tear down and
    rebuild every folder override, so only the desktop database is refreshed.
    """
    if icon_theme_value() != THEME_NAME:
        return False
    update_desktop_database()
    return True


def refresh_gnome_shell() -> bool:
    """Reload the running GNOME Shell app system on an X11 session.

    GIO monitors desktop-file changes, but GNOME Shell can retain the old
    GFileIcon for an already loaded app.  X11 supports ``--replace``; Wayland
    deliberately does not, so the normal session restart remains the safe
    fallback there.
    """
    if os.environ.get("FORGE_CORE_ALLOW_GNOME_SHELL_REPLACE") != "1":
        print(
            "GNOME Shell nao recarregado automaticamente; use logout/login para atualizar"
        )
        return False
    if icon_theme_value() != THEME_NAME:
        return False
    if os.environ.get("XDG_SESSION_TYPE", "").lower() != "x11":
        print("GNOME Shell nao recarregado: sessao sem suporte a --replace")
        return False
    executable = shutil.which("gnome-shell")
    if not executable or not os.environ.get("DISPLAY"):
        print("GNOME Shell nao recarregado: gnome-shell ou DISPLAY ausente")
        return False
    try:
        subprocess.Popen(
            [executable, "--replace"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
            start_new_session=True,
        )
    except OSError as error:
        print(f"aviso: nao foi possivel recarregar o GNOME Shell: {error}")
        return False
    print("GNOME Shell recarregamento solicitado via --replace")
    return True


def _restore() -> None:
    """Restore user-local desktop entries; callers hold state_lock()."""
    if not STATE_FILE.is_file():
        print("nenhum override de ícone de launcher registrado")
        update_desktop_database()
        return

    state = load_state()
    created = state["created"]
    backups = state["backups"]
    managed = state["managed"]
    assert isinstance(created, list)
    assert isinstance(backups, dict)
    assert isinstance(managed, dict)
    remaining_created: list[str] = []
    remaining_backups: dict[str, str] = {}
    remaining_managed: dict[str, str] = {}

    for path_name in created:
        path = Path(path_name)
        if not valid_target_path(path, APPLICATIONS):
            print(f"aviso: destino inseguro no estado, mantido: {path}")
            remaining_created.append(path_name)
            continue
        if path.is_symlink():
            print(f"aviso: override symlink mantido: {path}")
            remaining_created.append(path_name)
            continue
        if not path.exists():
            continue
        if not is_regular_file(path):
            print(f"aviso: override nao regular mantido: {path}")
            remaining_created.append(path_name)
            continue
        try:
            lines = read_lines(path)
        except (OSError, UnicodeDecodeError):
            remaining_created.append(path_name)
            continue
        if not has_marker(lines):
            continue
        expected = managed.get(path_name)
        if expected and file_digest(path) != expected:
            print(f"aviso: override alterado pelo usuario, mantido: {path}")
            remaining_created.append(path_name)
            if isinstance(expected, str):
                remaining_managed[path_name] = expected
            continue
        path.unlink()
        print(f"removido: {path}")

    for path_name, backup_name in backups.items():
        path = Path(path_name)
        backup = Path(backup_name)
        if not valid_target_path(path, APPLICATIONS) or not valid_backup_path(backup):
            print(f"aviso: entrada de backup insegura, mantida: {path} <- {backup}")
            remaining_backups[path_name] = backup_name
            continue
        if backup.is_symlink() or not is_regular_file(backup):
            print(f"aviso: backup inseguro mantido: {backup}")
            remaining_backups[path_name] = backup_name
            continue
        if not path.exists():
            backup.unlink()
            print(f"backup descartado porque o launcher foi removido: {backup}")
            continue
        expected = managed.get(path_name)
        if path.is_symlink() or not is_regular_file(path):
            print(f"aviso: destino inseguro, backup mantido: {path}")
            remaining_backups[path_name] = backup_name
            continue
        if expected and file_digest(path) != expected:
            print(f"aviso: override alterado pelo usuario, backup mantido: {backup}")
            remaining_backups[path_name] = backup_name
            if isinstance(expected, str):
                remaining_managed[path_name] = expected
            continue
        atomic_copy(backup, path)
        backup.unlink()
        print(f"restaurado: {path}")

    if remaining_created or remaining_backups:
        state["created"] = remaining_created
        state["backups"] = remaining_backups
        state["managed"] = remaining_managed
        save_state(state)
    else:
        STATE_FILE.unlink(missing_ok=True)
    backup_dir = STATE_DIR / "browser-icon-backups"
    if backup_dir.is_dir() and not any(backup_dir.iterdir()):
        backup_dir.rmdir()
    update_desktop_database()


def restore() -> None:
    """Restore user-local desktop entries changed for Forge Core."""
    with state_lock():
        _restore()
