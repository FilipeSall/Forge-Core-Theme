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
import shlex
import shutil
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import unquote, urlsplit

import gi

gi.require_version("GdkPixbuf", "2.0")
from gi.repository import GdkPixbuf, Gio, GLib


TAG = "forge-core-folder-chooser-icons"
THUMBNAIL_ROOT = Path(GLib.get_user_cache_dir()) / "thumbnails"
SIZES = {"large": 256, "normal": 128}
STATE_DIR = Path.home() / ".local" / "share" / "forge-core" / "folder-chooser-icons"
MANIFEST = STATE_DIR / "manifest.json"
BACKUP_ROOT = Path.home() / ".local" / "share" / "forge-core" / "backups" / "folder-chooser-icons"
SYSTEMD_DIR = Path.home() / ".config" / "systemd" / "user"
UNIT = "forge-core-folder-chooser-icons"
APPLY_SCRIPT = Path(__file__).resolve().parent / "apply-folder-chooser-icons.py"
NAUTILUS_CSS_NAME = "forge-core-nautilus-thumbnails.css"
NAUTILUS_CSS_SOURCE = Path(__file__).resolve().parent.parent / "gtk-4.0" / NAUTILUS_CSS_NAME
GTK4_DIR = Path(GLib.get_user_config_dir()) / "gtk-4.0"
GTK4_CSS = GTK4_DIR / "gtk.css"
NAUTILUS_CSS_IMPORT = f'@import url("{NAUTILUS_CSS_NAME}");'
DEFAULT_DEPTH = 6
SCAN_ATTRIBUTES = "standard::name,standard::type,metadata::custom-icon"
NO_DESCEND = {
    ".cache", ".cargo", ".config", ".git", ".gradle", ".local", ".m2", ".mozilla",
    ".npm", ".pnpm-store", ".rustup", ".var", ".vscode", "node_modules", "snap",
}


def abort(message: str) -> None:
    print(f"erro: {message}", file=sys.stderr)
    raise SystemExit(1)


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
    if MANIFEST.is_file():
        return json.loads(MANIFEST.read_text(encoding="utf-8"))
    return {"version": 1, "folders": {}}


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
            target.unlink()
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
                thumbnail.unlink()
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


def install_nautilus_css() -> None:
    if not NAUTILUS_CSS_SOURCE.is_file():
        abort(f"css do Nautilus nao encontrado em {NAUTILUS_CSS_SOURCE}")
    GTK4_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(NAUTILUS_CSS_SOURCE, GTK4_DIR / NAUTILUS_CSS_NAME)
    current = GTK4_CSS.read_text(encoding="utf-8") if GTK4_CSS.is_file() else ""
    if NAUTILUS_CSS_IMPORT in (line.strip() for line in current.splitlines()):
        return
    GTK4_CSS.write_text(f"{NAUTILUS_CSS_IMPORT}\n{current}", encoding="utf-8")
    print(f"css do Nautilus instalado: {GTK4_CSS} (reabra o Nautilus: nautilus -q)")


def remove_nautilus_css() -> None:
    if GTK4_CSS.is_file():
        lines = GTK4_CSS.read_text(encoding="utf-8").splitlines(keepends=True)
        remaining = "".join(line for line in lines if line.strip() != NAUTILUS_CSS_IMPORT)
        if len(remaining) != sum(map(len, lines)):
            if remaining.strip():
                GTK4_CSS.write_text(remaining, encoding="utf-8")
            else:
                GTK4_CSS.unlink()
            print(f"css do Nautilus removido: {GTK4_CSS}")
    (GTK4_DIR / NAUTILUS_CSS_NAME).unlink(missing_ok=True)


def unit_paths() -> tuple[Path, Path]:
    return SYSTEMD_DIR / f"{UNIT}.service", SYSTEMD_DIR / f"{UNIT}.timer"


def install_timer(arguments: list[str]) -> None:
    service, timer = unit_paths()
    for unit in (service, timer):
        if unit.exists() and TAG not in unit.read_text(encoding="utf-8"):
            abort(f"{unit} existe e nao pertence ao Forge Core; nada foi sobrescrito")
    command = " ".join(shlex.quote(part) for part in [sys.executable, str(APPLY_SCRIPT), *arguments])
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
    subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
    subprocess.run(["systemctl", "--user", "enable", "--now", timer.name], check=True)
    print(f"timer instalado: {timer}")


def remove_timer() -> None:
    service, timer = unit_paths()
    units = [unit for unit in (timer, service) if unit.is_file() and TAG in unit.read_text(encoding="utf-8")]
    if not units:
        return
    subprocess.run(["systemctl", "--user", "disable", "--now", timer.name], check=False)
    for unit in units:
        unit.unlink()
    subprocess.run(["systemctl", "--user", "daemon-reload"], check=False)
    print(f"timer removido: {timer}")


def apply(roots: list[Path], depth: int, dry_run: bool, timer_arguments: list[str] | None) -> None:
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
    for folder, icon_uri in sorted(found.items()):
        source = icon_path(icon_uri)
        if source is None:
            print(f"ignorado: icone inacessivel para {folder}: {icon_uri}")
            continue
        if dry_run:
            print(f"aplicaria: {folder} -> {source.name}")
            continue
        try:
            write_thumbnails(folder, icon_uri, source, folders.setdefault(folder, {}))
        except GLib.Error as error:
            print(f"ignorado: {folder}: {error.message}")
            if not folders[folder].get("thumbnails"):
                folders.pop(folder)
            continue
        applied += 1
        print(f"aplicado: {folder} -> {source.name}")

    if dry_run:
        print(f"Simulacao: {len(found)} pasta(s) com metadata::custom-icon. Nada foi alterado.")
        return
    save_manifest(manifest)
    install_nautilus_css()
    if timer_arguments is not None:
        install_timer(timer_arguments)
    print(f"Concluido: {applied} pasta(s). Manifesto: {MANIFEST}")
    print("Abra o seletor de pastas de novo; nao e preciso reiniciar o portal nem a sessao.")


def restore() -> None:
    remove_timer()
    remove_nautilus_css()
    manifest = load_manifest()
    for folder, entry in manifest["folders"].items():
        remove_entry(folder, entry)
    orphans = sweep_orphans()
    if orphans:
        print(f"miniaturas Forge Core orfas removidas: {orphans}")
    if MANIFEST.is_file():
        MANIFEST.unlink()
    if STATE_DIR.is_dir() and not any(STATE_DIR.iterdir()):
        STATE_DIR.rmdir()
    prune_empty_backups()
    if not manifest["folders"] and not orphans:
        print("Nenhuma miniatura Forge Core encontrada.")
    else:
        print("Concluido. O metadata::custom-icon das pastas (Nautilus) nao foi alterado.")
