#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=../config/typography.conf
source "$ROOT/config/typography.conf"
"$ROOT/scripts/install-fonts.sh"

gsettings set org.gnome.desktop.interface font-name "$UI_FONT"
gsettings set org.gnome.desktop.interface document-font-name "$DOCUMENT_FONT"
gsettings set org.gnome.desktop.interface monospace-font-name "$MONOSPACE_FONT"
gsettings set org.gnome.desktop.wm.preferences titlebar-font "$TITLEBAR_FONT"

# Warp already has this exact key; replace only the value if it differs.
WARP_SETTINGS="$HOME/.config/warp-terminal/settings.toml"
if test -f "$WARP_SETTINGS" && ! grep -q '^font_name = "JetBrains Mono"$' "$WARP_SETTINGS"; then
  python3 - "$WARP_SETTINGS" <<'PY'
import re, sys
path = sys.argv[1]
text = open(path).read()
updated, count = re.subn(r'^font_name\s*=\s*.*$', 'font_name = "JetBrains Mono"', text, flags=re.M)
if count != 1:
    raise SystemExit('Warp font_name key was not found; nothing changed.')
open(path, 'w').write(updated)
PY
fi

# User settings already use JetBrains Mono. Do not rewrite JSONC or unrelated keys.
VSCODE_SETTINGS="$HOME/.config/Code/User/settings.json"
if test -f "$VSCODE_SETTINGS"; then
  grep -q '"editor.fontFamily".*JetBrains Mono' "$VSCODE_SETTINGS" || echo 'VS Code editor font needs manual review.' >&2
  grep -q '"terminal.integrated.fontFamily".*JetBrains Mono' "$VSCODE_SETTINGS" || echo 'VS Code terminal font needs manual review.' >&2
fi

printf 'Interface: '; gsettings get org.gnome.desktop.interface font-name
printf 'Document: '; gsettings get org.gnome.desktop.interface document-font-name
printf 'Monospace: '; gsettings get org.gnome.desktop.interface monospace-font-name
printf 'Titlebar: '; gsettings get org.gnome.desktop.wm.preferences titlebar-font
