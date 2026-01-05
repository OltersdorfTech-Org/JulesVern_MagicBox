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

purge_path() {
  local target="$1"
  local label="$2"
  if [ -d "$target" ]; then
    rm -rf "$target"
    log "Deleted $label at $target"
  fi
}

main() {
  require_root

  SYSTEMD_DIR="/etc/systemd/system"
  HELPER_PATH="/usr/local/bin/magicbox"
  CONFIG_DIR="/etc/julesverne_magicbox"
  CONFIG_FILE="$CONFIG_DIR/runtime.conf"
  DEFAULT_REPO_DIR="/opt/julesvern/JulesVern_MagicBox"
  DEFAULT_STATE_DIR="/var/lib/julesverne_magicbox"
  DEFAULT_LOG_DIR="/var/log/julesverne_magicbox"

  # Load saved config if present
  if [ -f "$CONFIG_FILE" ]; then
    # shellcheck source=/dev/null
    source "$CONFIG_FILE"
  fi

  REPO_DIR=${JV_REPO_DIR:-$DEFAULT_REPO_DIR}
  STATE_DIR=${MAGICBOX_STATE_DIR:-$DEFAULT_STATE_DIR}
  LOG_DIR=${MAGICBOX_LOG_DIR:-$DEFAULT_LOG_DIR}

  log "Stopping and removing systemd units"
  remove_service "magic_lid.service" "$SYSTEMD_DIR"
  remove_service "magic_lid_web.service" "$SYSTEMD_DIR"
  remove_service "jv-status-led.service" "$SYSTEMD_DIR"
  remove_service "magic_lid.path" "$SYSTEMD_DIR"
  remove_service "jv-poweroff.service" "$SYSTEMD_DIR"
  systemctl daemon-reload

  if [ -f "$HELPER_PATH" ]; then
    rm -f "$HELPER_PATH"
    log "Removed helper at $HELPER_PATH"
  fi

  if [ -d "$CONFIG_DIR" ]; then
    rm -rf "$CONFIG_DIR"
    log "Removed config dir $CONFIG_DIR"
  fi

  if [ -f /etc/sudoers.d/magicbox-poweroff ]; then
    rm -f /etc/sudoers.d/magicbox-poweroff
    log "Removed shutdown sudoers rule"
  fi

  if [ "${PURGE_REPO:-0}" -eq 1 ]; then
    purge_repo "$REPO_DIR"
  else
    log "Leaving repository at $REPO_DIR (set PURGE_REPO=1 to delete)"
  fi

  if [ "${PURGE_STATE:-0}" -eq 1 ]; then
    purge_path "$STATE_DIR" "state directory"
  else
    log "Leaving state directory at $STATE_DIR (set PURGE_STATE=1 to delete)"
  fi

  if [ "${PURGE_LOGS:-0}" -eq 1 ]; then
    purge_path "$LOG_DIR" "log directory"
  else
    log "Leaving log directory at $LOG_DIR (set PURGE_LOGS=1 to delete)"
  fi

  log "Uninstall complete"
}

main "$@"
