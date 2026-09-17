#!/usr/bin/env bash
set -euo pipefail

THEME_DIR_NAME="Forge-Core"
THEME_LABEL="Forge Core"
FALLBACK_THEME="Yaru"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE_THEME="${REPO_ROOT}/icon-theme/${THEME_DIR_NAME}"
USER_DATA_HOME="${XDG_DATA_HOME:-${HOME}/.local/share}"
ICONS_HOME="${USER_DATA_HOME}/icons"
TARGET_THEME="${ICONS_HOME}/${THEME_DIR_NAME}"
STATE_DIR="${USER_DATA_HOME}/forge-core"
STATE_FILE="${STATE_DIR}/previous-icon-theme"
CONFIG_HOME="${XDG_CONFIG_HOME:-${HOME}/.config}"
SYSTEMD_USER_DIR="${CONFIG_HOME}/systemd/user"
WATCHER_UNIT_NAME="forge-core-browser-icons.service"
WATCHER_UNIT="${SYSTEMD_USER_DIR}/${WATCHER_UNIT_NAME}"
WATCHER_TEMPLATE="${REPO_ROOT}/config/forge-core-browser-icons.service"
WATCHER_SCRIPT="${REPO_ROOT}/scripts/watch-browser-icons.py"
WATCHER_LIBRARY="${REPO_ROOT}/scripts/browser_icons.py"
WATCHER_RUNTIME_DIR="${STATE_DIR}/browser-icons-watcher"
WATCHER_RUNTIME_SCRIPT="${WATCHER_RUNTIME_DIR}/watch-browser-icons.py"
WATCHER_MARKER="# Forge Core managed: browser launcher icon watcher"
FOLDER_CHOOSER_SCRIPT="${REPO_ROOT}/scripts/apply-folder-chooser-icons.py"
SPECIAL_FOLDER_SCRIPT="${REPO_ROOT}/scripts/special_folder_icons.py"

APPLY=1
[[ "${1:-}" == "--no-apply" ]] && APPLY=0

abort() { printf '\033[0;31merro:\033[0m %s\n' "$1" >&2; exit 1; }
APPLIED_THEME=0
rollback() {
  local status=$?
  trap - ERR
  if [[ ${APPLIED_THEME} -eq 1 ]]; then
    local previous
    previous="$(tr -d "[:space:]'\"" < "${STATE_FILE}" 2>/dev/null || true)"
    [[ -n "${previous}" ]] || previous="${FALLBACK_THEME}"
    gsettings set org.gnome.desktop.interface icon-theme "${previous}" || true
    printf '\033[0;31merro:\033[0m instalacao falhou; icon-theme revertido para %s\n' \
      "${previous}" >&2
  fi
  exit "${status}"
}
info()  { printf '\033[0;36m::\033[0m %s\n' "$1"; }
ok()    { printf '\033[0;32mok\033[0m %s\n' "$1"; }

install_browser_watcher() {
  [[ -f "${WATCHER_TEMPLATE}" ]] || abort "template do watcher ausente em ${WATCHER_TEMPLATE}"
  [[ -f "${WATCHER_SCRIPT}" ]] || abort "watcher ausente em ${WATCHER_SCRIPT}"
  [[ -f "${WATCHER_LIBRARY}" ]] || abort "biblioteca do watcher ausente em ${WATCHER_LIBRARY}"

  if [[ -f "${WATCHER_UNIT}" ]] && ! grep -Fqx "${WATCHER_MARKER}" "${WATCHER_UNIT}"; then
    abort "ja existe ${WATCHER_UNIT} e ele nao pertence ao Forge Core"
  fi

  if ! command -v systemctl >/dev/null 2>&1; then
    info "systemctl ausente; watcher de futuras instalacoes nao foi habilitado"
    return
  fi

  mkdir -p "${SYSTEMD_USER_DIR}" "${WATCHER_RUNTIME_DIR}"
  cp -f "${WATCHER_SCRIPT}" "${WATCHER_RUNTIME_SCRIPT}"
  cp -f "${WATCHER_LIBRARY}" "${WATCHER_RUNTIME_DIR}/browser_icons.py"
  chmod 755 "${WATCHER_RUNTIME_SCRIPT}"
  chmod 644 "${WATCHER_RUNTIME_DIR}/browser_icons.py"
  local service_content
  service_content="$(<"${WATCHER_TEMPLATE}")"
  service_content="${service_content//@WATCHER_SCRIPT@/${WATCHER_RUNTIME_SCRIPT}}"
  printf '%s\n' "${service_content}" > "${WATCHER_UNIT}"

  if ! systemctl --user daemon-reload; then
    info "nao foi possivel recarregar o systemd --user; watcher instalado, mas inativo"
    return
  fi
  if ! systemctl --user enable --now "${WATCHER_UNIT_NAME}"; then
    info "nao foi possivel iniciar o watcher; launcher atuais continuam aplicados"
    return
  fi
  ok "watcher de instalacoes futuras habilitado"
}

install_folder_chooser_icons() {
  [[ -f "${FOLDER_CHOOSER_SCRIPT}" ]] || {
    info "integracao de icones de pastas ausente; seletor do VS Code nao foi ajustado"
    return
  }

  if python3 "${FOLDER_CHOOSER_SCRIPT}" --timer; then
    ok "icones de pastas customizadas habilitados somente no Forge Core"
  else
    info "nao foi possivel habilitar os icones de pastas customizadas"
  fi
}

install_special_folder_icons() {
  [[ -f "${SPECIAL_FOLDER_SCRIPT}" ]] || {
    info "sincronizador de pastas especiais ausente"
    return
  }

  if python3 "${SPECIAL_FOLDER_SCRIPT}" --timer; then
    ok "icones especiais por nome habilitados somente no Forge Core"
  else
    info "nao foi possivel habilitar os icones especiais por nome"
  fi
}

[[ ${EUID} -eq 0 ]] && abort "nao execute como root: o Forge Core instala apenas no HOME do usuario"
[[ -d "${SOURCE_THEME}" ]] || abort "tema nao encontrado em ${SOURCE_THEME} - rode scripts/build-icons.py antes"
[[ -f "${SOURCE_THEME}/index.theme" ]] || abort "index.theme ausente em ${SOURCE_THEME}"

info "destino: ${TARGET_THEME}"
mkdir -p "${ICONS_HOME}" "${STATE_DIR}"

CURRENT_THEME="$(gsettings get org.gnome.desktop.interface icon-theme | tr -d "'\"")"
info "icon-theme atual: ${CURRENT_THEME}"

if [[ "${CURRENT_THEME}" != "${THEME_DIR_NAME}" ]]; then
  printf '%s\n' "${CURRENT_THEME}" > "${STATE_FILE}"
  ok "tema anterior registrado em ${STATE_FILE}"
elif [[ ! -f "${STATE_FILE}" ]]; then
  printf '%s\n' "${FALLBACK_THEME}" > "${STATE_FILE}"
fi

rm -rf "${TARGET_THEME}"
cp -a "${SOURCE_THEME}" "${TARGET_THEME}"
find "${TARGET_THEME}" -type d -exec chmod 755 {} +
find "${TARGET_THEME}" -type f -exec chmod 644 {} +
ok "$(find "${TARGET_THEME}" -name '*.png' | wc -l) arquivos de icone copiados"

if gtk-update-icon-cache -f -t "${TARGET_THEME}" >/dev/null 2>&1; then
  ok "cache GTK atualizado"
else
  info "cache GTK nao gerado (tema funciona sem cache)"
fi

if [[ ${APPLY} -eq 1 ]]; then
  gsettings set org.gnome.desktop.interface icon-theme "${THEME_DIR_NAME}"
  ok "${THEME_LABEL} aplicado como icon-theme"
  APPLIED_THEME=1
  trap rollback ERR
  python3 "${REPO_ROOT}/scripts/apply-browser-icons.py" --refresh \
    || info "overrides de launcher nao foram aplicados"
  install_browser_watcher
  install_special_folder_icons
  install_folder_chooser_icons
  trap - ERR
else
  info "instalado sem aplicar (--no-apply)"
fi

echo
echo "reverter:  ${REPO_ROOT}/scripts/uninstall-icons.sh"
echo "ou:        gsettings set org.gnome.desktop.interface icon-theme '$(cat "${STATE_FILE}")'"
