#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=../config/typography.conf
source "$ROOT/config/typography.conf"
FONT_ROOT="${FONT_ROOT:-$HOME/.local/share/fonts/Forge-Core}"
TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT

need() { command -v "$1" >/dev/null || { echo "Missing dependency: $1" >&2; exit 1; }; }
has_family() {
  local requested="$1" resolved
  resolved="$(fc-match -f '%{family}' "$requested")"
  test "${resolved%%,*}" = "$requested"
}
for tool in curl unzip find install fc-cache fc-match; do need "$tool"; done
mkdir -p "$FONT_ROOT/IBMPlexSans" "$FONT_ROOT/Oxanium" "$FONT_ROOT/JetBrainsMono"

install_ibm_plex() {
  if has_family 'IBM Plex Sans'; then return; fi
  curl --fail --location --retry 3 --output "$TMPDIR/ibm-plex-sans.zip" "$IBM_PLEX_RELEASE"
  unzip -q "$TMPDIR/ibm-plex-sans.zip" -d "$TMPDIR/ibm"
  for name in IBMPlexSans-Regular.ttf IBMPlexSans-Medium.ttf IBMPlexSans-SemiBold.ttf; do
    source_file="$(find "$TMPDIR/ibm" -type f -name "$name" -print -quit)"
    test -n "$source_file" || { echo "IBM Plex archive missing $name" >&2; exit 1; }
    install -m 0644 "$source_file" "$FONT_ROOT/IBMPlexSans/$name"
  done
}

install_oxanium() {
  if has_family 'Oxanium'; then return; fi
  curl --fail --location --retry 3 --output "$FONT_ROOT/Oxanium/Oxanium[wght].ttf" "$OXANIUM_TTF"
}

install_jetbrains_mono_if_needed() {
  if has_family 'JetBrains Mono'; then return; fi
  curl --fail --location --retry 3 --output "$TMPDIR/jetbrains-mono.zip" "$JETBRAINS_MONO_RELEASE"
  unzip -q "$TMPDIR/jetbrains-mono.zip" -d "$TMPDIR/jetbrains"
  for name in JetBrainsMono-Regular.ttf JetBrainsMono-Medium.ttf; do
    source_file="$(find "$TMPDIR/jetbrains" -type f -name "$name" -print -quit)"
    test -n "$source_file" || { echo "JetBrains Mono archive missing $name" >&2; exit 1; }
    install -m 0644 "$source_file" "$FONT_ROOT/JetBrainsMono/$name"
  done
}

install_ibm_plex
install_oxanium
install_jetbrains_mono_if_needed
fc-cache -f "$FONT_ROOT"

for family in 'IBM Plex Sans' Oxanium 'JetBrains Mono'; do
  resolved="$(fc-match -f '%{family}' "$family")"
  primary="${resolved%%,*}"
  test "$primary" = "$family" || { echo "$family resolved to $resolved" >&2; exit 1; }
  echo "$family: $resolved"
done
