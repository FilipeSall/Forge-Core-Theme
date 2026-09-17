#!/usr/bin/env bash
set -euo pipefail

THEME_DIR_NAME="Forge-Core"
FALLBACK_THEME="Yaru"

USER_DATA_HOME="${XDG_DATA_HOME:-${HOME}/.local/share}"
ICONS_HOME="${USER_DATA_HOME}/icons"
TARGET_THEME="${ICONS_HOME}/${THEME_DIR_NAME}"
STATE_DIR="${USER_DATA_HOME}/forge-core"
STATE_FILE="${STATE_DIR}/previous-icon-theme"
THEME_MODE_FILE="${STATE_DIR}/icon-theme-mode"
ICON_OVERRIDE_LOCK="${STATE_DIR}/browser-icon-overrides.lock"
CONFIG_HOME="${XDG_CONFIG_HOME:-${HOME}/.config}"
SYSTEMD_USER_DIR="${CONFIG_HOME}/systemd/user"
WATCHER_UNIT_NAME="forge-core-browser-icons.service"
WATCHER_UNIT="${SYSTEMD_USER_DIR}/${WATCHER_UNIT_NAME}"
WATCHER_RUNTIME_DIR="${STATE_DIR}/browser-icons-watcher"
WATCHER_MARKER="# Forge Core managed: browser launcher icon watcher"
FOLDER_CHOOSER_RESTORE_SCRIPT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/restore-folder-chooser-icons.py"

KEEP_FILES=0
[[ "${1:-}" == "--keep-files" ]] && KEEP_FILES=1

abort() { printf '\033[0;31merro:\033[0m %s\n' "$1" >&2; exit 1; }
info()  { printf '\033[0;36m::\033[0m %s\n' "$1"; }
ok()    { printf '\033[0;32mok\033[0m %s\n' "$1"; }

remove_browser_watcher() {
  [[ -f "${WATCHER_UNIT}" ]] || return
  if ! grep -Fqx "${WATCHER_MARKER}" "${WATCHER_UNIT}"; then
    info "watcher existente nao pertence ao Forge Core; arquivo mantido"
    return
  fi

  if command -v systemctl >/dev/null 2>&1; then
    systemctl --user disable --now "${WATCHER_UNIT_NAME}" >/dev/null 2>&1 || true
    systemctl --user daemon-reload >/dev/null 2>&1 || true
  fi
  rm -f "${WATCHER_UNIT}"
  if [[ "${WATCHER_RUNTIME_DIR}" == "${STATE_DIR}/browser-icons-watcher" ]]; then
    rm -rf "${WATCHER_RUNTIME_DIR}"
  fi
  ok "watcher de instalacoes futuras removido"
}

[[ ${EUID} -eq 0 ]] && abort "nao execute como root"

remove_browser_watcher

PREVIOUS_THEME="${FALLBACK_THEME}"
if [[ -f "${STATE_FILE}" ]]; then
  PREVIOUS_THEME="$(tr -d "[:space:]'\"" < "${STATE_FILE}")"
  [[ -n "${PREVIOUS_THEME}" ]] || PREVIOUS_THEME="${FALLBACK_THEME}"
fi

if [[ ! -d "/usr/share/icons/${PREVIOUS_THEME}" && ! -d "${ICONS_HOME}/${PREVIOUS_THEME}" ]]; then
  info "tema anterior '${PREVIOUS_THEME}' nao existe mais, usando ${FALLBACK_THEME}"
  PREVIOUS_THEME="${FALLBACK_THEME}"
fi

# Se a extensao Forge Core estiver ativa, informe que a saida foi intencional
# antes de alterar o GSettings; isso evita que o guard restaure Forge-Core.
mkdir -p "${STATE_DIR}"
printf '%s\n' "${FALLBACK_THEME}" > "${THEME_MODE_FILE}"
gsettings set org.gnome.desktop.interface icon-theme "${PREVIOUS_THEME}"
ok "icon-theme restaurado para '${PREVIOUS_THEME}'"

python3 "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/restore-browser-icons.py"
rm -f "${ICON_OVERRIDE_LOCK}"

if [[ -f "${FOLDER_CHOOSER_RESTORE_SCRIPT}" ]]; then
  python3 "${FOLDER_CHOOSER_RESTORE_SCRIPT}" || \
    info "icones de pastas customizadas nao foram totalmente restaurados"
fi

if [[ ${KEEP_FILES} -eq 0 ]]; then
  if [[ "${TARGET_THEME}" == "${ICONS_HOME}/${THEME_DIR_NAME}" && -d "${TARGET_THEME}" ]]; then
    rm -rf "${TARGET_THEME}"
    ok "removido ${TARGET_THEME}"
  else
    info "nada a remover em ${TARGET_THEME}"
  fi
  rm -f "${THEME_MODE_FILE}"
  rmdir "${STATE_DIR}" 2>/dev/null || true
else
  info "arquivos mantidos em ${TARGET_THEME} (--keep-files)"
fi

echo
echo "nenhum tema do sistema foi tocado (/usr/share/icons intacto)"
