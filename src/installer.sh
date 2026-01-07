#!/bin/bash
set -euo pipefail

LOG_DIR="/var/log/magicbox"
LOG_FILE="${LOG_DIR}/installer.log"
INSTALL_ROOT="/opt/magicbox"
SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

mkdir -p "${LOG_DIR}"

touch "${LOG_FILE}"
exec > >(tee -a "${LOG_FILE}") 2>&1

log() {
  echo "$(date '+%Y-%m-%d %H:%M:%S') [installer] $*"
}

log "Starting Magic Box installer"

log "Installing system packages"
apt-get update -y
apt-get install -y python3 python3-pip

log "Installing Python dependencies"
pip3 install --no-cache-dir flask gpiozero

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
