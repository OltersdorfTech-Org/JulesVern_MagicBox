"""Utilities for exporting logs to a Windows-readable partition."""
from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional, Sequence

import config

BOOT_CANDIDATES = (Path("/boot/firmware"), Path("/boot"))
SERVICE_LOGS = {
    "magic_lid.service": "magic_lid.service.log",
    "magic_lid_web.service": "magic_lid_web.service.log",
    "jv-status-led.service": "jv-status-led.service.log",
}


def select_boot_root(candidates: Sequence[Path] = BOOT_CANDIDATES) -> Path:
    mounted = [candidate for candidate in candidates if candidate.exists() and os.path.ismount(candidate)]
    if mounted:
        return mounted[0]
    existing = [candidate for candidate in candidates if candidate.exists()]
    if existing:
        return existing[0]
    raise FileNotFoundError("No boot partition found at /boot or /boot/firmware")


def export_logs(
    destination_root: Path,
    log_files: Iterable[Path],
) -> list[Path]:
    destination_root.mkdir(parents=True, exist_ok=True)
    copied: list[Path] = []
    for log_file in log_files:
        source = log_file
        if not source.exists():
            continue
        target = destination_root / source.name
        shutil.copy2(source, target)
        copied.append(target)
    return copied


def default_log_files() -> list[Path]:
    return [config.LOG_FILE_MAIN, config.LOG_FILE_WEB]


def _run_command(command: list[str]) -> str:
    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        return f"Command failed: {' '.join(command)} ({exc})"
    if result.returncode != 0:
        error = result.stderr.strip() or result.stdout.strip()
        return f"Command failed: {' '.join(command)} ({error})"
    return result.stdout.strip()


def _write_text(path: Path, content: str) -> None:
    path.write_text(content + "\n", encoding="utf-8")


def _system_info() -> str:
    lines = [
        f"uname: {platform.uname()}",
        f"python: {platform.python_version()}",
        "",
        "os-release:",
        _run_command(["cat", "/etc/os-release"]),
        "",
        "ip addr:",
        _run_command(["ip", "addr"]),
        "",
        "pip freeze:",
        _run_command(["python3", "-m", "pip", "freeze"]),
    ]
    return "\n".join(lines)


def _config_snapshot() -> dict:
    def pin_entry(pin: config.SignalPin) -> dict:
        return {
            "bcm_pin": pin.bcm_pin,
            "physical_pin": pin.physical_pin,
            "active_high": pin.active_high,
            "note": pin.note,
        }

    return {
        "pins": {
            "lid_switch": pin_entry(config.LID_SWITCH),
            "lid_led": pin_entry(config.LID_LED),
            "key1_switch": pin_entry(config.KEY1_SWITCH),
            "key2_switch": pin_entry(config.KEY2_SWITCH),
            "key1_led": pin_entry(config.KEY1_LED),
            "key2_led": pin_entry(config.KEY2_LED),
            "magic_led": pin_entry(config.MAGIC_LED),
        },
        "switch_pull_up": config.SWITCH_PULL_UP,
        "switch_debounce_s": config.SWITCH_DEBOUNCE_S,
        "magic_flicker_min_ms": config.MAGIC_FLICKER_MIN_MS,
        "magic_flicker_max_ms": config.MAGIC_FLICKER_MAX_MS,
        "main_loop_sleep_s": config.MAIN_LOOP_SLEEP_S,
        "status_file": str(config.STATUS_FILE),
        "log_dir": str(config.LOG_DIR),
        "state_dir": str(config.STATE_DIR),
        "app_version": config.APP_VERSION,
    }


def _journalctl(service: str) -> str:
    return _run_command(["journalctl", "-u", service, "--no-pager"])


def _copy_state_snapshot(destination: Path) -> None:
    if config.REMOTE_STATE_FILE.exists():
        shutil.copy2(config.REMOTE_STATE_FILE, destination)
    else:
        destination.write_text(
            json.dumps({"error": "state file missing"}, indent=2),
            encoding="utf-8",
        )


def build_export_bundle(destination_root: Path) -> Path:
    export_dir = destination_root / "jv_logs"
    export_dir.mkdir(parents=True, exist_ok=True)

    export_logs(export_dir, default_log_files())

    for service, filename in SERVICE_LOGS.items():
        _write_text(export_dir / filename, _journalctl(service))

    _write_text(export_dir / "system_info.txt", _system_info())
    (export_dir / "config_snapshot.json").write_text(
        json.dumps(_config_snapshot(), indent=2),
        encoding="utf-8",
    )
    _copy_state_snapshot(export_dir / "state_snapshot.json")
    _write_text(
        export_dir / "LAST_EXPORT.txt",
        datetime.now().isoformat(timespec="seconds"),
    )

    return export_dir


def ensure_writable_export_root(boot_root: Path) -> tuple[Path, Optional[str]]:
    destination_root = boot_root
    try:
        test_dir = destination_root / "jv_logs"
        test_dir.mkdir(parents=True, exist_ok=True)
        if not os.access(test_dir, os.W_OK):
            raise PermissionError(f"{test_dir} is not writable")
        return destination_root, None
    except OSError as exc:
        fallback = Path("/tmp")
        return fallback, f"Boot partition not writable ({exc}). Wrote logs to {fallback}."
