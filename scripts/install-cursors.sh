#!/usr/bin/env bash
set -euo pipefail

THEME_DIR_NAME="Forge-Core-Cursor"
THEME_LABEL="Forge Core Cursor"
FALLBACK_THEME="Yaru"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE_THEME="${REPO_ROOT}/cursor-theme/${THEME_DIR_NAME}"
USER_DATA_HOME="${XDG_DATA_HOME:-${HOME}/.local/share}"
ICONS_HOME="${USER_DATA_HOME}/icons"
TARGET_THEME="${ICONS_HOME}/${THEME_DIR_NAME}"
LEGACY_ICONS="${HOME}/.icons"
DEFAULT_THEME_DIR="${LEGACY_ICONS}/default"
STATE_DIR="${USER_DATA_HOME}/forge-core"
STATE_FILE="${STATE_DIR}/previous-cursor-theme"
BACKUP_DIR="${STATE_DIR}/backup"

APPLY=1
[[ "${1:-}" == "--no-apply" ]] && APPLY=0

abort() { printf '\033[0;31merro:\033[0m %s\n' "$1" >&2; exit 1; }
info()  { printf '\033[0;36m::\033[0m %s\n' "$1"; }
ok()    { printf '\033[0;32mok\033[0m %s\n' "$1"; }

[[ ${EUID} -eq 0 ]] && abort "nao execute como root: o Forge Core instala apenas no HOME do usuario"
[[ -d "${SOURCE_THEME}" ]] || abort "tema nao encontrado em ${SOURCE_THEME} - rode scripts/build-cursors.py antes"
[[ -f "${SOURCE_THEME}/index.theme" ]] || abort "index.theme ausente em ${SOURCE_THEME}"
[[ -f "${SOURCE_THEME}/cursors/left_ptr" ]] || abort "cursors/left_ptr ausente em ${SOURCE_THEME}"

info "destino: ${TARGET_THEME}"
mkdir -p "${ICONS_HOME}" "${STATE_DIR}" "${BACKUP_DIR}" "${LEGACY_ICONS}"

CURRENT_THEME="$(gsettings get org.gnome.desktop.interface cursor-theme | tr -d "'\"")"
info "cursor-theme atual: ${CURRENT_THEME}"

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
ok "$(find "${TARGET_THEME}/cursors" -type f | wc -l) cursores e $(find "${TARGET_THEME}/cursors" -type l | wc -l) apelidos instalados"

if [[ -e "${LEGACY_ICONS}/${THEME_DIR_NAME}" && ! -L "${LEGACY_ICONS}/${THEME_DIR_NAME}" ]]; then
  info "${LEGACY_ICONS}/${THEME_DIR_NAME} existe e nao e link, mantido como esta"
else
  ln -sfn "${TARGET_THEME}" "${LEGACY_ICONS}/${THEME_DIR_NAME}"
  ok "link legado ${LEGACY_ICONS}/${THEME_DIR_NAME}"
fi

if [[ ${APPLY} -eq 1 ]]; then
  if [[ -f "${DEFAULT_THEME_DIR}/index.theme" && ! -f "${BACKUP_DIR}/default-index.theme" ]]; then
    cp -a "${DEFAULT_THEME_DIR}/index.theme" "${BACKUP_DIR}/default-index.theme"
    info "backup de ${DEFAULT_THEME_DIR}/index.theme"
  fi
  mkdir -p "${DEFAULT_THEME_DIR}"
  printf '[Icon Theme]\nName=Default\nComment=Forge Core\nInherits=%s\n' "${THEME_DIR_NAME}" \
    > "${DEFAULT_THEME_DIR}/index.theme"
  ok "cursor padrao do X apontando para ${THEME_DIR_NAME}"

  gsettings set org.gnome.desktop.interface cursor-theme "${THEME_DIR_NAME}"
  ok "${THEME_LABEL} aplicado como cursor-theme"

  command -v xsetroot >/dev/null 2>&1 && xsetroot -cursor_name left_ptr 2>/dev/null || true
else
  info "instalado sem aplicar (--no-apply)"
fi

echo
echo "apps ja abertos podem manter o cursor antigo ate serem reiniciados"
echo "reverter:  ${REPO_ROOT}/scripts/uninstall-cursors.sh"
