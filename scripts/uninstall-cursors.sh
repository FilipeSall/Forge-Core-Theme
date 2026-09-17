#!/usr/bin/env bash
set -euo pipefail

THEME_DIR_NAME="Forge-Core-Cursor"
FALLBACK_THEME="Yaru"

USER_DATA_HOME="${XDG_DATA_HOME:-${HOME}/.local/share}"
ICONS_HOME="${USER_DATA_HOME}/icons"
TARGET_THEME="${ICONS_HOME}/${THEME_DIR_NAME}"
LEGACY_ICONS="${HOME}/.icons"
DEFAULT_THEME_DIR="${LEGACY_ICONS}/default"
STATE_DIR="${USER_DATA_HOME}/forge-core"
STATE_FILE="${STATE_DIR}/previous-cursor-theme"
BACKUP_DIR="${STATE_DIR}/backup"

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
[[ "${PREVIOUS_THEME}" == "${THEME_DIR_NAME}" ]] && PREVIOUS_THEME="${FALLBACK_THEME}"

if [[ ! -d "/usr/share/icons/${PREVIOUS_THEME}" && ! -d "${ICONS_HOME}/${PREVIOUS_THEME}" ]]; then
  info "tema anterior '${PREVIOUS_THEME}' nao existe mais, usando ${FALLBACK_THEME}"
  PREVIOUS_THEME="${FALLBACK_THEME}"
fi

gsettings set org.gnome.desktop.interface cursor-theme "${PREVIOUS_THEME}"
ok "cursor-theme restaurado para '${PREVIOUS_THEME}'"

if [[ -f "${BACKUP_DIR}/default-index.theme" ]]; then
  mkdir -p "${DEFAULT_THEME_DIR}"
  cp -a "${BACKUP_DIR}/default-index.theme" "${DEFAULT_THEME_DIR}/index.theme"
  rm -f "${BACKUP_DIR}/default-index.theme"
  ok "${DEFAULT_THEME_DIR}/index.theme restaurado do backup"
elif [[ -f "${DEFAULT_THEME_DIR}/index.theme" ]] && grep -q "Inherits=${THEME_DIR_NAME}" "${DEFAULT_THEME_DIR}/index.theme"; then
  rm -f "${DEFAULT_THEME_DIR}/index.theme"
  rmdir "${DEFAULT_THEME_DIR}" 2>/dev/null || true
  ok "cursor padrao do X devolvido ao tema do sistema"
fi

if [[ ${KEEP_FILES} -eq 0 ]]; then
  if [[ -L "${LEGACY_ICONS}/${THEME_DIR_NAME}" ]]; then
    rm -f "${LEGACY_ICONS}/${THEME_DIR_NAME}"
    ok "link legado removido"
  fi
  if [[ "${TARGET_THEME}" == "${ICONS_HOME}/${THEME_DIR_NAME}" && -d "${TARGET_THEME}" ]]; then
    rm -rf "${TARGET_THEME}"
    ok "removido ${TARGET_THEME}"
  fi
  rm -f "${STATE_FILE}"
  rmdir "${BACKUP_DIR}" 2>/dev/null || true
  rmdir "${STATE_DIR}" 2>/dev/null || true
else
  info "arquivos mantidos em ${TARGET_THEME} (--keep-files)"
fi

command -v xsetroot >/dev/null 2>&1 && xsetroot -cursor_name left_ptr 2>/dev/null || true

echo
echo "nenhum tema do sistema foi tocado (/usr/share/icons intacto)"
echo "apps ja abertos podem manter o cursor Forge Core ate serem reiniciados"
