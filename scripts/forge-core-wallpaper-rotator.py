#!/usr/bin/env python3
"""Rotate Forge Core backgrounds, using a distinct image per active monitor."""

from __future__ import annotations

import fcntl
import json
import secrets
import re
import subprocess
import time
from pathlib import Path

from PIL import Image

BACKGROUND_DIR = Path('/home/sea/projetos/forge-core/assets/wallpaper')
CACHE_DIR = Path('/home/sea/.cache/forge-core-wallpaper')
STATE_FILE = CACHE_DIR / 'state.json'
LOCK_FILE = CACHE_DIR / 'rotator.lock'
ROTATION_SECONDS = 30 * 60
POLL_SECONDS = 60
DISPLAY_RE = re.compile(r'^(?P<name>\S+) connected(?: primary)? (?P<w>\d+)x(?P<h>\d+)\+(?P<x>-?\d+)\+(?P<y>-?\d+)')


def displays() -> list[tuple[str, int, int, int, int]]:
    result = subprocess.run(['xrandr', '--current'], check=True, text=True, capture_output=True)
    active = []
    for line in result.stdout.splitlines():
        match = DISPLAY_RE.match(line)
        if match:
            active.append((match['name'], int(match['w']), int(match['h']), int(match['x']), int(match['y'])))
    return active


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
    STATE_FILE.write_text(json.dumps({'last_rotation': time.time(), 'topology': active, 'wallpaper': str(output)}))


def main() -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with LOCK_FILE.open('w') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return
        while True:
            active = displays()
            if active:
                state = load_state()
                topology_changed = state.get('topology') != active
                due = time.time() - state.get('last_rotation', 0) >= ROTATION_SECONDS
                if topology_changed or due:
                    render(active)
            time.sleep(POLL_SECONDS)


if __name__ == '__main__':
    main()
