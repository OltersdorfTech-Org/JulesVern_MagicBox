#!/bin/bash
set -Eeuo pipefail

LOG_DIR="/var/log/magicbox"
LOG_FILE="${LOG_DIR}/installer.log"
INSTALL_ROOT="/opt/magicbox"
PURGE_LOGS="false"

if [[ "${1-}" == "--purge-logs" ]]; then
  PURGE_LOGS="true"
fi

log() {
  echo "$(date '+%Y-%m-%d %H:%M:%S') [uninstaller] $*"
}

mkdir -p "${LOG_DIR}"
touch "${LOG_FILE}"
exec > >(tee -a "${LOG_FILE}") 2>&1

trap 'log "ERROR at line ${LINENO}: ${BASH_COMMAND}"; exit 1' ERR

if [[ "${EUID}" -ne 0 ]]; then
  log "Uninstaller must be run as root"
  exit 1
fi

log "Starting Magic Box uninstall"

if systemctl is-active --quiet magicbox.service; then
  log "Stopping service"
  systemctl stop magicbox.service
fi

if systemctl is-enabled --quiet magicbox.service; then
  log "Disabling service"
  systemctl disable magicbox.service
fi

log "Removing systemd unit"
rm -f /etc/systemd/system/magicbox.service
systemctl daemon-reload

log "Removing application files"
rm -rf "${INSTALL_ROOT}"

if [[ "${PURGE_LOGS}" == "true" ]]; then
  log "Purging logs"
  rm -rf "${LOG_DIR}"
else
  log "Preserving logs"
fi

log "Uninstall complete"
