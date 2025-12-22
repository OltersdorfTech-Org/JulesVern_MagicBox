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
  apt-get install -y python3 python3-venv python3-pip python3-gpiozero python3-rpi.gpio
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

ensure_service_user() {
  local user="$1"
  local home_dir="$2"

  if id -u "$user" >/dev/null 2>&1; then
    log "Using existing service user: $user"
  else
    log "Creating service user: $user"
    useradd --system --create-home --home-dir "$home_dir" --shell /usr/sbin/nologin "$user"
  fi

  if getent group gpio >/dev/null 2>&1; then
    usermod -a -G gpio "$user"
  else
    log "Warning: gpio group not found; GPIO access may fail until the group exists."
  fi
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
  local data_dir="$6"
  local state_dir="$7"

  cat >"$unit_path" <<EOF_UNIT
[Unit]
Description=$description
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$user
Group=$user
WorkingDirectory=$workdir
ExecStart=$exec_cmd
Restart=on-failure
RestartSec=2
TimeoutStopSec=15
Environment=PYTHONUNBUFFERED=1
Environment=MAGICBOX_DATA_DIR=$data_dir
Environment=MAGICBOX_STATE_DIR=$state_dir
SupplementaryGroups=gpio

[Install]
WantedBy=multi-user.target
EOF_UNIT
  log "Wrote systemd unit $unit_path"
}

install_services() {
  local systemd_dir="$1"
  local venv_dir="$2"
  local repo_dir="$3"
  local user="$4"
  local web_port="$5"
  local data_dir="$6"
  local state_dir="$7"

  write_systemd_unit \
    "$systemd_dir/magic_lid.service" \
    "Magic Lid GPIO controller" \
    "$venv_dir/bin/python $repo_dir/src/main.py" \
    "$repo_dir" \
    "$user" \
    "$data_dir" \
    "$state_dir"

  write_systemd_unit \
    "$systemd_dir/magic_lid_web.service" \
    "Magic Lid Flask web server" \
    "$venv_dir/bin/python $repo_dir/src/web_server.py --port $web_port" \
    "$repo_dir" \
    "$user" \
    "$data_dir" \
    "$state_dir"
}

install_helper_command() {
  local helper_path="$1"
  local config_file="$2"
  cat >"$helper_path" <<'EOF_HELPER'
#!/usr/bin/env bash
set -euo pipefail

CONFIG_FILE="/etc/magicbox/config"
DEFAULT_REPO_DIR="/opt/julesvern"
DEFAULT_VENV_DIR="$DEFAULT_REPO_DIR/venv"
DEFAULT_USER="julesvern"
DEFAULT_DATA_DIR="/var/lib/julesvern"
SERVICES=(magic_lid.service magic_lid_web.service)

if [ -f "$CONFIG_FILE" ]; then
  # shellcheck source=/dev/null
  source "$CONFIG_FILE"
fi

REPO_DIR="${REPO_DIR:-$DEFAULT_REPO_DIR}"
VENV_DIR="${VENV_DIR:-$DEFAULT_VENV_DIR}"
SERVICE_USER="${SERVICE_USER:-$DEFAULT_USER}"
DATA_DIR="${DATA_DIR:-$DEFAULT_DATA_DIR}"
WEB_PORT="${WEB_PORT:-8080}"

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
magicbox open            # open the web UI in a browser on this machine
USAGE
}

require_repo() {
  if [ ! -d "$REPO_DIR" ]; then
    echo "Magic Box repo not found at $REPO_DIR. Set REPO_DIR in $CONFIG_FILE." >&2
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
      exec sudo MAGICBOX_REPO_DIR="$REPO_DIR" MAGICBOX_USER="$SERVICE_USER" MAGICBOX_DATA_DIR="$DATA_DIR" MAGICBOX_WEB_PORT="$WEB_PORT" "$REPO_DIR/scripts/install_pi.sh"
    else
      exec MAGICBOX_REPO_DIR="$REPO_DIR" MAGICBOX_USER="$SERVICE_USER" MAGICBOX_DATA_DIR="$DATA_DIR" MAGICBOX_WEB_PORT="$WEB_PORT" "$REPO_DIR/scripts/install_pi.sh"
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
    exec sudo journalctl -u magic_lid.service -u magic_lid_web.service -f
    ;;
  logs-main)
    exec sudo journalctl -u magic_lid.service -f
    ;;
  logs-web)
    exec sudo journalctl -u magic_lid_web.service -f
    ;;
  open)
    open_url
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

persist_config() {
  local config_file="$1"
  local repo_dir="$2"
  local venv_dir="$3"
  local user="$4"
  local web_port="$5"
  local data_dir="$6"
  mkdir -p "$(dirname "$config_file")"
  cat >"$config_file" <<EOF_CFG
REPO_DIR="$repo_dir"
VENV_DIR="$venv_dir"
SERVICE_USER="$user"
WEB_PORT="$web_port"
DATA_DIR="$data_dir"
EOF_CFG
  log "Saved config to $config_file"
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
  log "Services enabled: magic_lid.service, magic_lid_web.service"
}

main() {
  require_root
  warn_if_not_pi

  SOURCE_REPO_DIR=${MAGICBOX_REPO_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}
  SYSTEMD_DIR="/etc/systemd/system"
  HELPER_PATH="/usr/local/bin/magicbox"
  CONFIG_FILE="/etc/magicbox/config"
  PYTHON_BIN="/usr/bin/python3"
  SERVICE_USER=${MAGICBOX_USER:-julesvern}
  SERVICE_HOME=${MAGICBOX_USER_HOME:-/var/lib/julesvern}
  DATA_DIR=${MAGICBOX_DATA_DIR:-/var/lib/julesvern}
  STATE_DIR="$DATA_DIR/state"
  INSTALL_ROOT_DEFAULT="/opt/julesvern"
  TARGET_REPO=${MAGICBOX_TARGET:-$INSTALL_ROOT_DEFAULT}
  WEB_PORT=${MAGICBOX_WEB_PORT:-8080}
  LAUNCHER_USER=${MAGICBOX_LAUNCHER_USER:-${SUDO_USER:-pi}}

  if [ ! -f "$SOURCE_REPO_DIR/src/main.py" ]; then
    echo "Repository not found at $SOURCE_REPO_DIR (main.py missing)." >&2
    exit 1
  fi

  log "Preparing service user"
  ensure_service_user "$SERVICE_USER" "$SERVICE_HOME"

  log "Copying repo to $TARGET_REPO"
  copy_repo "$SOURCE_REPO_DIR" "$TARGET_REPO"
  REPO_DIR="$TARGET_REPO"
  VENV_DIR="$REPO_DIR/venv"
  DESKTOP_PATH="$(get_home_dir "$LAUNCHER_USER")/Desktop/Magic Lid Web Remote.desktop"

  log "Using repository at $REPO_DIR"
  log "Service will run as user: $SERVICE_USER"
  log "Web UI port: $WEB_PORT"
  log "Data directory: $DATA_DIR"

  install_apt_packages
  mkdir -p "$DATA_DIR" "$STATE_DIR"
  chown -R "$SERVICE_USER":"$SERVICE_USER" "$DATA_DIR"

  create_venv "$PYTHON_BIN" "$VENV_DIR"
  chown -R "$SERVICE_USER":"$SERVICE_USER" "$REPO_DIR"

  install_services "$SYSTEMD_DIR" "$VENV_DIR" "$REPO_DIR" "$SERVICE_USER" "$WEB_PORT" "$DATA_DIR" "$STATE_DIR"
  install_helper_command "$HELPER_PATH" "$CONFIG_FILE"
  persist_config "$CONFIG_FILE" "$REPO_DIR" "$VENV_DIR" "$SERVICE_USER" "$WEB_PORT" "$DATA_DIR"
  create_desktop_launcher "$LAUNCHER_USER" "$WEB_PORT" "$DESKTOP_PATH"
  start_services

  log "SUCCESS: Magic Box installed. Next steps:\n  - Status: sudo systemctl status magic_lid.service magic_lid_web.service\n  - Logs: sudo journalctl -u magic_lid.service -u magic_lid_web.service -f\n  - Helper: magicbox status | magicbox logs"
}

main "$@"
