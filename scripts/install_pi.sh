#!/usr/bin/env bash
set -euo pipefail

log() {
  echo "[magicbox] $*"
}

require_root() {
  if [ "$(id -u)" -ne 0 ]; then
    echo "This installer must run as root. Try: sudo $0" >&2
    exit 1
  fi
}

warn_if_not_pi() {
  if [ "$(uname -s)" != "Linux" ]; then
    log "Warning: non-Linux platform detected. This script targets Raspberry Pi OS."
    return
  fi
  if [ ! -f /proc/device-tree/model ]; then
    log "Warning: /proc/device-tree/model missing; unable to confirm Raspberry Pi hardware."
    return
  fi
  if ! grep -qi "Raspberry Pi" /proc/device-tree/model; then
    log "Warning: hardware model does not look like a Raspberry Pi."
  fi
}

get_home_dir() {
  local user="$1"
  local home_dir
  home_dir=$(getent passwd "$user" | cut -d: -f6)
  if [ -z "$home_dir" ]; then
    echo "/home/$user"
  else
    echo "$home_dir"
  fi
}

install_apt_packages() {
  log "Installing system packages via apt..."
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -y
  apt-get install -y \
    python3 \
    python3-flask \
    python3-gpiozero \
    python3-lgpio \
    python3-rpi.gpio \
    wireless-tools
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

resolve_runtime_user() {
  local requested_user="${MAGICBOX_USER:-}"
  local runtime_user

  if [ -n "$requested_user" ]; then
    runtime_user="$requested_user"
  elif [ -n "${SUDO_USER:-}" ]; then
    runtime_user="$SUDO_USER"
  else
    runtime_user="$USER"
  fi

  if ! id -u "$runtime_user" >/dev/null 2>&1; then
    echo "Runtime user $runtime_user does not exist. Create the user before installing." >&2
    exit 1
  fi

  echo "$runtime_user"
}

ensure_user_groups() {
  local user="$1"
  local group
  for group in gpio adm; do
    if getent group "$group" >/dev/null 2>&1; then
      usermod -a -G "$group" "$user"
    fi
  done
}

install_shutdown_sudoers() {
  local user="$1"
  local sudoers_file="/etc/sudoers.d/magicbox-poweroff"
  cat >"$sudoers_file" <<EOF_SUDO
$user ALL=(root) NOPASSWD: /bin/systemctl start jv-poweroff.service
EOF_SUDO
  chmod 440 "$sudoers_file"
  log "Installed shutdown sudoers rule at $sudoers_file"
}

write_runtime_conf() {
  local conf_path="$1"
  local repo_dir="$2"
  local user="$3"
  local web_port="$4"

  mkdir -p "$(dirname "$conf_path")"
  cat >"$conf_path" <<EOF_CONF
JV_USER="$user"
JV_REPO_DIR="$repo_dir"
MAGICBOX_WEB_PORT="$web_port"
EOF_CONF
  log "Saved runtime config to $conf_path"
}

write_systemd_unit() {
  local unit_path="$1"
  local description="$2"
  local exec_cmd="$3"
  local restart_policy="${4:-always}"
  local env_file="$5"

  cat >"$unit_path" <<EOF_UNIT
[Unit]
Description=$description
After=network-online.target local-fs.target
Wants=network-online.target

[Service]
Type=simple
EnvironmentFile=$env_file
User=\${JV_USER}
Group=\${JV_USER}
WorkingDirectory=\${JV_REPO_DIR}
ExecStart=$exec_cmd
Restart=$restart_policy
RestartSec=2
TimeoutStopSec=15
Environment=PYTHONUNBUFFERED=1
SupplementaryGroups=gpio
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF_UNIT
  log "Wrote systemd unit $unit_path"
}

write_path_unit() {
  local unit_path="$1"
  local watch_path="$2"
  cat >"$unit_path" <<EOF_UNIT
[Unit]
Description=Watch Magic Box config.py for changes

[Path]
PathChanged=$watch_path
Unit=magic_lid.service

[Install]
WantedBy=multi-user.target
EOF_UNIT
  log "Wrote systemd unit $unit_path"
}

write_poweroff_unit() {
  local unit_path="$1"
  cat >"$unit_path" <<'EOF_UNIT'
[Unit]
Description=Magic Box safe poweroff helper

[Service]
Type=oneshot
ExecStart=/bin/systemctl poweroff
User=root

[Install]
WantedBy=multi-user.target
EOF_UNIT
  log "Wrote systemd unit $unit_path"
}

install_services() {
  local systemd_dir="$1"
  local repo_dir="$2"
  local web_port="$3"
  local env_file="$4"
  local config_path="$5"

  write_systemd_unit \
    "$systemd_dir/magic_lid.service" \
    "Magic Lid GPIO controller" \
    "/usr/bin/python3 \${JV_REPO_DIR}/src/main.py" \
    "always" \
    "$env_file"

  write_systemd_unit \
    "$systemd_dir/magic_lid_web.service" \
    "Magic Lid Flask web server" \
    "/usr/bin/python3 \${JV_REPO_DIR}/src/web_server.py --port \${MAGICBOX_WEB_PORT}" \
    "always" \
    "$env_file"

  write_systemd_unit \
    "$systemd_dir/jv-status-led.service" \
    "Magic Box status LED daemon" \
    "/usr/bin/python3 \${JV_REPO_DIR}/src/hardware/status_led_daemon.py" \
    "always" \
    "$env_file"

  write_path_unit \
    "$systemd_dir/magic_lid.path" \
    "$config_path"

  write_poweroff_unit "$systemd_dir/jv-poweroff.service"
}

install_helper_command() {
  local helper_path="$1"
  local config_file="$2"
  cat >"$helper_path" <<'EOF_HELPER'
#!/usr/bin/env bash
set -euo pipefail

CONFIG_FILE="/etc/julesverne_magicbox/runtime.conf"
SERVICES=(magic_lid.service magic_lid_web.service jv-status-led.service)

if [ -f "$CONFIG_FILE" ]; then
  # shellcheck source=/dev/null
  source "$CONFIG_FILE"
fi

REPO_DIR="${JV_REPO_DIR:-/opt/julesvern/JulesVern_MagicBox}"
WEB_PORT="${MAGICBOX_WEB_PORT:-8080}"

usage() {
  cat <<'USAGE'
magicbox install         # re-run the installer
magicbox start           # start both services
magicbox stop            # stop both services
magicbox restart         # restart both services
magicbox status          # status for both services
magicbox logs            # follow combined logs
magicbox logs-main       # follow GPIO service logs
magicbox logs-web        # follow web service logs
magicbox logs-led        # follow status LED logs
magicbox open            # open the web UI in a browser on this machine
magicbox export-logs     # export logs to the boot partition
USAGE
}

require_repo() {
  if [ ! -d "$REPO_DIR" ]; then
    echo "Magic Box repo not found at $REPO_DIR." >&2
    exit 1
  fi
}

open_url() {
  local url="http://localhost:${WEB_PORT:-8080}"
  if command -v xdg-open >/dev/null 2>&1; then
    xdg-open "$url"
  elif command -v sensible-browser >/dev/null 2>&1; then
    sensible-browser "$url"
  else
    echo "Open $url in your browser" >&2
  fi
}

cmd="${1:-help}"
case "$cmd" in
  install)
    require_repo
    if [ "$(id -u)" -ne 0 ]; then
      exec sudo MAGICBOX_REPO_DIR="$REPO_DIR" "$REPO_DIR/scripts/install_pi.sh"
    else
      exec MAGICBOX_REPO_DIR="$REPO_DIR" "$REPO_DIR/scripts/install_pi.sh"
    fi
    ;;
  start)
    exec sudo systemctl start "${SERVICES[@]}"
    ;;
  stop)
    exec sudo systemctl stop "${SERVICES[@]}"
    ;;
  restart)
    exec sudo systemctl restart "${SERVICES[@]}"
    ;;
  status)
    exec sudo systemctl status "${SERVICES[@]}"
    ;;
  logs)
    exec sudo journalctl -u magic_lid.service -u magic_lid_web.service -u jv-status-led.service -f
    ;;
  logs-main)
    exec sudo journalctl -u magic_lid.service -f
    ;;
  logs-web)
    exec sudo journalctl -u magic_lid_web.service -f
    ;;
  logs-led)
    exec sudo journalctl -u jv-status-led.service -f
    ;;
  open)
    open_url
    ;;
  export-logs)
    require_repo
    if [ "$(id -u)" -ne 0 ]; then
      exec sudo /usr/bin/python3 "$REPO_DIR/tools/export_logs_to_boot.py"
    else
      exec /usr/bin/python3 "$REPO_DIR/tools/export_logs_to_boot.py"
    fi
    ;;
  *)
    usage
    ;;

esac
EOF_HELPER
  chmod +x "$helper_path"
  mkdir -p "$(dirname "$config_file")"
  log "Installed helper command at $helper_path"
}

create_desktop_launcher() {
  local launcher_user="$1"
  local web_port="$2"
  local launcher_path="$3"
  if ! id -u "$launcher_user" >/dev/null 2>&1; then
    log "Desktop launcher skipped; user $launcher_user not found"
    return
  fi

  local desktop_dir
  desktop_dir=$(dirname "$launcher_path")
  mkdir -p "$desktop_dir"

  cat >"$launcher_path" <<EOF_DESKTOP
[Desktop Entry]
Type=Application
Name=Magic Lid Web Remote
Comment=Open the Magic Lid web remote in your browser
Exec=xdg-open http://localhost:$web_port
Terminal=false
Categories=Utility;Network;
EOF_DESKTOP

  chown "$launcher_user":"$launcher_user" "$launcher_path" || true
  chmod +x "$launcher_path"
  log "Installed desktop launcher at $launcher_path"
}

start_services() {
  log "Reloading systemd daemon and enabling services"
  systemctl daemon-reload
  systemctl enable --now magic_lid.service
  systemctl enable --now magic_lid_web.service
  systemctl enable --now jv-status-led.service
  systemctl enable --now magic_lid.path
  log "Services enabled: magic_lid.service, magic_lid_web.service, jv-status-led.service"
}

main() {
  require_root
  warn_if_not_pi

  SOURCE_REPO_DIR=${MAGICBOX_REPO_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}
  SYSTEMD_DIR="/etc/systemd/system"
  HELPER_PATH="/usr/local/bin/magicbox"
  RUNTIME_CONF="/etc/julesverne_magicbox/runtime.conf"
  SERVICE_USER=$(resolve_runtime_user)
  STATE_DIR="/var/lib/julesverne_magicbox"
  LOG_DIR="/var/log/julesverne_magicbox"
  INSTALL_ROOT_DEFAULT="/opt/julesvern/JulesVern_MagicBox"
  TARGET_REPO=${MAGICBOX_TARGET:-$INSTALL_ROOT_DEFAULT}
  WEB_PORT=${MAGICBOX_WEB_PORT:-8080}
  LAUNCHER_USER=${MAGICBOX_LAUNCHER_USER:-${SUDO_USER:-$SERVICE_USER}}

  if [ ! -f "$SOURCE_REPO_DIR/src/main.py" ]; then
    echo "Repository not found at $SOURCE_REPO_DIR (main.py missing)." >&2
    exit 1
  fi

  log "Using existing user for services: $SERVICE_USER"
  ensure_user_groups "$SERVICE_USER"
  install_shutdown_sudoers "$SERVICE_USER"

  log "Copying repo to $TARGET_REPO"
  copy_repo "$SOURCE_REPO_DIR" "$TARGET_REPO"
  REPO_DIR="$TARGET_REPO"
  CONFIG_PATH="$REPO_DIR/src/config.py"
  DESKTOP_PATH="$(get_home_dir "$LAUNCHER_USER")/Desktop/Magic Lid Web Remote.desktop"

  log "Using repository at $REPO_DIR"
  log "Web UI port: $WEB_PORT"
  log "State directory: $STATE_DIR"
  log "Log directory: $LOG_DIR"

  install_apt_packages
  if ! /usr/bin/python3 --version; then
    echo "Unable to run /usr/bin/python3. Ensure Python 3 is installed." >&2
    exit 1
  fi

  if ! getent group adm >/dev/null 2>&1; then
    echo "Required group 'adm' is missing; cannot set log permissions." >&2
    exit 1
  fi

  mkdir -p "$STATE_DIR" "$LOG_DIR"
  chown -R "$SERVICE_USER":adm "$STATE_DIR" "$LOG_DIR"
  chmod -R 775 "$STATE_DIR" "$LOG_DIR"

  chown -R "$SERVICE_USER":"$SERVICE_USER" "$REPO_DIR"

  write_runtime_conf "$RUNTIME_CONF" "$REPO_DIR" "$SERVICE_USER" "$WEB_PORT"
  install_services "$SYSTEMD_DIR" "$REPO_DIR" "$WEB_PORT" "$RUNTIME_CONF" "$CONFIG_PATH"
  install_helper_command "$HELPER_PATH" "$RUNTIME_CONF"
  create_desktop_launcher "$LAUNCHER_USER" "$WEB_PORT" "$DESKTOP_PATH"
  start_services

  log "SUCCESS: Magic Box installed."
  log "Reboot recommended to ensure group membership changes apply."
  log "Service status commands:"
  log "  sudo systemctl status magic_lid.service --no-pager"
  log "  sudo systemctl status magic_lid_web.service --no-pager"
}

main "$@"
