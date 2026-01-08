#!/bin/bash
set -Eeuo pipefail

LOG_DIR="/var/log/magicbox"
LOG_FILE="${LOG_DIR}/installer.log"
INSTALL_ROOT="/opt/magicbox"
SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

log() {
  echo "$(date '+%Y-%m-%d %H:%M:%S') [installer] $*"
}

mkdir -p "${LOG_DIR}"
touch "${LOG_FILE}"
exec > >(tee -a "${LOG_FILE}") 2>&1

trap 'log "ERROR at line ${LINENO}: ${BASH_COMMAND}"; exit 1' ERR

if [[ "${EUID}" -ne 0 ]]; then
  log "Installer must be run as root"
  exit 1
fi

log "Starting Magic Box installer"

log "Installing system packages"
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y python3 python3-flask python3-gpiozero

log "Installing application files"
rm -rf "${INSTALL_ROOT}"
mkdir -p "${INSTALL_ROOT}"
cp -a "${SRC_DIR}" "${INSTALL_ROOT}/src"

log "Installing systemd service"
cp -a "${SRC_DIR}/systemd/magicbox.service" /etc/systemd/system/magicbox.service
systemctl daemon-reload
systemctl enable magicbox.service
systemctl restart magicbox.service

log "Installer completed successfully"
