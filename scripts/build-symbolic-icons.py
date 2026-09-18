#!/usr/bin/env python3
"""Gera a familia de icones simbolicos Forge Core em assets/icons/symbolic/.

Icone simbolico e recolorido pelo St/GTK trocando so o `fill` de `rect`, `circle`
e `path` pela cor de primeiro plano; `.error`, `.warning` e `.success` recebem as
cores desses estados. Stroke nao e recolorido, entao toda a geometria aqui e
feita de formas preenchidas, e o vermelho Forge Core entra via classe `error`.
"""

from __future__ import annotations

import math
import os
import shutil

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "assets", "icons", "symbolic")
SIZE = 16


def fmt(value: float) -> str:
    return f"{round(value, 2):g}"


def poly(points: list[tuple[float, float]]) -> str:
    head = f"M{fmt(points[0][0])} {fmt(points[0][1])}"
    rest = "".join(f"L{fmt(x)} {fmt(y)}" for x, y in points[1:])
    return f"{head}{rest}Z"


def offset_line(a, b, distance):
    dx, dy = b[0] - a[0], b[1] - a[1]
    length = math.hypot(dx, dy)
    nx, ny = -dy / length * distance, dx / length * distance
    return (a[0] + nx, a[1] + ny), (b[0] + nx, b[1] + ny)


def intersect(p1, p2, p3, p4):
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    x4, y4 = p4
    den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(den) < 1e-6:
        return p2
    px = ((x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)) / den
    py = ((x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)) / den
    return px, py


def side(points, distance):
    segments = [offset_line(points[i], points[i + 1], distance) for i in range(len(points) - 1)]
    result = [segments[0][0]]
    for first, second in zip(segments, segments[1:]):
        result.append(intersect(first[0], first[1], second[0], second[1]))
    result.append(segments[-1][1])
    return result


def thick(points: list[tuple[float, float]], width: float) -> str:
    half = width / 2
    left = side(points, half)
    right = side(points, -half)
    return poly(left + list(reversed(right)))


def chamfered(x, y, w, h, cut) -> list[tuple[float, float]]:
    return [
        (x + cut, y), (x + w - cut, y), (x + w, y + cut), (x + w, y + h - cut),
        (x + w - cut, y + h), (x + cut, y + h), (x, y + h - cut), (x, y + cut),
    ]


def ring(outer: list[tuple[float, float]], inner: list[tuple[float, float]]) -> str:
    return poly(outer) + poly(list(reversed(inner)))


def path(d: str, klass: str | None = None, opacity: float | None = None) -> str:
    attrs = [f'd="{d}"']
    if klass:
        attrs.append(f'class="{klass}"')
    if opacity is not None:
        attrs.append(f'fill-opacity="{fmt(opacity)}"')
    attrs.append('fill-rule="evenodd"')
    return f'  <path {" ".join(attrs)}/>'


def svg(*parts: str) -> str:
    body = "\n".join(p for p in parts if p)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{SIZE}" height="{SIZE}" '
        f'viewBox="0 0 {SIZE} {SIZE}">\n{body}\n</svg>\n'
    )


def slash() -> str:
    return path(thick([(3, 13), (13, 3)], 1.9), "error")


def wifi(level: int, dimmed: bool = False) -> list[str]:
    parts = [path(poly(chamfered(6.6, 12, 2.8, 2.8, 0.8)), None, 1 if level >= 1 else 0.28)]
    arcs = [(2.9, 9.4), (5.2, 6.1), (7.5, 2.8)]
    for index, (half, apex) in enumerate(arcs, start=2):
        opacity = 1 if level >= index else 0.28
        chevron = [(8 - half, apex + half), (8, apex), (8 + half, apex + half)]
        parts.append(path(thick(chevron, 1.4), None, 0.5 if dimmed else opacity))
    return parts


def battery(level: int, charging: bool, charged: bool = False) -> str:
    body = ring(chamfered(0.8, 4.2, 12.1, 7.6, 1.4), chamfered(2.1, 5.5, 9.5, 5, 0.8))
    cap = poly(chamfered(13.4, 6.4, 2, 3.2, 0.6))
    parts = [path(body + cap)]
    if level > 0:
        width = 8.1 * level / 100
        parts.append(path(poly(chamfered(2.8, 6.2, max(1.1, width), 3.6, 0.5))))
    if charging:
        bolt = poly([(8.4, 3.6), (5.6, 8.6), (7.4, 8.6), (6.7, 12.4), (10.4, 7.2), (8.5, 7.2), (9.6, 3.6)])
        parts.append(path(bolt, "error"))
    elif charged:
        parts.append(path(poly(chamfered(13.4, 6.4, 2, 3.2, 0.6)), "error"))
    return svg(*parts)


def speaker() -> str:
    return poly([(1.2, 6.2), (4.4, 6.2), (8.1, 2.6), (8.1, 13.4), (4.4, 9.8), (1.2, 9.8)])


def volume(level: int, over: bool = False) -> str:
    parts = [path(speaker())]
    waves = [(9.6, 2.2), (12, 3.6), (14.4, 5)]
    for index, (x, half) in enumerate(waves, start=1):
        if level < index:
            continue
        klass = "error" if over and index == 3 else None
        chevron = [(x - half * 0.72, 8 - half), (x, 8), (x - half * 0.72, 8 + half)]
        parts.append(path(thick(chevron, 1.35), klass))
    return svg(*parts)


def microphone(level: int, muted: bool = False) -> str:
    capsule = ring(chamfered(5.5, 1.1, 5, 8.4, 1.4), chamfered(6.9, 2.5, 2.2, 5.6, 0.7))
    stand = poly(chamfered(7.1, 11.6, 1.8, 3.3, 0.5)) + poly(chamfered(4.4, 13.9, 7.2, 1.6, 0.5))
    arc = thick([(3.1, 8.1), (3.1, 9.8), (5.6, 11.9), (10.4, 11.9), (12.9, 9.8), (12.9, 8.1)], 1.6)
    parts = [path(capsule + stand), path(arc, None, 1 if level >= 1 else 0.3)]
    if muted:
        parts.append(slash())
    elif level >= 2:
        parts.append(path(poly(chamfered(13.6, 3.4, 1.8, 1.8, 0.5)), "error", 1 if level >= 3 else 0.5))
    return svg(*parts)


def headphones() -> str:
    arc = thick([(2.4, 11), (2.4, 7.2), (5.4, 3.4), (10.6, 3.4), (13.6, 7.2), (13.6, 11)], 1.7)
    cups = poly(chamfered(0.9, 9.6, 3.3, 5.5, 1)) + poly(chamfered(11.8, 9.6, 3.3, 5.5, 1))
    return svg(path(arc), path(cups))


def brightness() -> str:
    core = ring(chamfered(4.9, 4.9, 6.2, 6.2, 1.8), chamfered(6.6, 6.6, 2.8, 2.8, 0.8))
    rays = []
    for index in range(8):
        angle = math.radians(index * 45)
        cx, cy = 8 + math.cos(angle) * 6.4, 8 + math.sin(angle) * 6.4
        dx, dy = math.cos(angle) * 1.1, math.sin(angle) * 1.1
        rays.append(thick([(cx - dx, cy - dy), (cx + dx, cy + dy)], 1.7))
    return svg(path(core), path("".join(rays)))


def bluetooth(state: str) -> str:
    stem = thick([(8, 1.6), (8, 14.4)], 1.5)
    upper = thick([(5.4, 5.4), (10.9, 10.3), (8, 12.8)], 1.5)
    lower = thick([(5.4, 10.6), (10.9, 5.7), (8, 3.2)], 1.5)
    if state == "active":
        return svg(path(stem + upper + lower))
    if state == "acquiring":
        return svg(path(stem + upper + lower, None, 0.5), path(poly(chamfered(12.2, 12.2, 3, 3, 0.8)), "error"))
    return svg(path(stem + upper + lower, None, 0.55), slash())


def night_light() -> str:
    outer = chamfered(1.6, 1.6, 12.8, 12.8, 3.7)
    inner = [(x + 5.2, y - 0.8) for x, y in chamfered(1.6, 1.6, 12.8, 12.8, 3.7)]
    crescent = path(ring(outer, inner))
    spark = path(poly(chamfered(11.6, 11.4, 2.4, 2.4, 0.7)), "error")
    return svg(crescent, spark)


def dark_mode() -> str:
    outer = chamfered(2.2, 2.2, 11.6, 11.6, 3.3)
    inner = chamfered(3.9, 3.9, 8.2, 8.2, 2.4)
    half = poly([(8, 3.9), (12.1, 6.3), (12.1, 9.7), (8, 12.1)])
    return svg(path(ring(outer, inner)), path(half))


def airplane() -> str:
    body = poly([
        (8, 0.9), (9.4, 6.2), (15.2, 9.6), (15.2, 11.4), (9.4, 9.9), (9.1, 13.1),
        (11.2, 14.8), (11.2, 15.4), (8, 14.4), (4.8, 15.4), (4.8, 14.8), (6.9, 13.1),
        (6.6, 9.9), (0.8, 11.4), (0.8, 9.6), (6.6, 6.2),
    ])
    return svg(path(body))


def power_profile(level: int) -> str:
    bars = [(2.2, 11.3, 11.6), (3.9, 7.9, 8.2), (5.6, 4.5, 4.8)]
    parts = []
    for index, (x, y, width) in enumerate(bars, start=1):
        lit = level >= index
        klass = "error" if lit and index == 3 and level == 3 else None
        parts.append(path(poly(chamfered(x, y, width, 2.2, 0.6)), klass, 1 if lit else 0.28))
    return svg(*parts)


def screenshooter() -> str:
    body = ring(chamfered(0.9, 3.4, 14.2, 10.2, 1.8), chamfered(2.4, 4.9, 11.2, 7.2, 1.2))
    hump = poly(chamfered(5.2, 1.4, 5.6, 2.4, 0.7))
    lens = poly(chamfered(5.9, 6.2, 4.2, 4.2, 1.2))
    led = poly(chamfered(11.9, 5.7, 1.7, 1.7, 0.5))
    return svg(path(body + hump), path(lens), path(led, "error"))


def lock_screen() -> str:
    shackle = thick([(4.6, 7.4), (4.6, 4.6), (8, 2.2), (11.4, 4.6), (11.4, 7.4)], 1.7)
    body = ring(chamfered(2.6, 7.2, 10.8, 7.4, 1.4), chamfered(4.1, 8.7, 7.8, 4.4, 0.8))
    keyhole = poly(chamfered(7.2, 9.6, 1.6, 2.6, 0.4))
    return svg(path(shackle), path(body), path(keyhole, "error"))


def shutdown() -> str:
    outer = chamfered(2.1, 2.1, 11.8, 11.8, 3.4)
    inner = chamfered(4.2, 4.2, 7.6, 7.6, 2.2)
    gap = poly([(6.4, 1.4), (9.6, 1.4), (9.6, 5.2), (6.4, 5.2)])
    stem = poly(chamfered(7.1, 1.1, 1.8, 6.4, 0.5))
    return svg(path(ring(outer, inner) + gap), path(stem, "error"))


def settings() -> str:
    teeth = []
    for index in range(6):
        angle = math.radians(index * 60)
        cx, cy = 8 + math.cos(angle) * 6.1, 8 + math.sin(angle) * 6.1
        dx, dy = math.cos(angle) * 1.4, math.sin(angle) * 1.4
        teeth.append(thick([(cx - dx, cy - dy), (cx + dx, cy + dy)], 2.6))
    body = ring(chamfered(3.1, 3.1, 9.8, 9.8, 2.8), chamfered(5.9, 5.9, 4.2, 4.2, 1.2))
    return svg(path("".join(teeth)), path(body))


def go_next() -> str:
    return svg(path(thick([(5.8, 3.4), (10.4, 8), (5.8, 12.6)], 2)))


def go_previous() -> str:
    return svg(path(thick([(10.2, 3.4), (5.6, 8), (10.2, 12.6)], 2)))


def object_select() -> str:
    return svg(path(thick([(2.8, 8.4), (6.2, 11.8), (13.2, 4.2)], 2.1), "error"))


def wired(state: str) -> str:
    port = ring(chamfered(1.4, 5.6, 13.2, 8.4, 1.6), chamfered(3.1, 7.3, 9.8, 5, 0.9))
    prongs = poly(chamfered(4.4, 1.8, 1.9, 4.2, 0.5)) + poly(chamfered(9.7, 1.8, 1.9, 4.2, 0.5))
    if state == "connected":
        return svg(path(port + prongs), path(poly(chamfered(6.6, 8.6, 2.8, 2.4, 0.6)), "error"))
    if state == "acquiring":
        return svg(path(port + prongs, None, 0.55))
    return svg(path(port + prongs, None, 0.55), slash())


def wireless(name: str) -> str:
    if name == "excellent":
        return svg(*wifi(4))
    if name == "good":
        return svg(*wifi(3))
    if name == "ok":
        return svg(*wifi(2))
    if name == "weak":
        return svg(*wifi(1))
    if name == "none":
        return svg(*wifi(0), path(poly(chamfered(6.4, 11.4, 3.2, 3.2, 0.9)), "error"))
    if name == "acquiring":
        return svg(*wifi(4, dimmed=True))
    if name == "offline":
        return svg(*wifi(1), slash())
    return svg(*wifi(0), slash())


def recent() -> str:
    dial = ring(chamfered(1.5, 1.5, 13, 13, 3.8), chamfered(3.2, 3.2, 9.6, 9.6, 2.8))
    hands = thick([(10.6, 9.8), (8, 8.2), (8, 4.4)], 1.6)
    return svg(path(dial), path(hands, "error"))


def starred() -> str:
    points = []
    for index in range(10):
        angle = math.radians(-90 + index * 36)
        radius = 7.1 if index % 2 == 0 else 3.1
        points.append((8 + math.cos(angle) * radius, 8 + math.sin(angle) * radius))
    apex = poly([points[9], points[0], points[1]])
    return svg(path(poly(points)), path(apex, "error"))


def home() -> str:
    outline = thick([
        (2, 10.6), (2, 7.7), (8, 2.3), (14, 7.7), (14, 13.7),
        (9.7, 13.7), (9.7, 9.6), (6.3, 9.6), (6.3, 13.7), (2, 13.7), (2, 10.6),
    ], 1.6)
    door = poly(chamfered(6.5, 9.8, 3, 3.9, 0.8))
    return svg(path(outline), path(door, "error"))


def desktop() -> str:
    screen = ring(chamfered(1.4, 2.6, 13.2, 9.2, 1.6), chamfered(3, 4.2, 10, 6, 1))
    stand = thick([(8, 11.8), (8, 13.4)], 1.6) + thick([(5.2, 13.9), (10.8, 13.9)], 1.6)
    cursor = poly(chamfered(4.4, 7.2, 2.6, 2.2, 0.6))
    return svg(path(screen), path(stand), path(cursor, "error"))


def documents() -> str:
    sheet = thick([
        (3.6, 9), (3.6, 2.2), (9.4, 2.2), (12.6, 5.4), (12.6, 13.8), (3.6, 13.8), (3.6, 9),
    ], 1.5)
    lines = thick([(6, 9.2), (10.2, 9.2)], 1.3) + thick([(6, 11.4), (10.2, 11.4)], 1.3)
    fold = thick([(9.4, 2.8), (9.4, 5.4), (12, 5.4)], 1.4)
    return svg(path(sheet), path(lines), path(fold, "error"))


def download() -> str:
    stem = thick([(8, 2.2), (8, 8.8)], 1.7)
    base = thick([(3, 13.4), (13, 13.4)], 1.6)
    arrow = thick([(4.9, 7.4), (8, 10.5), (11.1, 7.4)], 1.7)
    return svg(path(stem), path(base), path(arrow, "error"))


def pictures() -> str:
    frame = ring(chamfered(1.4, 2.4, 13.2, 11.2, 1.6), chamfered(3, 4, 10, 8, 1))
    ridge = thick([(4.2, 11.3), (7.5, 8), (12.3, 11.3)], 1.4)
    lens = poly(chamfered(4.6, 5.3, 2.6, 2.6, 0.8))
    return svg(path(frame), path(ridge), path(lens, "error"))


def music() -> str:
    staff = thick([(6.5, 11.6), (6.5, 4.1), (12.4, 2.9), (12.4, 10.4)], 1.5)
    heads = poly(chamfered(3.2, 10.4, 3.4, 3.4, 1)) + poly(chamfered(9.1, 9.2, 3.4, 3.4, 1))
    beam = thick([(6.5, 7.1), (12.4, 5.9)], 1.3)
    return svg(path(staff), path(heads), path(beam, "error"))


def videos() -> str:
    frame = ring(chamfered(1.4, 2.8, 13.2, 10.4, 1.6), chamfered(3, 4.4, 10, 7.2, 1))
    play = poly([(6.7, 5.7), (10.8, 8), (6.7, 10.3)])
    return svg(path(frame), path(play, "error"))


def trash(full: bool = False) -> str:
    body = thick([(4.2, 5.8), (4.9, 13.8), (11.1, 13.8), (11.8, 5.8)], 1.5)
    if full:
        load = poly(chamfered(5.7, 8.4, 4.8, 3.8, 1.1))
    else:
        load = thick([(6.6, 7.9), (6.9, 11.7)], 1.3) + thick([(9.4, 7.9), (9.1, 11.7)], 1.3)
    lid = thick([(2.6, 5.2), (13.4, 5.2)], 1.6) + thick([(6.1, 2.6), (9.9, 2.6)], 1.6)
    return svg(path(body), path(load), path(lid, "error"))


def icons() -> dict[str, dict[str, str]]:
    status = {}
    for name in ("excellent", "good", "ok", "weak", "none"):
        status[f"network-wireless-signal-{name}-symbolic"] = wireless(name)
    status["network-wireless-symbolic"] = wireless("excellent")
    status["network-wireless-acquiring-symbolic"] = wireless("acquiring")
    status["network-wireless-offline-symbolic"] = wireless("offline")
    status["network-wireless-disabled-symbolic"] = wireless("disabled")
    status["network-wired-acquiring-symbolic"] = wired("acquiring")
    status["network-wired-disconnected-symbolic"] = wired("disconnected")

    for level, name in ((3, "high"), (2, "medium"), (1, "low")):
        status[f"audio-volume-{name}-symbolic"] = volume(level)
    status["audio-volume-overamplified-symbolic"] = volume(3, over=True)
    status["audio-volume-muted-symbolic"] = svg(path(speaker()), slash())
    for level, name in ((3, "high"), (2, "medium"), (1, "low")):
        status[f"microphone-sensitivity-{name}-symbolic"] = microphone(level)
    status["microphone-sensitivity-muted-symbolic"] = microphone(0, muted=True)

    for fill in range(0, 101, 10):
        status[f"battery-level-{fill}-symbolic"] = battery(fill, False)
        status[f"battery-level-{fill}-charging-symbolic"] = battery(fill, True)
    status["battery-level-100-charged-symbolic"] = battery(100, False, charged=True)
    status["battery-missing-symbolic"] = svg(
        path(ring(chamfered(0.8, 4.2, 12.1, 7.6, 1.4), chamfered(2.1, 5.5, 9.5, 5, 0.8))
             + poly(chamfered(13.4, 6.4, 2, 3.2, 0.6)), None, 0.55),
        slash(),
    )

    status["display-brightness-symbolic"] = brightness()
    status["bluetooth-active-symbolic"] = bluetooth("active")
    status["bluetooth-acquiring-symbolic"] = bluetooth("acquiring")
    status["bluetooth-disabled-symbolic"] = bluetooth("disabled")
    status["night-light-symbolic"] = night_light()
    status["dark-mode-symbolic"] = dark_mode()
    status["airplane-mode-symbolic"] = airplane()
    status["power-profile-power-saver-symbolic"] = power_profile(1)
    status["power-profile-balanced-symbolic"] = power_profile(2)
    status["power-profile-performance-symbolic"] = power_profile(3)

    actions = {
        "screenshooter-symbolic": screenshooter(),
        "system-lock-screen-symbolic": lock_screen(),
        "system-shutdown-symbolic": shutdown(),
        "go-next-symbolic": go_next(),
        "go-previous-symbolic": go_previous(),
        "object-select-symbolic": object_select(),
    }
    devices = {
        "network-wired-symbolic": wired("connected"),
        "audio-headphones-symbolic": headphones(),
    }
    apps = {"org.gnome.Settings-symbolic": settings()}
    status["starred-symbolic"] = starred()
    actions["document-open-recent-symbolic"] = recent()
    places = {
        "user-home-symbolic": home(),
        "user-desktop-symbolic": desktop(),
        "folder-documents-symbolic": documents(),
        "folder-download-symbolic": download(),
        "folder-pictures-symbolic": pictures(),
        "folder-music-symbolic": music(),
        "folder-videos-symbolic": videos(),
        "user-trash-symbolic": trash(),
        "user-trash-full-symbolic": trash(full=True),
    }
    return {
        "status": status,
        "actions": actions,
        "devices": devices,
        "apps": apps,
        "places": places,
    }


def build() -> None:
    shutil.rmtree(OUT, ignore_errors=True)
    total = 0
    for context, entries in icons().items():
        directory = os.path.join(OUT, context)
        os.makedirs(directory, exist_ok=True)
        for name, content in entries.items():
            with open(os.path.join(directory, f"{name}.svg"), "w", encoding="utf-8") as handle:
                handle.write(content)
            total += 1
        print(f"{context:8} {len(entries):3} icones")
    print()
    print(f"{total} icones simbolicos em {OUT}")


if __name__ == "__main__":
    build()
