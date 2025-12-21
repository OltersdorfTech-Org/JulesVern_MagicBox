#!/usr/bin/env bash
set -euo pipefail

log() {
  echo "[magicbox] $*"
}

require_root() {
  if [ "$(id -u)" -ne 0 ]; then
    echo "This installer must run as root. Try: sudo $0"
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

create_desktop_launcher() {
  local user="$1"
  local web_port="$2"
  local launcher_path="$3"
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

  chown "$user":"$user" "$launcher_path" || true
  chmod +x "$launcher_path"
  log "Installed desktop launcher at $launcher_path"
}

ensure_user_exists() {
  local candidate="$1"
  if id -u "$candidate" >/dev/null 2>&1; then
    echo "$candidate"
    return
  fi
  log "User '$candidate' not found; defaulting to root for the service."
  echo "root"
}

install_apt_packages() {
  log "Installing system packages via apt..."
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -y
  apt-get install -y python3 python3-venv python3-pip python3-gpiozero python3-rpi.gpio
}

create_venv() {
  local python_bin="$1"
  local venv_dir="$2"
  if [ ! -d "$venv_dir" ]; then
    log "Creating virtual environment at $venv_dir"
    "$python_bin" -m venv "$venv_dir"
  else
    log "Reusing existing virtual environment at $venv_dir"
  fi
  # shellcheck source=/dev/null
  source "$venv_dir/bin/activate"
  pip install --upgrade pip
  pip install -r "$REPO_DIR/requirements.txt"
}

write_systemd_unit() {
  local unit_path="$1"
  local description="$2"
  local exec_cmd="$3"
  local workdir="$4"
  local user="$5"

  cat >"$unit_path" <<EOF_UNIT
[Unit]
Description=$description
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=$workdir
ExecStart=$exec_cmd
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal
User=$user

[Install]
WantedBy=multi-user.target
EOF_UNIT
  log "Wrote systemd unit $unit_path"
}

install_helper_command() {
  local helper_path="$1"
  local config_file="$2"
  cat >"$helper_path" <<'EOF_HELPER'
#!/usr/bin/env bash
set -euo pipefail

CONFIG_FILE="/etc/magicbox/config"
DEFAULT_REPO_DIR="/home/pi/JulesVern_MagicBox"
DEFAULT_VENV_DIR="$DEFAULT_REPO_DIR/.venv"
DEFAULT_USER="pi"

if [ -f "$CONFIG_FILE" ]; then
  # shellcheck source=/dev/null
  source "$CONFIG_FILE"
fi

REPO_DIR="${REPO_DIR:-$DEFAULT_REPO_DIR}"
VENV_DIR="${VENV_DIR:-$DEFAULT_VENV_DIR}"
SERVICE_USER="${SERVICE_USER:-$DEFAULT_USER}"

usage() {
  cat <<'USAGE'
magicbox install        # re-run the installer
magicbox start          # start the GPIO service
magicbox stop           # stop the GPIO service
magicbox restart        # restart the GPIO service
magicbox status         # service status
magicbox logs           # follow live logs
USAGE
}

require_repo() {
  if [ ! -d "$REPO_DIR" ]; then
    echo "Magic Box repo not found at $REPO_DIR. Set REPO_DIR in $CONFIG_FILE."
    exit 1
  fi
}

cmd="${1:-help}"
case "$cmd" in
  install)
    require_repo
    if [ "$(id -u)" -ne 0 ]; then
      exec sudo MAGICBOX_REPO_DIR="$REPO_DIR" MAGICBOX_USER="$SERVICE_USER" "$REPO_DIR/scripts/install_pi.sh"
    else
      exec MAGICBOX_REPO_DIR="$REPO_DIR" MAGICBOX_USER="$SERVICE_USER" "$REPO_DIR/scripts/install_pi.sh"
    fi
    ;;
  start)
    exec sudo systemctl start magic_lid.service
    ;;
  stop)
    exec sudo systemctl stop magic_lid.service
    ;;
  restart)
    exec sudo systemctl restart magic_lid.service
    ;;
  status)
    exec sudo systemctl status magic_lid.service
    ;;
  logs)
    exec sudo journalctl -u magic_lid.service -f
    ;;
  *)
    usage
    ;;

esac
EOF_HELPER
  chmod +x "$helper_path"
  log "Installed helper command at $helper_path"
  mkdir -p "$(dirname "$config_file")"
}

install_services() {
  local systemd_dir="$1"
  local venv_dir="$2"
  local repo_dir="$3"
  local user="$4"
  local web_port="$5"

  write_systemd_unit \
    "$systemd_dir/magic_lid.service" \
    "Magic Lid GPIO controller" \
    "$venv_dir/bin/python $repo_dir/src/main.py" \
    "$repo_dir" \
    "$user"

  write_systemd_unit \
    "$systemd_dir/magic_lid_web.service" \
    "Magic Lid Flask web server" \
    "$venv_dir/bin/python $repo_dir/src/web_server.py --port $web_port" \
    "$repo_dir" \
    "$user"
}

persist_config() {
  local config_file="$1"
  local repo_dir="$2"
  local venv_dir="$3"
  local user="$4"
  local web_port="$5"
  mkdir -p "$(dirname "$config_file")"
  cat >"$config_file" <<EOF_CFG
REPO_DIR="$repo_dir"
VENV_DIR="$venv_dir"
SERVICE_USER="$user"
WEB_PORT="$web_port"
EOF_CFG
  log "Saved config to $config_file"
}

start_services() {
  log "Reloading systemd daemon and enabling magic_lid.service"
  systemctl daemon-reload
  systemctl enable --now magic_lid.service
  log "magic_lid.service is active. Use 'sudo systemctl status magic_lid.service' to verify."
  log "Web service installed but not enabled by default. Enable with: sudo systemctl enable --now magic_lid_web.service"
}

main() {
  require_root
  warn_if_not_pi

  SOURCE_REPO_DIR=${MAGICBOX_REPO_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}
  SYSTEMD_DIR="/etc/systemd/system"
  HELPER_PATH="/usr/local/bin/magicbox"
  CONFIG_FILE="/etc/magicbox/config"
  PYTHON_BIN="/usr/bin/python3"
  TARGET_USER=$(ensure_user_exists "${MAGICBOX_USER:-${SUDO_USER:-pi}}")
  TARGET_HOME=$(get_home_dir "$TARGET_USER")
  TARGET_REPO_DEFAULT="$TARGET_HOME/JulesVern_MagicBox"
  TARGET_REPO=${MAGICBOX_TARGET:-$TARGET_REPO_DEFAULT}
  WEB_PORT=${MAGICBOX_WEB_PORT:-8080}

  if [ ! -f "$SOURCE_REPO_DIR/src/main.py" ]; then
    echo "Repository not found at $SOURCE_REPO_DIR (main.py missing)." >&2
    exit 1
  fi

  if [ "$SOURCE_REPO_DIR" != "$TARGET_REPO" ]; then
    log "Copying repo to $TARGET_REPO for service use"
    copy_repo "$SOURCE_REPO_DIR" "$TARGET_REPO"
    REPO_DIR="$TARGET_REPO"
  else
    REPO_DIR="$SOURCE_REPO_DIR"
  fi

  VENV_DIR="$REPO_DIR/.venv"
  DESKTOP_PATH="$TARGET_HOME/Desktop/Magic Lid Web Remote.desktop"

  log "Using repository at $REPO_DIR"
  log "Service will run as user: $TARGET_USER"
  log "Web UI port: $WEB_PORT"

  install_apt_packages
  mkdir -p "$REPO_DIR/state"
  create_venv "$PYTHON_BIN" "$VENV_DIR"
  chown -R "$TARGET_USER" "$REPO_DIR"
  install_services "$SYSTEMD_DIR" "$VENV_DIR" "$REPO_DIR" "$TARGET_USER" "$WEB_PORT"
  install_helper_command "$HELPER_PATH" "$CONFIG_FILE"
  persist_config "$CONFIG_FILE" "$REPO_DIR" "$VENV_DIR" "$TARGET_USER" "$WEB_PORT"
  create_desktop_launcher "$TARGET_USER" "$WEB_PORT" "$DESKTOP_PATH"
  start_services

  log "SUCCESS: Magic Box installed. Next steps:\n  - To see status: sudo systemctl status magic_lid.service\n  - To follow logs: sudo journalctl -u magic_lid.service -f\n  - To control via helper: magicbox status | magicbox logs"
}

main "$@"
