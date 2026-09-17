#!/usr/bin/env bash
set -euo pipefail

UUID="forge-core-shell@forgecore.local"
GTK_CSS_NAME="forge-core-desktop-menu.css"
MARKER_BEGIN="/* forge-core:begin */"
MARKER_END="/* forge-core:end */"
DOCK_SETTINGS_SCHEMA="org.gnome.shell.extensions.dash-to-dock"
DOCK_KEYS=(
  dash-max-icon-size
  extend-height
  custom-theme-shrink
  height-fraction
  running-indicator-style
)

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
USER_DATA_HOME="${XDG_DATA_HOME:-${HOME}/.local/share}"
USER_CONFIG_HOME="${XDG_CONFIG_HOME:-${HOME}/.config}"
TARGET_EXT="${USER_DATA_HOME}/gnome-shell/extensions/${UUID}"
GTK_DIR="${USER_CONFIG_HOME}/gtk-3.0"
GTK_CSS="${GTK_DIR}/gtk.css"
TARGET_GTK="${GTK_DIR}/${GTK_CSS_NAME}"
STATE_DIR="${USER_DATA_HOME}/forge-core"
STATE_FILE="${STATE_DIR}/shell-state.env"
BACKUP_DIR="${STATE_DIR}/backup"

KEEP_FILES=0
[[ "${1:-}" == "--keep-files" ]] && KEEP_FILES=1

abort() { printf '\033[0;31merro:\033[0m %s\n' "$1" >&2; exit 1; }
info()  { printf '\033[0;36m::\033[0m %s\n' "$1"; }
ok()    { printf '\033[0;32mok\033[0m %s\n' "$1"; }
warn()  { printf '\033[0;33m!!\033[0m %s\n' "$1"; }

[[ ${EUID} -eq 0 ]] && abort "nao execute como root"

PREV_GTK_CSS="absent"
PREV_DASH_MAX_ICON_SIZE=""
if [[ -f "${STATE_FILE}" ]]; then
  PREV_GTK_CSS="$(awk -F= '/^PREV_GTK_CSS=/{print $2}' "${STATE_FILE}")"
  PREV_DASH_MAX_ICON_SIZE="$(awk -F= '/^PREV_DASH_MAX_ICON_SIZE=/{print $2}' "${STATE_FILE}")"
fi

gnome-extensions disable "${UUID}" >/dev/null 2>&1 || true

restore_dock_setting() {
  local key="$1" state_key value
  state_key="PREV_DOCK_$(printf '%s' "${key}" | tr 'a-z-' 'A-Z_')"
  [[ -f "${STATE_FILE}" ]] || return 0
  value="$(sed -n "s/^${state_key}=//p" "${STATE_FILE}")"
  [[ -z "${value}" || "${value}" == "unavailable" ]] && return 0
  gsettings writable "${DOCK_SETTINGS_SCHEMA}" "${key}" >/dev/null 2>&1 || return 0
  gsettings set "${DOCK_SETTINGS_SCHEMA}" "${key}" "${value}"
  ok "dock: ${key} restaurado para ${value}"
}

for key in "${DOCK_KEYS[@]}"; do
  restore_dock_setting "${key}"
done

if ! grep -q '^PREV_DOCK_DASH_MAX_ICON_SIZE=' "${STATE_FILE}" 2>/dev/null && \
   [[ "${PREV_DASH_MAX_ICON_SIZE}" =~ ^[0-9]+$ ]] && \
   gsettings writable "${DOCK_SETTINGS_SCHEMA}" dash-max-icon-size >/dev/null 2>&1; then
  gsettings set "${DOCK_SETTINGS_SCHEMA}" dash-max-icon-size "${PREV_DASH_MAX_ICON_SIZE}"
  ok "tamanho anterior do dock restaurado (${PREV_DASH_MAX_ICON_SIZE}px)"
fi

python3 - "${UUID}" <<'PY'
import subprocess, sys
uuid = sys.argv[1]
raw = subprocess.check_output(
    ['gsettings', 'get', 'org.gnome.shell', 'enabled-extensions'], text=True).strip()
current = [] if raw in ('@as []', '[]') else [
    p.strip().strip("'\"") for p in raw.strip('[]').split(',') if p.strip()
]
if uuid in current:
    current = [u for u in current if u != uuid]
    value = '[' + ', '.join("'%s'" % u for u in current) + ']' if current else '@as []'
    subprocess.check_call(['gsettings', 'set', 'org.gnome.shell', 'enabled-extensions', value])
    print('enabled-extensions atualizado')
else:
    print('enabled-extensions ja estava sem a extensao')
PY
ok "${UUID} desabilitada"

if [[ -f "${GTK_CSS}" ]]; then
  if [[ "${PREV_GTK_CSS}" == "preexisting" && -f "${BACKUP_DIR}/gtk.css" ]]; then
    cp -a "${BACKUP_DIR}/gtk.css" "${GTK_CSS}"
    ok "gtk.css restaurado do backup"
  else
    TMP_CSS="$(mktemp)"
    awk -v b="${MARKER_BEGIN}" -v e="${MARKER_END}" '
      index($0, b) {skip=1}
      !skip {print}
      index($0, e) {skip=0; next}
    ' "${GTK_CSS}" | awk 'NF || seen {print; seen=1}' > "${TMP_CSS}"
    if [[ -s "${TMP_CSS}" ]]; then
      mv "${TMP_CSS}" "${GTK_CSS}"
      chmod 644 "${GTK_CSS}"
      ok "bloco forge-core removido de ${GTK_CSS}"
    else
      rm -f "${TMP_CSS}" "${GTK_CSS}"
      ok "removido ${GTK_CSS} (criado pelo Forge Core e agora vazio)"
    fi
  fi
fi

if [[ ${KEEP_FILES} -eq 0 ]]; then
  [[ -d "${TARGET_EXT}" ]] && rm -rf "${TARGET_EXT}" && ok "removido ${TARGET_EXT}"
  [[ -f "${TARGET_GTK}" ]] && rm -f "${TARGET_GTK}" && ok "removido ${TARGET_GTK}"
  rm -f "${STATE_FILE}" "${BACKUP_DIR}/gtk.css"
  rmdir "${BACKUP_DIR}" 2>/dev/null || true
  rmdir "${STATE_DIR}" 2>/dev/null || true
else
  info "arquivos mantidos (--keep-files)"
fi

info "reiniciando o processo do Desktop Icons (DING)"
pkill -f "ding@rastersoft.com/app/ding.js" >/dev/null 2>&1 || true

echo
ok "visual anterior restaurado (Yaru-dark)"
echo "nenhum tema do sistema foi tocado (/usr/share intacto)"
if [[ "${XDG_SESSION_TYPE:-}" == "x11" ]]; then
  echo "se o banner de notificacao ainda aparecer estilizado: Alt+F2, digite  r  e Enter"
else
  echo "se o banner de notificacao ainda aparecer estilizado: faca logout/login"
fi
