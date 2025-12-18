#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
INSTALL_SCRIPT="$SCRIPT_DIR/scripts/install_pi.sh"

if [ ! -f "$INSTALL_SCRIPT" ]; then
  echo "Installer not found at $INSTALL_SCRIPT"
  exit 1
fi

if [ "$(id -u)" -ne 0 ]; then
  exec sudo MAGICBOX_REPO_DIR="$SCRIPT_DIR" "$INSTALL_SCRIPT"
else
  exec MAGICBOX_REPO_DIR="$SCRIPT_DIR" "$INSTALL_SCRIPT"
fi
