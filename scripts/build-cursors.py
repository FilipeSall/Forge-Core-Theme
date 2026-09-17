#!/usr/bin/env python3
"""Gera o cursor theme Forge Core em cursor-theme/<dir>/ a partir de assets/cursors/manifest.json."""

import json
import math
import os
import shutil
import subprocess
import sys

from PIL import Image

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(REPO, "assets", "cursors")
MANIFEST = os.path.join(ASSETS, "manifest.json")
ALPHA_FLOOR = 8


def load_manifest():
    with open(MANIFEST, encoding="utf-8") as handle:
        return json.load(handle)


def content_bbox(image):
    alpha = image.getchannel("A")
    return alpha.point(lambda value: 255 if value > ALPHA_FLOOR else 0).getbbox()


def square_box(bbox, padding):
    x0, y0, x1, y1 = bbox
    side = max(x1 - x0, y1 - y0)
    side = int(round(side * (1 + 2 * padding)))
    center_x = (x0 + x1) // 2
    center_y = (y0 + y1) // 2
    left = center_x - side // 2
    top = center_y - side // 2
    return left, top, left + side, top + side


def map_hotspot(hotspot, box, size):
    left, top, right, _ = box
    side = right - left
    x = int(round((hotspot[0] - left) * size / side))
    y = int(round((hotspot[1] - top) * size / side))
    return max(0, min(size - 1, x)), max(0, min(size - 1, y))


def rotated_master(master, hotspot, angle):
    if not angle:
        return master, hotspot
    x0, y0, x1, y1 = content_bbox(master)
    radius = max(
        math.dist(hotspot, corner)
        for corner in ((x0, y0), (x1, y0), (x0, y1), (x1, y1))
    )
    side = 2 * math.ceil(radius) + 4
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    center = (side // 2, side // 2)
    canvas.paste(master, (center[0] - hotspot[0], center[1] - hotspot[1]), master)
    return canvas.rotate(-angle, resample=Image.BICUBIC, center=center), center


def render_master(master, hotspot, padding, size, angle):
    box = square_box(content_bbox(master), padding)
    source = master
    if angle:
        source = master.rotate(-angle, resample=Image.BICUBIC, center=hotspot)
    frame = source.crop(box).resize((size, size), Image.LANCZOS)
    return frame, map_hotspot(hotspot, box, size)


def render_prerendered(path, hotspot, size):
    image = Image.open(path).convert("RGBA")
    if max(image.size) == size:
        return image, hotspot
    scale = size / max(image.size)
    target = (max(1, round(image.width * scale)), max(1, round(image.height * scale)))
    resized = image.resize(target, Image.LANCZOS)
    return resized, (round(hotspot[0] * scale), round(hotspot[1] * scale))


def build_cursor(spec, manifest, work_dir):
    sizes = manifest["sizes"]
    padding = manifest["content_padding"]
    animation = spec.get("animation")
    lines = []

    if "master" in spec:
        master = Image.open(os.path.join(ASSETS, spec["master"])).convert("RGBA")
        master, hotspot = rotated_master(master, tuple(spec["hotspot"]), spec.get("rotate", 0))
        frame_count = animation["frames"] if animation else 1
        for size in sizes:
            for index in range(frame_count):
                angle = index * 360 / frame_count if animation else 0
                frame, spot = render_master(master, hotspot, padding, size, angle)
                name = f"{spec['id']}-{size}-{index}.png"
                frame.save(os.path.join(work_dir, name))
                line = f"{size} {spot[0]} {spot[1]} {name}"
                if animation:
                    line += f" {animation['delay_ms']}"
                lines.append(line)
        return lines

    frames = spec["frames"]
    available = sorted(int(key) for key in frames)
    for size in sizes:
        source_size = min(available, key=lambda value: (abs(value - size), -value))
        if size > max(available):
            continue
        path = os.path.join(ASSETS, frames[str(source_size)])
        frame, spot = render_prerendered(path, tuple(spec["hotspot"]), size)
        name = f"{spec['id']}-{size}-0.png"
        frame.save(os.path.join(work_dir, name))
        lines.append(f"{size} {spot[0]} {spot[1]} {name}")
    return lines


def write_index_theme(theme_root, theme):
    with open(os.path.join(theme_root, "index.theme"), "w", encoding="utf-8") as handle:
        handle.write("[Icon Theme]\n")
        handle.write(f"Name={theme['name']}\n")
        handle.write(f"Comment={theme['comment']}\n")
        handle.write(f"Inherits={theme['inherits']}\n")
    with open(os.path.join(theme_root, "cursor.theme"), "w", encoding="utf-8") as handle:
        handle.write("[Icon Theme]\n")
        handle.write(f"Name={theme['name']}\n")
        handle.write(f"Inherits={theme['inherits']}\n")


def build():
    if shutil.which("xcursorgen") is None:
        sys.exit("xcursorgen nao encontrado: instale o pacote x11-apps")

    manifest = load_manifest()
    theme = manifest["theme"]
    theme_root = os.path.join(REPO, "cursor-theme", theme["dir_name"])
    cursors_dir = os.path.join(theme_root, "cursors")
    work_dir = os.path.join(REPO, "cursor-theme", ".build")

    shutil.rmtree(theme_root, ignore_errors=True)
    shutil.rmtree(work_dir, ignore_errors=True)
    os.makedirs(cursors_dir)
    os.makedirs(work_dir)

    total_names = 0
    for spec in manifest["cursors"]:
        lines = build_cursor(spec, manifest, work_dir)
        config = os.path.join(work_dir, f"{spec['id']}.cursor")
        with open(config, "w", encoding="utf-8") as handle:
            handle.write("\n".join(lines) + "\n")

        primary = spec["names"][0]
        output = os.path.join(cursors_dir, primary)
        subprocess.run(
            ["xcursorgen", os.path.basename(config), output],
            cwd=work_dir,
            check=True,
        )

        for alias in spec["names"][1:]:
            link = os.path.join(cursors_dir, alias)
            if os.path.lexists(link):
                os.remove(link)
            os.symlink(primary, link)

        total_names += len(spec["names"])
        frames = len(lines)
        print(f"{spec['id']:10} {len(spec['names']):2} nomes  {frames:3} imagens")

    write_index_theme(theme_root, theme)
    shutil.rmtree(work_dir, ignore_errors=True)

    print()
    print(f"{len(manifest['cursors'])} cursores, {total_names} nomes em {theme_root}")


if __name__ == "__main__":
    build()
