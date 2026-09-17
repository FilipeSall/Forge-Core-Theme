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

APPLY=1
[[ "${1:-}" == "--no-apply" ]] && APPLY=0

abort() { printf '\033[0;31merro:\033[0m %s\n' "$1" >&2; exit 1; }
info()  { printf '\033[0;36m::\033[0m %s\n' "$1"; }
ok()    { printf '\033[0;32mok\033[0m %s\n' "$1"; }

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
else
  info "instalado sem aplicar (--no-apply)"
fi

echo
echo "reverter:  ${REPO_ROOT}/scripts/uninstall-icons.sh"
echo "ou:        gsettings set org.gnome.desktop.interface icon-theme '$(cat "${STATE_FILE}")'"
