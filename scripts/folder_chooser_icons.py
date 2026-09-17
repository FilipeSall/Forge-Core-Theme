"""Expose GVfs ``metadata::custom-icon`` folder icons to GTK file choosers.

GtkFileChooser (GTK 3 and GTK 4, used by xdg-desktop-portal-gnome/-gtk and by
Electron apps) never reads ``metadata::custom-icon``, but renders the
freedesktop thumbnail (``thumbnail::path``) before ``standard::icon``. Each
folder with a custom icon gets a thumbnail; the metadata stays the source of truth.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import unquote, urlsplit

import gi

from forge_locks import folder_icons_lock

gi.require_version("GdkPixbuf", "2.0")
from gi.repository import GdkPixbuf, Gio, GLib


TAG = "forge-core-folder-chooser-icons"
ICON_THEME_SCHEMA = "org.gnome.desktop.interface"
FORGE_ICON_THEME = "Forge-Core"
THUMBNAIL_ROOT = Path(GLib.get_user_cache_dir()) / "thumbnails"
SIZES = {"large": 256, "normal": 128}
STATE_DIR = Path.home() / ".local" / "share" / "forge-core" / "folder-chooser-icons"
MANIFEST = STATE_DIR / "manifest.json"
BACKUP_ROOT = Path.home() / ".local" / "share" / "forge-core" / "backups" / "folder-chooser-icons"
SYSTEMD_DIR = Path.home() / ".config" / "systemd" / "user"
UNIT = "forge-core-folder-chooser-icons"
APPLY_SCRIPT = Path(__file__).resolve().parent / "apply-folder-chooser-icons.py"
WATCH_SCRIPT = Path(__file__).resolve().parent / "watch-folder-chooser-icons.py"
NAUTILUS_CSS_NAME = "forge-core-nautilus-thumbnails.css"
NAUTILUS_CSS_SOURCE = Path(__file__).resolve().parent.parent / "gtk-4.0" / NAUTILUS_CSS_NAME
GTK4_DIR = Path(GLib.get_user_config_dir()) / "gtk-4.0"
GTK4_CSS = GTK4_DIR / "gtk.css"
NAUTILUS_CSS_IMPORT = f'@import url("{NAUTILUS_CSS_NAME}");'
GTK4_BEGIN = "/* forge-core:begin */"
GTK4_END = "/* forge-core:end */"
NAUTILUS_BUS = "org.gnome.Nautilus"
NAUTILUS_WINDOW_PATH = "/org/gnome/Nautilus/window"
NAUTILUS_CALL_TIMEOUT_MS = 2000
DEFAULT_DEPTH = 6
SCAN_ATTRIBUTES = "standard::name,standard::type,metadata::custom-icon"
NO_DESCEND = {
    ".cache", ".cargo", ".config", ".git", ".gradle", ".local", ".m2", ".mozilla",
    ".npm", ".pnpm-store", ".rustup", ".var", ".vscode", "node_modules", "snap",
}


def abort(message: str) -> None:
    print(f"erro: {message}", file=sys.stderr)
    raise SystemExit(1)


def forge_core_active() -> bool:
    try:
        result = subprocess.run(
            ["gsettings", "get", ICON_THEME_SCHEMA, "icon-theme"],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return False
    return result.returncode == 0 and result.stdout.strip().strip("'\"") == FORGE_ICON_THEME


def png_text(path: Path) -> dict[str, str]:
    text: dict[str, str] = {}
    try:
        with path.open("rb") as handle:
            if handle.read(8) != b"\x89PNG\r\n\x1a\n":
                return text
            while header := handle.read(8):
                if len(header) < 8:
                    break
                length = int.from_bytes(header[:4], "big")
                if header[4:] in (b"IDAT", b"IEND"):
                    break
                if header[4:] == b"tEXt":
                    key, _, value = handle.read(length).partition(b"\0")
                    text[key.decode("latin-1")] = value.decode("latin-1")
                else:
                    handle.seek(length, os.SEEK_CUR)
                handle.seek(4, os.SEEK_CUR)
    except OSError:
        pass
    return text


def is_ours(path: Path) -> bool:
    return path.is_file() and png_text(path).get("Software") == TAG


def load_manifest() -> dict:
    empty: dict = {"version": 1, "folders": {}}
    if not MANIFEST.is_file():
        return empty
    try:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"aviso: manifesto invalido, recomecando: {error}", file=sys.stderr)
        return empty
    if not isinstance(manifest, dict) or not isinstance(manifest.get("folders"), dict):
        print("aviso: manifesto com formato inesperado, recomecando", file=sys.stderr)
        return empty
    return manifest


def save_manifest(manifest: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    temporary = MANIFEST.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, MANIFEST)


def custom_icon(file: Gio.File) -> str | None:
    try:
        info = file.query_info("metadata::custom-icon", Gio.FileQueryInfoFlags.NONE, None)
    except GLib.Error:
        return None
    return info.get_attribute_string("metadata::custom-icon")


def scan(root: Path, depth: int, found: dict[str, str]) -> None:
    try:
        children = Gio.File.new_for_path(str(root)).enumerate_children(
            SCAN_ATTRIBUTES, Gio.FileQueryInfoFlags.NOFOLLOW_SYMLINKS, None
        )
    except GLib.Error:
        return
    for info in children:
        if info.get_file_type() != Gio.FileType.DIRECTORY:
            continue
        child = root / info.get_name()
        icon = info.get_attribute_string("metadata::custom-icon")
        if icon:
            found[str(child)] = icon
        if depth > 1 and info.get_name() not in NO_DESCEND:
            scan(child, depth - 1, found)


def icon_path(uri: str) -> Path | None:
    candidates = [Gio.File.new_for_uri(uri).get_path()]
    parts = urlsplit(uri)
    if parts.scheme in ("", "file"):
        candidates.append(unquote(parts.path))
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return Path(candidate)
    return None


def thumbnail_name(folder: str) -> tuple[str, str]:
    uri = GLib.filename_to_uri(folder, None)
    return uri, hashlib.md5(uri.encode("utf-8")).hexdigest() + ".png"


def backup_foreign(target: Path) -> Path:
    destination = BACKUP_ROOT / time.strftime("%Y%m%d-%H%M%S") / target.parent.name / target.name
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(target, destination)
    print(f"backup: {target} -> {destination}")
    return destination


def thumbnails_current(folder: str, icon_uri: str, entry: dict) -> bool:
    """Report whether both thumbnails already match the folder and its icon."""
    if entry.get("icon") != icon_uri:
        return False
    try:
        uri, name = thumbnail_name(folder)
        mtime = str(int(os.stat(folder).st_mtime))
    except (OSError, GLib.Error):
        return False
    if entry.get("uri") != uri:
        return False
    for directory in SIZES:
        target = THUMBNAIL_ROOT / directory / name
        if not target.is_file():
            return False
        text = png_text(target)
        if text.get("Software") != TAG:
            return False
        if text.get("Thumb::URI") != uri or text.get("Thumb::MTime") != mtime:
            return False
    return True


def write_thumbnails(folder: str, icon_uri: str, source: Path, entry: dict) -> None:
    uri, name = thumbnail_name(folder)
    mtime = str(int(os.stat(folder).st_mtime))
    image = GdkPixbuf.Pixbuf.new_from_file_at_scale(str(source), max(SIZES.values()), max(SIZES.values()), True)
    records = entry.setdefault("thumbnails", {})
    for directory, size in SIZES.items():
        target = THUMBNAIL_ROOT / directory / name
        target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        if target.exists() and not is_ours(target):
            backup = backup_foreign(target)
            records.setdefault(str(target), str(backup))
        records.setdefault(str(target), None)
        ratio = size / max(image.get_width(), image.get_height())
        scaled = image.scale_simple(
            max(1, round(image.get_width() * ratio)),
            max(1, round(image.get_height() * ratio)),
            GdkPixbuf.InterpType.HYPER,
        )
        temporary = target.with_name(f"{name}.{TAG}.tmp")
        scaled.savev(
            str(temporary), "png",
            ["tEXt::Thumb::URI", "tEXt::Thumb::MTime", "tEXt::Software"],
            [uri, mtime, TAG],
        )
        os.chmod(temporary, 0o600)
        os.replace(temporary, target)
    entry.update({"uri": uri, "icon": icon_uri})


def remove_entry(folder: str, entry: dict) -> None:
    for thumbnail, backup in entry.get("thumbnails", {}).items():
        target = Path(thumbnail)
        if is_ours(target):
            target.unlink(missing_ok=True)
        if backup and Path(backup).is_file():
            if target.exists():
                print(f"aviso: {target} foi recriado por outro programa; backup mantido em {backup}")
            else:
                shutil.move(backup, target)
                print(f"backup restaurado: {target}")
    print(f"removido: {folder}")


def sweep_orphans() -> int:
    removed = 0
    for directory in SIZES:
        for thumbnail in (THUMBNAIL_ROOT / directory).glob("*.png"):
            if is_ours(thumbnail):
                thumbnail.unlink(missing_ok=True)
                removed += 1
    return removed


def prune_empty_backups() -> None:
    if not BACKUP_ROOT.is_dir():
        return
    for directory in sorted(BACKUP_ROOT.rglob("*"), key=lambda path: len(path.parts), reverse=True):
        if directory.is_dir() and not any(directory.iterdir()):
            directory.rmdir()
    if not any(BACKUP_ROOT.iterdir()):
        BACKUP_ROOT.rmdir()


def thumbnail_files() -> list[Path]:
    """Every cached thumbnail, including the failed-thumbnail markers."""
    if not THUMBNAIL_ROOT.is_dir():
        return []
    found: list[Path] = []
    for directory in THUMBNAIL_ROOT.iterdir():
        if not directory.is_dir():
            continue
        pattern = "*/*.png" if directory.name == "fail" else "*.png"
        found.extend(directory.glob(pattern))
    return found


def is_directory_uri(uri: str) -> bool:
    """Only Forge creates thumbnails that stand for a directory."""
    if not uri:
        return False
    parts = urlsplit(uri)
    if parts.scheme not in ("", "file"):
        return False
    try:
        return Path(unquote(parts.path)).is_dir()
    except OSError:
        return False


def refresh_icon_cache() -> None:
    """Rebuild the GTK icon cache so replaced assets are picked up."""
    executable = shutil.which("gtk-update-icon-cache")
    theme = Path(GLib.get_user_data_dir()) / "icons" / FORGE_ICON_THEME
    if not executable or not theme.is_dir():
        return
    subprocess.run(
        [executable, "-f", "-t", str(theme)], check=False,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )


def _purge_asset_caches() -> int:
    """Drop cached folder artwork; callers hold folder_icons_lock()."""
    removed = 0
    for path in thumbnail_files():
        text = png_text(path)
        if text.get("Software") != TAG and not is_directory_uri(text.get("Thumb::URI", "")):
            continue
        try:
            path.unlink(missing_ok=True)
        except OSError:
            continue
        removed += 1
    refresh_icon_cache()
    return removed


def purge_asset_caches() -> int:
    """Remove every cached folder icon so a theme switch shows no stale art."""
    with folder_icons_lock():
        removed = _purge_asset_caches()
    if removed:
        print(f"cache de assets limpo: {removed} miniatura(s) de pasta removida(s)")
        refresh_nautilus(removed=True)
    return removed


def nautilus_windows() -> list[str] | None:
    """List open Nautilus window object paths, or None when it is not running."""
    try:
        connection = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        reply = connection.call_sync(
            NAUTILUS_BUS, NAUTILUS_WINDOW_PATH,
            "org.freedesktop.DBus.Introspectable", "Introspect", None,
            GLib.VariantType.new("(s)"), Gio.DBusCallFlags.NO_AUTO_START,
            NAUTILUS_CALL_TIMEOUT_MS, None)
    except GLib.Error:
        return None
    return [
        f"{NAUTILUS_WINDOW_PATH}/{name}"
        for name in re.findall(r'<node name="(\d+)"', reply.unpack()[0])
    ]


def reload_nautilus_window(path: str) -> bool:
    """Trigger the window's own reload action, the same as Ctrl+R."""
    try:
        connection = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        connection.call_sync(
            NAUTILUS_BUS, path, "org.gtk.Actions", "Activate",
            GLib.Variant("(sava{sv})", ("reload", [], {})), None,
            Gio.DBusCallFlags.NO_AUTO_START, NAUTILUS_CALL_TIMEOUT_MS, None)
    except GLib.Error as error:
        print(f"aviso: nao foi possivel recarregar {path}: {error.message}", file=sys.stderr)
        return False
    return True


def quit_nautilus() -> bool:
    """Restart the Nautilus service; only this drops its in-memory art cache."""
    executable = shutil.which("nautilus")
    if not executable:
        return False
    subprocess.run(
        [executable, "-q"], check=False,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    return True


def refresh_nautilus(removed: bool = False) -> None:
    """Make Nautilus forget folder art that no longer exists.

    Reloading a window is enough to pick up new artwork, but Nautilus keeps a
    process-wide cache that still renders thumbnails deleted from disk, so a
    removal has to restart the service.
    """
    windows = nautilus_windows()
    if windows is None:
        return
    if removed:
        if quit_nautilus():
            if windows:
                print(
                    f"Nautilus reiniciado para descartar icones antigos"
                    f" ({len(windows)} janela(s) fechada(s))"
                )
            else:
                print("cache do Nautilus descartado")
        return
    if not windows:
        quit_nautilus()
        return
    reloaded = sum(reload_nautilus_window(path) for path in windows)
    if reloaded:
        print(f"Nautilus recarregado ({reloaded} janela(s))")


def strip_forge_css(text: str) -> str:
    """Drop the Forge block and the legacy @import from a user gtk.css."""
    result: list[str] = []
    inside = False
    for line in text.splitlines(keepends=True):
        stripped = line.strip()
        if stripped == GTK4_BEGIN:
            inside = True
            continue
        if stripped == GTK4_END:
            inside = False
            continue
        if inside or stripped == NAUTILUS_CSS_IMPORT:
            continue
        result.append(line)
    return "".join(result)


def write_user_css(path: Path, text: str) -> None:
    """Replace a user stylesheet atomically, or remove it when empty."""
    if not text.strip():
        path.unlink(missing_ok=True)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.{TAG}.tmp")
    temporary.write_text(text, encoding="utf-8")
    os.replace(temporary, path)


def install_nautilus_css() -> None:
    """Inline the Nautilus rules; snaps cannot resolve a relative @import."""
    if not NAUTILUS_CSS_SOURCE.is_file():
        abort(f"css do Nautilus nao encontrado em {NAUTILUS_CSS_SOURCE}")
    GTK4_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(NAUTILUS_CSS_SOURCE, GTK4_DIR / NAUTILUS_CSS_NAME)
    rules = NAUTILUS_CSS_SOURCE.read_text(encoding="utf-8").strip()
    block = f"{GTK4_BEGIN}\n{rules}\n{GTK4_END}\n"
    current = GTK4_CSS.read_text(encoding="utf-8") if GTK4_CSS.is_file() else ""
    desired = block + strip_forge_css(current)
    if desired == current:
        return
    write_user_css(GTK4_CSS, desired)
    print(f"css do Nautilus embutido: {GTK4_CSS}")


def remove_nautilus_css() -> None:
    if GTK4_CSS.is_file():
        current = GTK4_CSS.read_text(encoding="utf-8")
        remaining = strip_forge_css(current)
        if remaining != current:
            write_user_css(GTK4_CSS, remaining)
            print(f"css do Nautilus removido: {GTK4_CSS}")
    (GTK4_DIR / NAUTILUS_CSS_NAME).unlink(missing_ok=True)


def unit_paths() -> tuple[Path, Path, Path, Path]:
    return (
        SYSTEMD_DIR / f"{UNIT}.service",
        SYSTEMD_DIR / f"{UNIT}.timer",
        SYSTEMD_DIR / f"{UNIT}-cleanup.service",
        SYSTEMD_DIR / f"{UNIT}-theme.service",
    )


def install_timer(arguments: list[str]) -> None:
    service, timer, cleanup, theme = unit_paths()
    if not WATCH_SCRIPT.is_file():
        abort(f"sincronizador de tema nao encontrado em {WATCH_SCRIPT}")
    for unit in (service, timer, cleanup, theme):
        if unit.exists() and TAG not in unit.read_text(encoding="utf-8"):
            abort(f"{unit} existe e nao pertence ao Forge Core; nada foi sobrescrito")
    command = " ".join(shlex.quote(part) for part in [sys.executable, str(APPLY_SCRIPT), *arguments])
    cleanup_command = " ".join(
        shlex.quote(part) for part in [sys.executable, str(APPLY_SCRIPT), "--deactivate"]
    )
    watch_command = " ".join(
        shlex.quote(part) for part in [sys.executable, str(WATCH_SCRIPT), "--depth", arguments[-1]]
    )
    SYSTEMD_DIR.mkdir(parents=True, exist_ok=True)
    service.write_text(
        f"[Unit]\nDescription=Forge Core: icones de pasta no seletor de arquivos GTK\n\n"
        f"[Service]\nType=oneshot\nSyslogIdentifier={TAG}\nExecStart={command}\n",
        encoding="utf-8",
    )
    timer.write_text(
        f"[Unit]\nDescription=Forge Core: reaplica icones de pasta no seletor GTK\n\n"
        f"[Timer]\nUnit={service.name}\nOnStartupSec=2min\nOnCalendar=weekly\nPersistent=true\n\n"
        f"[Install]\nWantedBy=timers.target\n",
        encoding="utf-8",
    )
    cleanup.write_text(
        f"[Unit]\nDescription=Forge Core: remove icones de pasta fora do tema\n\n"
        f"[Service]\nType=oneshot\nSyslogIdentifier={TAG}\nExecStart={cleanup_command}\n",
        encoding="utf-8",
    )
    theme.write_text(
        f"[Unit]\nDescription=Forge Core: sincroniza icones de pasta com o tema ativo\n"
        f"After=graphical-session.target\n\n"
        f"[Service]\nType=simple\nSyslogIdentifier={TAG}\nExecStart={watch_command}\n"
        f"Environment=PYTHONUNBUFFERED=1\nRestart=on-failure\nRestartSec=5s\n\n"
        f"[Install]\nWantedBy=default.target\n",
        encoding="utf-8",
    )
    subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
    subprocess.run(["systemctl", "--user", "enable", "--now", timer.name], check=True)
    subprocess.run(["systemctl", "--user", "enable", "--now", theme.name], check=True)
    subprocess.run(["systemctl", "--user", "restart", theme.name], check=True)
    print(f"timer e sincronizador instalados: {timer}, {theme}")


def remove_timer() -> None:
    service, timer, cleanup, theme = unit_paths()
    units = [
        unit for unit in (timer, service, cleanup, theme)
        if unit.is_file() and TAG in unit.read_text(encoding="utf-8")
    ]
    if not units:
        return
    subprocess.run(
        ["systemctl", "--user", "disable", "--now", timer.name, theme.name],
        check=False,
    )
    for unit in units:
        unit.unlink()
    subprocess.run(["systemctl", "--user", "daemon-reload"], check=False)
    print(f"timer removido: {timer}")


def remove_generated() -> tuple[bool, int]:
    manifest = load_manifest()
    folders = manifest.get("folders", {})
    had_entries = bool(folders)
    for folder, entry in folders.items():
        remove_entry(folder, entry)
    orphans = sweep_orphans()
    remove_nautilus_css()
    if MANIFEST.is_file():
        MANIFEST.unlink()
    if STATE_DIR.is_dir() and not any(STATE_DIR.iterdir()):
        STATE_DIR.rmdir()
    prune_empty_backups()
    return had_entries, orphans


def _deactivate() -> bool:
    try:
        from special_folder_icons import deactivate as deactivate_special_folders

        deactivate_special_folders()
    except (GLib.Error, OSError, RuntimeError) as error:
        print(f"aviso: icones de pastas especiais nao foram totalmente removidos: {error}")
    purged = _purge_asset_caches()
    had_entries, orphans = remove_generated()
    orphans += purged
    if had_entries or orphans:
        print("Concluido: icones do seletor removidos porque Forge-Core esta inativo.")
    else:
        print("Nenhuma miniatura Forge Core encontrada.")
    return bool(had_entries or orphans)


def _apply(roots: list[Path], depth: int, dry_run: bool, timer_arguments: list[str] | None) -> int:
    if not forge_core_active():
        if dry_run:
            print("Forge-Core inativo. Nada seria aplicado ao seletor de pastas.")
        else:
            deactivate()
        return 0

    try:
        from special_folder_icons import sync as sync_special_folders

        sync_special_folders(dry_run)
    except (GLib.Error, OSError, RuntimeError) as error:
        print(f"aviso: icones de pastas especiais nao foram aplicados: {error}")

    manifest = load_manifest()
    folders: dict = manifest["folders"]
    found: dict[str, str] = {}
    for root in roots:
        if not root.is_dir():
            abort(f"diretorio inexistente: {root}")
        icon = custom_icon(Gio.File.new_for_path(str(root)))
        if icon:
            found[str(root)] = icon
        scan(root, depth, found)
    for folder in list(folders):
        if folder not in found:
            icon = custom_icon(Gio.File.new_for_path(folder)) if Path(folder).is_dir() else None
            if icon:
                found[folder] = icon
            elif dry_run:
                print(f"removeria: {folder}")
            else:
                remove_entry(folder, folders.pop(folder))

    applied = 0
    unchanged = 0
    for folder, icon_uri in sorted(found.items()):
        source = icon_path(icon_uri)
        if source is None:
            print(f"ignorado: icone inacessivel para {folder}: {icon_uri}")
            continue
        if dry_run:
            print(f"aplicaria: {folder} -> {source.name}")
            continue
        entry = folders.setdefault(folder, {})
        if thumbnails_current(folder, icon_uri, entry):
            unchanged += 1
            continue
        try:
            write_thumbnails(folder, icon_uri, source, entry)
        except GLib.Error as error:
            print(f"ignorado: {folder}: {error.message}")
            if not folders[folder].get("thumbnails"):
                folders.pop(folder)
            continue
        applied += 1
        print(f"aplicado: {folder} -> {source.name}")

    if dry_run:
        print(f"Simulacao: {len(found)} pasta(s) com metadata::custom-icon. Nada foi alterado.")
        return 0
    save_manifest(manifest)
    install_nautilus_css()
    if timer_arguments is not None:
        install_timer(timer_arguments)
    print(f"Concluido: {applied} pasta(s) atualizada(s), {unchanged} ja em dia. Manifesto: {MANIFEST}")
    return applied


def _restore() -> None:
    remove_timer()
    try:
        from special_folder_icons import remove_timer as remove_special_timer
        from special_folder_icons import deactivate as deactivate_special_folders

        remove_special_timer()
        deactivate_special_folders()
    except (GLib.Error, OSError, RuntimeError) as error:
        print(f"aviso: icones de pastas especiais nao foram totalmente restaurados: {error}")
    had_entries, orphans = remove_generated()
    if orphans:
        print(f"miniaturas Forge Core orfas removidas: {orphans}")
    if not had_entries and not orphans:
        print("Nenhuma miniatura Forge Core encontrada.")
    else:
        print("Concluido. O metadata::custom-icon das pastas (Nautilus) nao foi alterado.")


def deactivate() -> None:
    """Remove the generated thumbnails; serialized against other Forge runs."""
    with folder_icons_lock():
        if _deactivate():
            refresh_nautilus(removed=True)


def apply(roots: list[Path], depth: int, dry_run: bool, timer_arguments: list[str] | None) -> None:
    """Refresh the generated thumbnails; serialized against other Forge runs."""
    with folder_icons_lock():
        if _apply(roots, depth, dry_run, timer_arguments):
            refresh_nautilus()


def restore() -> None:
    """Undo every Forge change to the chooser; serialized against other runs."""
    with folder_icons_lock():
        _restore()
