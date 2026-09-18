#!/usr/bin/env python3
"""Rotate Forge Core backgrounds, using a distinct image per active monitor."""

from __future__ import annotations

import fcntl
import json
import os
import secrets
import re
import subprocess
import time
from pathlib import Path

from PIL import Image

REPO_ROOT = Path(__file__).resolve().parent.parent
CACHE_HOME = Path(os.environ.get('XDG_CACHE_HOME') or Path.home() / '.cache')
DATA_HOME = Path(os.environ.get('XDG_DATA_HOME') or Path.home() / '.local' / 'share')
BACKGROUND_DIR = REPO_ROOT / 'assets' / 'wallpaper'
CACHE_DIR = CACHE_HOME / 'forge-core-wallpaper'
STATE_FILE = CACHE_DIR / 'state.json'
LOCK_FILE = CACHE_DIR / 'rotator.lock'
THEME_MODE_FILE = DATA_HOME / 'forge-core' / 'icon-theme-mode'
FORGE_ICON_THEME = 'Forge-Core'
ROTATION_SECONDS = 30 * 60
POLL_SECONDS = 60
GENERATED_GLOB = 'wallpaper-*.png'
KEEP_GENERATED = 3
DISPLAY_RE = re.compile(r'^(?P<name>\S+) connected(?: primary)? (?P<w>\d+)x(?P<h>\d+)\+(?P<x>-?\d+)\+(?P<y>-?\d+)')


def merge_mirrors(
    active: list[tuple[str, int, int, int, int]],
) -> list[tuple[str, int, int, int, int]]:
    """Collapse outputs that share an origin into one logical screen.

    Mirrored outputs report the same position, so keeping both would paste two
    images over each other; the larger area wins because it spans the framebuffer.
    """
    groups: dict[tuple[int, int], tuple[str, int, int, int, int]] = {}
    for monitor in active:
        _, width, height, x, y = monitor
        current = groups.get((x, y))
        if current is None or width * height > current[1] * current[2]:
            groups[(x, y)] = monitor
    return sorted(groups.values(), key=lambda monitor: (monitor[4], monitor[3]))


def displays() -> list[tuple[str, int, int, int, int]]:
    result = subprocess.run(['xrandr', '--current'], check=True, text=True, capture_output=True)
    active = []
    for line in result.stdout.splitlines():
        match = DISPLAY_RE.match(line)
        if match:
            active.append((match['name'], int(match['w']), int(match['h']), int(match['x']), int(match['y'])))
    return merge_mirrors(active)


def fit_cover(source: Image.Image, width: int, height: int) -> Image.Image:
    scale = max(width / source.width, height / source.height)
    scaled = source.resize((round(source.width * scale), round(source.height * scale)), Image.Resampling.LANCZOS)
    left = (scaled.width - width) // 2
    top = (scaled.height - height) // 2
    return scaled.crop((left, top, left + width, top + height))


def set_wallpaper(path: Path) -> None:
    uri = path.as_uri()
    for key in ('picture-uri', 'picture-uri-dark'):
        subprocess.run(['gsettings', 'set', 'org.gnome.desktop.background', key, uri], check=True)
    subprocess.run(['gsettings', 'set', 'org.gnome.desktop.background', 'picture-options', 'spanned'], check=True)


def forge_active() -> bool:
    try:
        if THEME_MODE_FILE.is_file() and THEME_MODE_FILE.read_text().strip() != FORGE_ICON_THEME:
            return False
        result = subprocess.run(
            ['gsettings', 'get', 'org.gnome.desktop.interface', 'icon-theme'],
            check=False,
            text=True,
            capture_output=True,
        )
        return result.returncode == 0 and result.stdout.strip().strip("'\"") == FORGE_ICON_THEME
    except OSError:
        return False


def current_wallpaper() -> str:
    try:
        result = subprocess.run(
            ['gsettings', 'get', 'org.gnome.desktop.background', 'picture-uri'],
            check=False,
            text=True,
            capture_output=True,
        )
        return result.stdout.strip().strip("'\"") if result.returncode == 0 else ''
    except OSError:
        return ''


def load_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def render(active: list[tuple[str, int, int, int, int]]) -> None:
    sources = sorted(BACKGROUND_DIR.glob('*.png'))
    if not sources:
        raise RuntimeError(f'No PNG backgrounds in {BACKGROUND_DIR}')
    randomizer = secrets.SystemRandom()
    selected = randomizer.sample(sources, k=min(len(active), len(sources)))
    if len(selected) < len(active):
        selected.extend(randomizer.choices(sources, k=len(active) - len(selected)))

    min_x = min(item[3] for item in active)
    min_y = min(item[4] for item in active)
    max_x = max(item[3] + item[1] for item in active)
    max_y = max(item[4] + item[2] for item in active)
    canvas = Image.new('RGB', (max_x - min_x, max_y - min_y), 'black')
    for monitor, source_path in zip(active, selected):
        _, width, height, x, y = monitor
        with Image.open(source_path).convert('RGB') as source:
            canvas.paste(fit_cover(source, width, height), (x - min_x, y - min_y))

    output = CACHE_DIR / f'wallpaper-{int(time.time())}.png'
    canvas.save(output, optimize=True)
    set_wallpaper(output)
    STATE_FILE.write_text(json.dumps({
        'last_rotation': time.time(),
        'topology': [list(item) for item in active],
        'wallpaper': str(output),
    }))
    prune_generated(output)


def generated_wallpapers() -> list[Path]:
    """Return the regular PNGs this script generated, newest first."""
    eligible: list[tuple[float, Path]] = []
    for path in CACHE_DIR.glob(GENERATED_GLOB):
        try:
            if path.is_symlink() or not path.is_file():
                continue
            eligible.append((path.stat().st_mtime, path))
        except OSError:
            continue
    eligible.sort(key=lambda item: item[0], reverse=True)
    return [path for _, path in eligible]


def prune_generated(current: Path | None = None) -> int:
    """Keep the wallpaper in use plus the newest ones, drop the rest."""
    eligible = generated_wallpapers()
    keep: list[Path] = []
    if current is not None and current in eligible:
        keep.append(current)
    for path in eligible:
        if len(keep) >= KEEP_GENERATED:
            break
        if path not in keep:
            keep.append(path)

    removed = 0
    for path in eligible:
        if path in keep:
            continue
        try:
            path.unlink()
            removed += 1
        except OSError:
            continue
    return removed


def main() -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with LOCK_FILE.open('w') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return
        startup_state = load_state().get('wallpaper', '')
        prune_generated(
            Path(startup_state) if isinstance(startup_state, str) and startup_state else None)
        while True:
            if not forge_active():
                return
            active = displays()
            if active:
                state = load_state()
                topology = [list(item) for item in active]
                topology_changed = state.get('topology') != topology
                due = time.time() - state.get('last_rotation', 0) >= ROTATION_SECONDS
                expected_wallpaper = state.get('wallpaper', '')
                expected_uri = ''
                if isinstance(expected_wallpaper, str) and expected_wallpaper:
                    try:
                        expected_uri = Path(expected_wallpaper).as_uri()
                    except ValueError:
                        expected_uri = ''
                wallpaper_changed = current_wallpaper() != expected_uri
                if topology_changed or due or wallpaper_changed:
                    render(active)
            time.sleep(POLL_SECONDS)


if __name__ == '__main__':
    main()
