#!/usr/bin/env bash
set -euo pipefail

log() {
  echo "[magicbox-uninstall] $*"
}

require_root() {
  if [ "$(id -u)" -ne 0 ]; then
    echo "This uninstaller must run as root. Try: sudo $0" >&2
    exit 1
  fi
}

remove_service() {
  local unit="$1"
  local systemd_dir="$2"
  if [ -f "$systemd_dir/$unit" ]; then
    systemctl stop "$unit" || true
    systemctl disable "$unit" || true
    rm -f "$systemd_dir/$unit"
    log "Removed $unit"
  fi
}

purge_repo() {
  local repo_dir="$1"
  if [ -d "$repo_dir" ]; then
    rm -rf "$repo_dir"
    log "Deleted repository at $repo_dir"
  fi
}

purge_data() {
  local data_dir="$1"
  if [ -d "$data_dir" ]; then
    rm -rf "$data_dir"
    log "Deleted data directory at $data_dir"
  fi
}

maybe_remove_user() {
  local user="$1"
  if id -u "$user" >/dev/null 2>&1; then
    if [ "${REMOVE_USER:-0}" -eq 1 ]; then
      deluser --remove-home "$user" || true
      log "Removed service user $user"
    else
      log "Leaving service user $user in place (set REMOVE_USER=1 to delete)"
    fi
  fi
}

main() {
  require_root

  SYSTEMD_DIR="/etc/systemd/system"
  HELPER_PATH="/usr/local/bin/magicbox"
  CONFIG_DIR="/etc/magicbox"
  CONFIG_FILE="$CONFIG_DIR/config"
  DEFAULT_REPO_DIR="/opt/julesvern"
  DEFAULT_DATA_DIR="/var/lib/julesvern"
  DEFAULT_USER="julesvern"

  # Load saved config if present
  if [ -f "$CONFIG_FILE" ]; then
    # shellcheck source=/dev/null
    source "$CONFIG_FILE"
  fi

  REPO_DIR=${REPO_DIR:-$DEFAULT_REPO_DIR}
  DATA_DIR=${DATA_DIR:-$DEFAULT_DATA_DIR}
  SERVICE_USER=${SERVICE_USER:-$DEFAULT_USER}

  log "Stopping and removing systemd units"
  remove_service "magic_lid.service" "$SYSTEMD_DIR"
  remove_service "magic_lid_web.service" "$SYSTEMD_DIR"
  systemctl daemon-reload

  if [ -f "$HELPER_PATH" ]; then
    rm -f "$HELPER_PATH"
    log "Removed helper at $HELPER_PATH"
  fi

  if [ -d "$CONFIG_DIR" ]; then
    rm -rf "$CONFIG_DIR"
    log "Removed config dir $CONFIG_DIR"
  fi

  if [ "${PURGE_REPO:-0}" -eq 1 ]; then
    purge_repo "$REPO_DIR"
  else
    log "Leaving repository at $REPO_DIR (set PURGE_REPO=1 to delete)"
  fi

  if [ "${PURGE_DATA:-0}" -eq 1 ]; then
    purge_data "$DATA_DIR"
  else
    log "Leaving data directory at $DATA_DIR (set PURGE_DATA=1 to delete)"
  fi

  maybe_remove_user "$SERVICE_USER"

  log "Uninstall complete"
}

main "$@"
