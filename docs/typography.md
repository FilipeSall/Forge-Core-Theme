# Forge Core Typography

## Font system

| Family | Role | Weights |
| --- | --- | --- |
| IBM Plex Sans | Functional interface | 400 regular, 500 medium, 600 semibold |
| Oxanium | Forge Core branding accent | 500 titles, 600 prominent headings |
| JetBrains Mono | Technical and monospace content | 400 regular, 500 medium |

Use IBM Plex Sans for functional content. Use Oxanium only as a typographic
accent. Use JetBrains Mono for technical content.

## Roles

IBM Plex Sans is the GNOME, GTK, document, menu, notification, and regular title
font. Oxanium is not a global UI font: it is reserved for explicit Forge Core
branding, HUDs, and future specialized headings. JetBrains Mono is the GNOME
monospace font and the code/terminal font for Warp and VS Code.

Avoid excess bold. Normal copy uses IBM Plex Sans 400; important labels use 500;
functional headings use 600. Oxanium uses 500 for Forge Core titles and 600 for
important headings. JetBrains Mono uses 400 for code and terminal content, and
500 for important technical information.

## Installation

Run `./scripts/install-fonts.sh`. It installs missing fonts in
`~/.local/share/fonts/Forge-Core`, rebuilds fontconfig, and verifies exact family
resolution. Font binaries are not committed: upstream official sources and OFL
licensing are recorded in `assets/fonts/README.md` and `config/typography.conf`.

## GNOME configuration

`./scripts/apply-typography.sh` sets IBM Plex Sans 11 for interface and documents,
JetBrains Mono 13 for monospace (preserving the prior monospace scale), and IBM
Plex Sans Medium 11 for title bars. It does not tune antialiasing, hinting, RGBA,
or display scaling.

## Warp and VS Code

Warp uses `appearance.text.font_name = "JetBrains Mono"`. VS Code User Settings
already define JetBrains Mono for the editor and integrated terminal; their existing
ligature preferences are preserved.

## Forge Core Shell

The date/time dropdown is the first HUD surface: Oxanium carries the weekday,
month label, module titles and the empty-notifications state; JetBrains Mono
carries calendar numerals, week numbers, times and temperatures. Everything else,
including notification bodies and action labels, stays IBM Plex Sans. Oxanium is
still not applied to generic menus or Nautilus. In St, only the first family in
`font-family` may be quoted (`Oxanium, IBM Plex Sans, sans-serif`).

## Fontconfig and rollback

Validate with `fc-match "IBM Plex Sans"`, `fc-match "Oxanium"`, and
`fc-match "JetBrains Mono"`. To restore pre-Forge-Core GNOME typography, run
`./scripts/restore-typography.sh`. This restores only typography gsettings and
never removes user data or installed fonts.
