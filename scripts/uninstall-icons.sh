#!/usr/bin/env bash
set -euo pipefail

THEME_DIR_NAME="Forge-Core"
FALLBACK_THEME="Yaru"

USER_DATA_HOME="${XDG_DATA_HOME:-${HOME}/.local/share}"
ICONS_HOME="${USER_DATA_HOME}/icons"
TARGET_THEME="${ICONS_HOME}/${THEME_DIR_NAME}"
STATE_DIR="${USER_DATA_HOME}/forge-core"
STATE_FILE="${STATE_DIR}/previous-icon-theme"

KEEP_FILES=0
[[ "${1:-}" == "--keep-files" ]] && KEEP_FILES=1

abort() { printf '\033[0;31merro:\033[0m %s\n' "$1" >&2; exit 1; }
info()  { printf '\033[0;36m::\033[0m %s\n' "$1"; }
ok()    { printf '\033[0;32mok\033[0m %s\n' "$1"; }

[[ ${EUID} -eq 0 ]] && abort "nao execute como root"

PREVIOUS_THEME="${FALLBACK_THEME}"
if [[ -f "${STATE_FILE}" ]]; then
  PREVIOUS_THEME="$(tr -d "[:space:]'\"" < "${STATE_FILE}")"
  [[ -n "${PREVIOUS_THEME}" ]] || PREVIOUS_THEME="${FALLBACK_THEME}"
fi

if [[ ! -d "/usr/share/icons/${PREVIOUS_THEME}" && ! -d "${ICONS_HOME}/${PREVIOUS_THEME}" ]]; then
  info "tema anterior '${PREVIOUS_THEME}' nao existe mais, usando ${FALLBACK_THEME}"
  PREVIOUS_THEME="${FALLBACK_THEME}"
fi

gsettings set org.gnome.desktop.interface icon-theme "${PREVIOUS_THEME}"
ok "icon-theme restaurado para '${PREVIOUS_THEME}'"

if [[ ${KEEP_FILES} -eq 0 ]]; then
  if [[ "${TARGET_THEME}" == "${ICONS_HOME}/${THEME_DIR_NAME}" && -d "${TARGET_THEME}" ]]; then
    rm -rf "${TARGET_THEME}"
    ok "removido ${TARGET_THEME}"
  else
    info "nada a remover em ${TARGET_THEME}"
  fi
  rm -f "${STATE_FILE}"
  rmdir "${STATE_DIR}" 2>/dev/null || true
else
  info "arquivos mantidos em ${TARGET_THEME} (--keep-files)"
fi

echo
echo "nenhum tema do sistema foi tocado (/usr/share/icons intacto)"
