#!/usr/bin/env bash
set -euo pipefail

UUID="forge-core-shell@forgecore.local"
GTK_CSS_NAME="forge-core-desktop-menu.css"
MARKER_BEGIN="/* forge-core:begin */"
MARKER_END="/* forge-core:end */"
DOCK_SETTINGS_SCHEMA="org.gnome.shell.extensions.dash-to-dock"
DOCK_ICON_SIZE=56

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE_EXT="${REPO_ROOT}/gnome-shell/${UUID}"
SOURCE_GTK="${REPO_ROOT}/gtk-3.0/${GTK_CSS_NAME}"

USER_DATA_HOME="${XDG_DATA_HOME:-${HOME}/.local/share}"
USER_CONFIG_HOME="${XDG_CONFIG_HOME:-${HOME}/.config}"
EXTENSIONS_HOME="${USER_DATA_HOME}/gnome-shell/extensions"
TARGET_EXT="${EXTENSIONS_HOME}/${UUID}"
GTK_DIR="${USER_CONFIG_HOME}/gtk-3.0"
GTK_CSS="${GTK_DIR}/gtk.css"
TARGET_GTK="${GTK_DIR}/${GTK_CSS_NAME}"
STATE_DIR="${USER_DATA_HOME}/forge-core"
STATE_FILE="${STATE_DIR}/shell-state.env"
BACKUP_DIR="${STATE_DIR}/backup"

abort() { printf '\033[0;31merro:\033[0m %s\n' "$1" >&2; exit 1; }
info()  { printf '\033[0;36m::\033[0m %s\n' "$1"; }
ok()    { printf '\033[0;32mok\033[0m %s\n' "$1"; }
warn()  { printf '\033[0;33m!!\033[0m %s\n' "$1"; }

get_previous_dock_icon_size() {
  if gsettings writable "${DOCK_SETTINGS_SCHEMA}" dash-max-icon-size >/dev/null 2>&1; then
    gsettings get "${DOCK_SETTINGS_SCHEMA}" dash-max-icon-size | awk '{print $NF}'
  else
    printf 'unavailable\n'
  fi
}

[[ ${EUID} -eq 0 ]] && abort "nao execute como root: o Forge Core instala apenas no HOME do usuario"
[[ -d "${SOURCE_EXT}" ]] || abort "extensao nao encontrada em ${SOURCE_EXT}"
[[ -f "${SOURCE_EXT}/metadata.json" ]] || abort "metadata.json ausente em ${SOURCE_EXT}"
[[ -f "${SOURCE_EXT}/stylesheet.css" ]] || abort "stylesheet.css ausente em ${SOURCE_EXT}"
[[ -f "${SOURCE_GTK}" ]] || abort "css do menu nao encontrado em ${SOURCE_GTK}"

SHELL_VERSION="$(gnome-shell --version 2>/dev/null | awk '{print $3}')"
SHELL_MAJOR="${SHELL_VERSION%%.*}"
[[ "${SHELL_MAJOR}" == "46" ]] || warn "GNOME Shell ${SHELL_VERSION}: seletores validados para a serie 46"

mkdir -p "${EXTENSIONS_HOME}" "${GTK_DIR}" "${STATE_DIR}" "${BACKUP_DIR}"

if [[ ! -f "${STATE_FILE}" ]]; then
  {
    printf '# forge-core shell: estado anterior a instalacao\n'
    printf 'CAPTURED_AT=%s\n' "$(date -Iseconds)"
    printf 'PREV_ENABLED_EXTENSIONS=%s\n' "$(gsettings get org.gnome.shell enabled-extensions)"
    printf 'PREV_GTK_THEME=%s\n' "$(gsettings get org.gnome.desktop.interface gtk-theme)"
    printf 'PREV_COLOR_SCHEME=%s\n' "$(gsettings get org.gnome.desktop.interface color-scheme)"
    printf 'PREV_DASH_MAX_ICON_SIZE=%s\n' "$(get_previous_dock_icon_size)"
    if [[ -f "${GTK_CSS}" ]]; then
      cp -a "${GTK_CSS}" "${BACKUP_DIR}/gtk.css"
      printf 'PREV_GTK_CSS=preexisting\n'
    else
      printf 'PREV_GTK_CSS=absent\n'
    fi
  } > "${STATE_FILE}"
  ok "estado anterior registrado em ${STATE_FILE}"
else
  info "estado anterior ja registrado em ${STATE_FILE} (mantido)"
fi

if [[ -f "${STATE_FILE}" ]] && ! grep -q '^PREV_DASH_MAX_ICON_SIZE=' "${STATE_FILE}"; then
  printf 'PREV_DASH_MAX_ICON_SIZE=%s\n' "$(get_previous_dock_icon_size)" >> "${STATE_FILE}"
  info "tamanho anterior do dock registrado no estado existente"
fi

rm -rf "${TARGET_EXT}"
cp -a "${SOURCE_EXT}" "${TARGET_EXT}"
find "${TARGET_EXT}" -type d -exec chmod 755 {} +
find "${TARGET_EXT}" -type f -exec chmod 644 {} +
ok "extensao instalada em ${TARGET_EXT}"

python3 - "${UUID}" <<'PY'
import subprocess, sys
uuid = sys.argv[1]
key = ['gsettings', 'get', 'org.gnome.shell', 'enabled-extensions']
raw = subprocess.check_output(key, text=True).strip()
current = [] if raw in ('@as []', '[]') else [
    p.strip().strip("'\"") for p in raw.strip('[]').split(',') if p.strip()
]
if uuid not in current:
    current.append(uuid)
    value = '[' + ', '.join("'%s'" % u for u in current) + ']'
    subprocess.check_call(['gsettings', 'set', 'org.gnome.shell', 'enabled-extensions', value])
    print('enabled-extensions atualizado')
else:
    print('enabled-extensions ja continha a extensao')
PY
ok "${UUID} habilitada"

if gsettings writable "${DOCK_SETTINGS_SCHEMA}" dash-max-icon-size >/dev/null 2>&1; then
  gsettings set "${DOCK_SETTINGS_SCHEMA}" dash-max-icon-size "${DOCK_ICON_SIZE}"
  ok "tamanho visual do dock ajustado para ${DOCK_ICON_SIZE}px"
else
  warn "Ubuntu Dock nao encontrado; tamanho visual nao foi ajustado"
fi

install -m 644 "${SOURCE_GTK}" "${TARGET_GTK}"
ok "css do menu instalado em ${TARGET_GTK}"

touch "${GTK_CSS}"
if grep -qF "${MARKER_BEGIN}" "${GTK_CSS}"; then
  info "import ja presente em ${GTK_CSS}"
else
  TMP_CSS="$(mktemp)"
  {
    printf '%s\n' "${MARKER_BEGIN}"
    printf '@import url("%s");\n' "${GTK_CSS_NAME}"
    printf '%s\n\n' "${MARKER_END}"
    cat "${GTK_CSS}"
  } > "${TMP_CSS}"
  mv "${TMP_CSS}" "${GTK_CSS}"
  chmod 644 "${GTK_CSS}"
  ok "import adicionado ao topo de ${GTK_CSS}"
fi

EXT_STATE="$(gnome-extensions info "${UUID}" 2>/dev/null | awk -F': ' '/Estado|State/ {print $2}' || true)"

info "reiniciando o processo do Desktop Icons (DING)"
pkill -f "ding@rastersoft.com/app/ding.js" >/dev/null 2>&1 || true
sleep 1
if pgrep -f "ding@rastersoft.com/app/ding.js" >/dev/null 2>&1; then
  ok "DING reiniciado com o novo css"
else
  warn "DING nao voltou sozinho; ele reinicia em alguns segundos ou ao recarregar o shell"
fi

echo
if [[ "${EXT_STATE}" == "ACTIVE" ]]; then
  ok "Forge Core Shell ativo (estado: ${EXT_STATE})"
else
  warn "extensao instalada mas ainda nao carregada (estado: ${EXT_STATE:-nao encontrada})"
  echo "   o GNOME Shell so varre o diretorio de extensoes na inicializacao,"
  echo "   entao a primeira instalacao exige um reload do shell:"
  if [[ "${XDG_SESSION_TYPE:-}" == "x11" ]]; then
    echo "   Alt+F2, digite  r  e Enter   (em notebook pode precisar de Fn+Alt+F2)"
  else
    echo "   logout/login (sessao Wayland nao permite reload do shell)"
  fi
  echo "   o menu do desktop ja esta valendo, nao depende disso"
fi

echo
echo "testar notificacao:  notify-send 'Forge Core' 'Teste visual das notificacoes'"
echo "testar menu:         clique com o botao direito em uma area vazia do desktop"
echo "reverter:            ${REPO_ROOT}/scripts/uninstall-shell.sh"
