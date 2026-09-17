#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=../config/typography.backup.conf
source "$ROOT/config/typography.backup.conf"

gsettings set org.gnome.desktop.interface font-name "$FONT_NAME"
gsettings set org.gnome.desktop.interface document-font-name "$DOCUMENT_FONT_NAME"
gsettings set org.gnome.desktop.interface monospace-font-name "$MONOSPACE_FONT_NAME"
gsettings set org.gnome.desktop.wm.preferences titlebar-font "$TITLEBAR_FONT"

printf 'Restored GNOME typography from %s\n' "$ROOT/config/typography.backup.conf"
printf 'Warp and VS Code were already using JetBrains Mono before Forge Core and were left unchanged.\n'
