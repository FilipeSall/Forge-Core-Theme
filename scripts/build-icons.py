#!/usr/bin/env python3
"""Gera o icon theme Forge Core em icon-theme/<dir>/ a partir de assets/icons/manifest.json."""

import json
import os
import shutil
import sys

from PIL import Image

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(REPO, "assets", "icons")
MANIFEST = os.path.join(ASSETS, "manifest.json")
SYMBOLIC = os.path.join(ASSETS, "symbolic")


def load_manifest():
    with open(MANIFEST, encoding="utf-8") as handle:
        return json.load(handle)


def content_bbox(image, threshold):
    alpha = image.split()[-1].point(lambda v: 255 if v > threshold else 0)
    bbox = alpha.getbbox()
    if bbox is None:
        raise ValueError("asset totalmente transparente")
    return bbox


def fill_for(size, table):
    return table.get(str(size), table["default"])


def reference_width(manifest):
    reference = os.path.join(ASSETS, manifest["referenceSource"])
    if not os.path.isfile(reference):
        sys.exit(f"referenceSource ausente: {reference}")
    image = Image.open(reference).convert("RGBA")
    left, _, right, _ = content_bbox(image, manifest["alphaTrimThreshold"])
    return right - left


def render(source_path, size, fill, threshold, reference_w):
    source = Image.open(source_path).convert("RGBA")
    left, top, right, bottom = content_bbox(source, threshold)
    content_w = right - left
    content_h = bottom - top

    scale = (size * fill) / (reference_w or max(content_w, content_h))

    scaled = source.resize(
        (max(1, round(source.width * scale)), max(1, round(source.height * scale))),
        Image.LANCZOS,
    )

    offset_x = round((size - content_w * scale) / 2 - left * scale)
    offset_y = round((size - content_h * scale) / 2 - top * scale)

    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    canvas.alpha_composite(scaled, dest=(max(0, offset_x), max(0, offset_y)),
                           source=(max(0, -offset_x), max(0, -offset_y)))
    return canvas


def symbolic_contexts():
    if not os.path.isdir(SYMBOLIC):
        return []
    return sorted(
        name for name in os.listdir(SYMBOLIC)
        if os.path.isdir(os.path.join(SYMBOLIC, name))
    )


def directory_entries(manifest):
    contexts = sorted({icon["context"] for icon in manifest["icons"]})
    entries = [f"{size}x{size}/{context}"
               for size in manifest["sizes"]
               for context in contexts]
    entries += [f"scalable/{context}" for context in symbolic_contexts()]
    return entries


def write_index_theme(theme_root, manifest):
    theme = manifest["theme"]
    scalable_from = manifest["scalableFrom"]
    min_size, max_size = manifest["scalableRange"]
    contexts = sorted({icon["context"] for icon in manifest["icons"]})

    lines = [
        "[Icon Theme]",
        f"Name={theme['name']}",
        f"Comment={theme['comment']}",
        f"Inherits={','.join(theme['inherits'])}",
        f"Example={theme['example']}",
        f"Directories={','.join(directory_entries(manifest))}",
        "",
    ]

    for context in symbolic_contexts():
        lines.append(f"[scalable/{context}]")
        lines.append("Size=16")
        lines.append(f"Context={context.capitalize()}")
        lines.append("Type=Scalable")
        lines.append("MinSize=8")
        lines.append("MaxSize=512")
        lines.append("")

    for size in manifest["sizes"]:
        for context in contexts:
            lines.append(f"[{size}x{size}/{context}]")
            lines.append(f"Size={size}")
            lines.append(f"Context={context.capitalize()}")
            if size == scalable_from:
                lines.append("Type=Scalable")
                lines.append(f"MinSize={min_size}")
                lines.append(f"MaxSize={max_size}")
            else:
                lines.append("Type=Fixed")
            lines.append("")

    with open(os.path.join(theme_root, "index.theme"), "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines))


def build():
    manifest = load_manifest()
    theme_root = os.path.join(REPO, "icon-theme", manifest["theme"]["directory"])

    if os.path.isdir(theme_root):
        shutil.rmtree(theme_root)
    os.makedirs(theme_root)

    threshold = manifest["alphaTrimThreshold"]
    reference_w = reference_width(manifest)
    written = 0
    linked = 0

    for icon in manifest["icons"]:
        source_path = os.path.join(ASSETS, icon["source"])
        if not os.path.isfile(source_path):
            sys.exit(f"asset ausente: {source_path}")

        for size in manifest["sizes"]:
            target_dir = os.path.join(theme_root, f"{size}x{size}", icon["context"])
            os.makedirs(target_dir, exist_ok=True)

            target = os.path.join(target_dir, f"{icon['name']}.png")
            render(
                source_path,
                size,
                icon.get("fill", fill_for(size, manifest["contentFill"])),
                threshold,
                None if "fill" in icon else reference_w,
            ).save(target, "PNG", optimize=True)
            written += 1

            for alias in icon.get("aliases", []):
                alias_path = os.path.join(target_dir, f"{alias}.png")
                if os.path.lexists(alias_path):
                    os.remove(alias_path)
                os.symlink(f"{icon['name']}.png", alias_path)
                linked += 1

    symbolic = 0
    for context in symbolic_contexts():
        source_dir = os.path.join(SYMBOLIC, context)
        target_dir = os.path.join(theme_root, "scalable", context)
        os.makedirs(target_dir, exist_ok=True)
        for name in sorted(os.listdir(source_dir)):
            if name.endswith(".svg"):
                shutil.copyfile(os.path.join(source_dir, name), os.path.join(target_dir, name))
                symbolic += 1

    write_index_theme(theme_root, manifest)

    print(f"escala ancorada em {manifest['referenceSource']} (largura de conteudo {reference_w}px)")
    print(f"tema gerado em {theme_root}")
    print(f"  {written} PNGs, {linked} aliases (symlink relativo), {symbolic} simbolicos, index.theme")
    return theme_root


if __name__ == "__main__":
    build()
