"""Shared GPIO status snapshot helpers for the controller and web UI."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import config


@dataclass
class GpioStatus:
    lid_closed: Optional[bool]
    remote_lid_on: bool
    magic_flag_on: bool
    safety_enabled: bool
    updated_at: str
    updated_at_unix: float
    last_error: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


def now_utc() -> tuple[str, float]:
    timestamp = datetime.now(timezone.utc)
    return timestamp.isoformat(timespec="seconds"), timestamp.timestamp()


def write_status(
    path: Path,
    lid_closed: Optional[bool],
    remote_lid_on: bool,
    magic_flag_on: bool,
    safety_enabled: bool,
    last_error: Optional[str] = None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    iso_time, unix_time = now_utc()
    status = GpioStatus(
        lid_closed=lid_closed,
        remote_lid_on=remote_lid_on,
        magic_flag_on=magic_flag_on,
        safety_enabled=safety_enabled,
        updated_at=iso_time,
        updated_at_unix=unix_time,
        last_error=last_error,
    )
    path.write_text(json.dumps(status.to_dict(), indent=2), encoding="utf-8")


def read_status(path: Path = config.STATUS_FILE) -> Optional[GpioStatus]:
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return GpioStatus(
        lid_closed=data.get("lid_closed"),
        remote_lid_on=bool(data.get("remote_lid_on", False)),
        magic_flag_on=bool(data.get("magic_flag_on", False)),
        safety_enabled=bool(data.get("safety_enabled", False)),
        updated_at=str(data.get("updated_at", "")),
        updated_at_unix=float(data.get("updated_at_unix", 0.0)),
        last_error=data.get("last_error"),
    )
