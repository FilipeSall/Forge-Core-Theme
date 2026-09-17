"""Apply Forge Core icons to named folders across the local filesystem."""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path

import gi

from forge_locks import folder_icons_lock

gi.require_version("Gio", "2.0")
from gi.repository import Gio, GLib


TAG = "forge-core-special-folder-icons"
ICON_THEME_SCHEMA = "org.gnome.desktop.interface"
FORGE_ICON_THEME = "Forge-Core"
REPO_ROOT = Path(__file__).resolve().parent.parent
ASSET_MANIFEST = REPO_ROOT / "assets" / "icons" / "manifest.json"
USER_DATA_DIR = Path(GLib.get_user_data_dir())
THEME_ROOT = USER_DATA_DIR / "icons" / FORGE_ICON_THEME
STATE_DIR = USER_DATA_DIR / "forge-core" / "special-folder-icons"
STATE_FILE = STATE_DIR / "manifest.json"
SYSTEMD_DIR = Path(GLib.get_user_config_dir()) / "systemd" / "user"
SCRIPT = Path(__file__).resolve()
UNIT = "forge-core-special-folder-icons"
UNIT_MARKER = f"# {TAG}"
DEFAULT_MATCH_DEPTH = 2
FIND_TIMEOUT_SECONDS = 30

SKIP_NAMES = (
    ".cache",
    ".git",
    ".gradle",
    ".m2",
    ".npm",
    ".pnpm-store",
    ".rustup",
    ".vscode",
    ".var",
    "__pycache__",
    "node_modules",
)


def normalize_name(name: str) -> str:
    return name.casefold()


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


def scan_roots(special: dict[str, dict]) -> dict[Path, tuple[int, list[str]]]:
    """Group the configured names by root, keeping the deepest limit needed."""
    roots: dict[Path, tuple[int, list[str]]] = {}
    for spec in special.values():
        depth = spec.get("matchDepth", DEFAULT_MATCH_DEPTH)
        for root in spec["matchRoots"]:
            current_depth, names = roots.get(root, (0, []))
            roots[root] = (max(current_depth, depth), [*names, spec["name"]])
    return roots


def find_command(root: Path, depth: int, names: list[str]) -> list[str]:
    """Build a bounded, single-filesystem search for the given root."""
    prune: list[str] = []
    for index, skip_name in enumerate(SKIP_NAMES):
        if index:
            prune.append("-o")
        prune.extend(("-name", skip_name))
    prune.extend(("-o", "-name", ".*"))
    matches: list[str] = []
    for index, name in enumerate(names):
        if index:
            matches.append("-o")
        matches.extend(("-iname", name))
    return [
        "find", str(root),
        "-xdev", "-maxdepth", str(depth),
        "-mindepth", "1",
        "(", *prune, ")", "-prune",
        "-o", "-type", "d", "(", *matches, ")", "-print0",
    ]


def iter_directories(special: dict[str, dict]):
    """Yield candidate directories, one bounded scan per configured root."""
    for root, (depth, names) in sorted(scan_roots(special).items()):
        if not root.is_dir():
            continue
        try:
            process = subprocess.Popen(
                find_command(root, depth, names),
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
            )
        except OSError as error:
            raise RuntimeError(f"find indisponivel: {error}") from error

        assert process.stdout is not None
        deadline = time.monotonic() + FIND_TIMEOUT_SECONDS
        pending = b""
        timed_out = False
        try:
            while chunk := process.stdout.read(64 * 1024):
                pending += chunk
                while b"\0" in pending:
                    raw_path, pending = pending.split(b"\0", 1)
                    if raw_path:
                        yield Path(os.fsdecode(raw_path))
                if time.monotonic() > deadline:
                    timed_out = True
                    break
        finally:
            process.stdout.close()
            if timed_out:
                process.kill()
            try:
                result = process.wait(timeout=FIND_TIMEOUT_SECONDS)
            except subprocess.TimeoutExpired:
                process.kill()
                result = process.wait()
                timed_out = True

        if timed_out:
            print(
                f"aviso: varredura de {root} excedeu {FIND_TIMEOUT_SECONDS}s e foi interrompida",
                file=sys.stderr,
            )
        elif result == 1:
            print(
                f"aviso: find encontrou diretorios sem permissao em {root};"
                " resultados acessiveis foram mantidos",
                file=sys.stderr,
            )
        elif result != 0:
            raise RuntimeError(f"find terminou com status {result} em {root}")


def load_special_folders() -> dict[str, dict]:
    if not ASSET_MANIFEST.is_file():
        raise RuntimeError(f"manifesto ausente: {ASSET_MANIFEST}")
    data = json.loads(ASSET_MANIFEST.read_text(encoding="utf-8"))
    special: dict[str, dict] = {}
    for icon in data.get("icons", []):
        folder_names = icon.get("folderNames", [])
        if not folder_names:
            continue
        icon_path = THEME_ROOT / "256x256" / icon["context"] / f"{icon['name']}.png"
        if not icon_path.is_file():
            print(
                f"aviso: asset instalado ausente, {icon['name']} ignorado: {icon_path}"
                " (rode scripts/install-icons.sh)",
                file=sys.stderr,
            )
            continue
        icon_uri = GLib.filename_to_uri(str(icon_path), None)
        legacy_sources = dict.fromkeys([icon["source"], *icon.get("legacySources", [])])
        legacy_uris = [
            GLib.filename_to_uri(str(REPO_ROOT / "assets" / "icons" / source), None)
            for source in legacy_sources
        ]
        for folder_name in folder_names:
            key = normalize_name(folder_name)
            if key in special:
                raise RuntimeError(f"nome de pasta especial duplicado: {folder_name}")
            match_roots = tuple(
                Path(root).expanduser() for root in icon.get("matchRoots", [])
            )
            if not match_roots:
                print(
                    f"aviso: {icon['name']} sem matchRoots, ignorado", file=sys.stderr
                )
                continue
            special[key] = {
                "name": folder_name,
                "icon": icon["name"],
                "uri": icon_uri,
                "legacyUris": legacy_uris,
                "matchRoots": match_roots,
                "matchDepth": int(icon.get("matchDepth", DEFAULT_MATCH_DEPTH)),
            }
    if not special:
        raise RuntimeError("nenhuma pasta especial foi definida no manifesto")
    return special


def load_state() -> dict[str, dict[str, str]]:
    if not STATE_FILE.is_file():
        return {}
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"aviso: manifesto de pastas especiais invalido: {error}", file=sys.stderr)
        return {}
    folders = data.get("folders", {})
    return folders if isinstance(folders, dict) else {}


def save_state(folders: dict[str, dict[str, str]]) -> None:
    if not folders:
        STATE_FILE.unlink(missing_ok=True)
        if STATE_DIR.is_dir() and not any(STATE_DIR.iterdir()):
            STATE_DIR.rmdir()
        return
    STATE_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
    temporary = STATE_FILE.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps({"version": 1, "tag": TAG, "folders": folders}, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )
    os.chmod(temporary, 0o600)
    os.replace(temporary, STATE_FILE)


def custom_icon(path: Path) -> str | None:
    try:
        info = Gio.File.new_for_path(str(path)).query_info(
            "metadata::custom-icon", Gio.FileQueryInfoFlags.NONE, None
        )
    except GLib.Error:
        return None
    return info.get_attribute_string("metadata::custom-icon") or None


def icon_uri_accessible(uri: str) -> bool:
    if not uri.startswith("file://"):
        return True
    try:
        return Gio.File.new_for_uri(uri).query_exists(None)
    except GLib.Error:
        return False


def set_custom_icon(path: Path, uri: str) -> bool:
    try:
        result = Gio.File.new_for_path(str(path)).set_attribute_string(
            "metadata::custom-icon", uri, Gio.FileQueryInfoFlags.NONE, None
        )
    except GLib.Error as error:
        print(f"ignorado: nao foi possivel definir {path}: {error.message}", file=sys.stderr)
        return False
    if result is False:
        print(f"ignorado: nao foi possivel definir {path}", file=sys.stderr)
        return False
    return True


def clear_custom_icon(path: Path) -> bool:
    try:
        result = Gio.File.new_for_path(str(path)).set_attribute(
            "metadata::custom-icon",
            Gio.FileAttributeType.INVALID,
            None,
            Gio.FileQueryInfoFlags.NONE,
            None,
        )
    except GLib.Error as error:
        print(f"ignorado: nao foi possivel remover {path}: {error.message}", file=sys.stderr)
        return False
    if result is False:
        print(f"ignorado: nao foi possivel remover {path}", file=sys.stderr)
        return False
    return True


def relative_depth(path: Path, root: Path) -> int | None:
    """Return how many components separate ``path`` from ``root``."""
    try:
        return len(path.relative_to(root).parts)
    except ValueError:
        return None


def in_scope(path: Path, spec: dict) -> bool:
    """Accept only shallow, visible folders under one of the declared roots."""
    roots = spec.get("matchRoots", ())
    if not roots:
        return False
    max_depth = spec.get("matchDepth", DEFAULT_MATCH_DEPTH)
    for root in roots:
        depth = relative_depth(path, root)
        if depth is None or depth < 1 or depth > max_depth:
            continue
        if any(part.startswith(".") for part in path.relative_to(root).parts):
            continue
        return True
    return False


def _sync(dry_run: bool = False) -> tuple[int, int, int]:
    if not forge_core_active():
        deactivate()
        print("Forge-Core inativo. Nenhum icone especial foi aplicado.")
        return 0, 0, 0

    special = load_special_folders()
    managed = load_state()
    seen: set[str] = set()
    applied = 0
    preserved = 0
    removed = 0

    for folder in iter_directories(special):
        spec = special.get(normalize_name(folder.name))
        if spec is None or not in_scope(folder, spec):
            continue
        folder_key = str(folder)
        seen.add(folder_key)
        desired = spec["uri"]
        current = custom_icon(folder)
        previous = managed.get(folder_key, {})
        previous_uri = previous.get("uri")

        if current == desired:
            managed[folder_key] = {"uri": desired, "name": spec["name"]}
            continue

        if current and current != previous_uri:
            if current in spec["legacyUris"]:
                if dry_run:
                    print(f"migraria: {folder} -> {spec['icon']}")
                    applied += 1
                elif set_custom_icon(folder, desired):
                    managed[folder_key] = {"uri": desired, "name": spec["name"]}
                    applied += 1
                continue
            if not icon_uri_accessible(current):
                print(
                    f"aviso: icone manual inacessivel para {folder}; usando {spec['icon']}",
                    file=sys.stderr,
                )
                if dry_run:
                    print(f"usaria fallback: {folder} -> {spec['icon']}")
                    applied += 1
                elif set_custom_icon(folder, desired):
                    managed[folder_key] = {"uri": desired, "name": spec["name"]}
                    applied += 1
                continue
            # A custom icon not previously managed by Forge Core belongs to the
            # user, as long as its file still exists.
            if previous_uri:
                managed.pop(folder_key, None)
            preserved += 1
            continue

        if dry_run:
            print(f"aplicaria: {folder} -> {spec['icon']}")
            applied += 1
            continue

        if set_custom_icon(folder, desired):
            managed[folder_key] = {"uri": desired, "name": spec["name"]}
            applied += 1

    # Remove Forge-owned metadata from folders that were renamed or deleted.
    # If the name still matches a configured folder but traversal missed it due
    # to permissions, keep the state for a later retry instead of clearing it.
    for folder_key, previous in list(managed.items()):
        if folder_key in seen:
            continue
        folder = Path(folder_key)
        if not folder.is_dir():
            managed.pop(folder_key, None)
            continue
        spec = special.get(normalize_name(folder.name))
        if spec is not None and in_scope(folder, spec):
            continue
        previous_uri = previous.get("uri")
        if custom_icon(folder) != previous_uri:
            managed.pop(folder_key, None)
            continue
        if dry_run:
            print(f"removeria: {folder}")
            removed += 1
        elif clear_custom_icon(folder):
            managed.pop(folder_key, None)
            removed += 1

    if not dry_run:
        save_state(managed)
    print(
        f"Sincronizacao: {applied} aplicado(s), {preserved} manual(is) preservado(s), "
        f"{removed} removido(s)."
    )
    return applied, preserved, removed


def _deactivate() -> int:
    managed = load_state()
    removed = 0
    remaining: dict[str, dict[str, str]] = {}
    for folder_key, previous in managed.items():
        folder = Path(folder_key)
        previous_uri = previous.get("uri")
        if not folder.is_dir():
            continue
        if custom_icon(folder) != previous_uri:
            # The user replaced the Forge icon manually; do not touch it.
            continue
        if clear_custom_icon(folder):
            removed += 1
        else:
            remaining[folder_key] = previous
    save_state(remaining)
    if removed:
        print(f"Removidos {removed} icone(s) especial(is) do Forge Core.")
    return removed


def sync(dry_run: bool = False) -> tuple[int, int, int]:
    """Apply the by-name folder icons; serialized against other Forge runs."""
    with folder_icons_lock():
        return _sync(dry_run)


def deactivate() -> int:
    """Clear the Forge-owned folder metadata; serialized against other runs."""
    with folder_icons_lock():
        return _deactivate()


def unit_paths() -> tuple[Path, Path]:
    return SYSTEMD_DIR / f"{UNIT}.service", SYSTEMD_DIR / f"{UNIT}.timer"


def install_timer() -> None:
    service, timer = unit_paths()
    for unit in (service, timer):
        if unit.exists() and UNIT_MARKER not in unit.read_text(encoding="utf-8"):
            raise RuntimeError(f"{unit} existe e nao pertence ao Forge Core; nada foi sobrescrito")
    SYSTEMD_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
    command = " ".join(shlex.quote(part) for part in [sys.executable, str(SCRIPT), "--sync"])
    service.write_text(
        f"{UNIT_MARKER}\n[Unit]\nDescription=Forge Core: pastas especiais por nome\n"
        f"After=graphical-session.target\n\n[Service]\nType=oneshot\n"
        f"SyslogIdentifier={TAG}\nExecStart={command}\n",
        encoding="utf-8",
    )
    timer.write_text(
        f"{UNIT_MARKER}\n[Unit]\nDescription=Forge Core: sincroniza pastas especiais\n\n"
        f"[Timer]\nUnit={service.name}\nOnStartupSec=2min\nOnUnitActiveSec=1d\n"
        f"Persistent=true\n\n[Install]\nWantedBy=timers.target\n",
        encoding="utf-8",
    )
    subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
    subprocess.run(["systemctl", "--user", "enable", "--now", timer.name], check=True)
    subprocess.run(["systemctl", "--user", "start", service.name], check=True)
    print(f"timer de pastas especiais instalado: {timer}")


def remove_timer() -> None:
    service, timer = unit_paths()
    units = [
        unit
        for unit in (service, timer)
        if unit.is_file() and UNIT_MARKER in unit.read_text(encoding="utf-8")
    ]
    if not units:
        return
    subprocess.run(
        ["systemctl", "--user", "disable", "--now", timer.name, service.name],
        check=False,
    )
    for unit in units:
        unit.unlink()
    subprocess.run(["systemctl", "--user", "daemon-reload"], check=False)
    print(f"timer de pastas especiais removido: {timer}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sync", action="store_true", help="sincroniza as pastas especiais")
    parser.add_argument("--dry-run", action="store_true", help="lista sem alterar metadata")
    parser.add_argument("--timer", action="store_true", help="instala o timer diario")
    parser.add_argument(
        "--deactivate",
        action="store_true",
        help="remove somente os icones especiais gerenciados pelo Forge Core",
    )
    args = parser.parse_args()
    if args.deactivate and (args.sync or args.dry_run or args.timer):
        parser.error("--deactivate nao pode ser combinado com --sync, --dry-run ou --timer")
    if args.deactivate:
        deactivate()
        return
    if args.dry_run and args.timer:
        parser.error("--dry-run nao pode ser combinado com --timer")
    sync(dry_run=args.dry_run)
    if args.timer and not args.dry_run:
        install_timer()


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError, GLib.Error) as error:
        print(f"erro: {error}", file=sys.stderr)
        raise SystemExit(1)
