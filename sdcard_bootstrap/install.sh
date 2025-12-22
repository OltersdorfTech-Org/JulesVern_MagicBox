#!/usr/bin/env bash
set -euo pipefail

require_root() {
  if [ "$(id -u)" -ne 0 ]; then
    echo "Run this script with sudo: sudo $0" >&2
    exit 1
  fi
}

log() {
  echo "[bootstrap] $*"
}

copy_repo() {
  local source_repo="$1"
  local target_repo="$2"

  mkdir -p "$target_repo"
  if command -v rsync >/dev/null 2>&1; then
    rsync -a --delete "$source_repo/" "$target_repo/"
  else
    cp -a "$source_repo/." "$target_repo/"
  fi
}

main() {
  require_root
  SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
  SOURCE_REPO=$(cd "$SCRIPT_DIR/.." && pwd)
  TARGET_REPO=${MAGICBOX_TARGET:-/home/pi/JulesVern_MagicBox}
  TARGET_USER=${MAGICBOX_USER:-${SUDO_USER:-pi}}

  if [ ! -d "$SOURCE_REPO/src" ]; then
    echo "Could not find the Magic Box repository beside this script." >&2
    exit 1
  fi

  log "Copying repo from $SOURCE_REPO to $TARGET_REPO"
  copy_repo "$SOURCE_REPO" "$TARGET_REPO"

  if id -u "$TARGET_USER" >/dev/null 2>&1; then
    chown -R "$TARGET_USER" "$TARGET_REPO"
  fi

  INSTALLER="$TARGET_REPO/install.sh"
  if [ ! -x "$INSTALLER" ]; then
    echo "Installer missing at $INSTALLER" >&2
    exit 1
  fi

  log "Running installer"
  MAGICBOX_REPO_DIR="$TARGET_REPO" MAGICBOX_USER="$TARGET_USER" "$INSTALLER"
}

main "$@"
