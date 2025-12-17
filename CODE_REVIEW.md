# Code Review

## Scope
- Reviewed Python sources: `src/main.py`, `src/web_server.py`, `src/config.py`.
- Reviewed front-end template `src/templates/remote_control.html` for integration concerns.
- Performed lightweight linting via bytecode compilation and checked dependency declarations in `requirements.txt`.

## Summary
The codebase is generally clear and organized, but there are a few robustness gaps (state writes, thread shutdown) and configuration-editing risks. Dependencies are unpinned and rely on platform packages that should be explicitly documented or constrained.

## Findings
### Correctness & Robustness
- **State file writes are not atomic.** `RemoteStateStore` opens and overwrites the JSON state file directly. A reboot or I/O error mid-write could leave a truncated JSON file that then loads as defaults silently. Use an atomic write (temporary file + replace) or a file lock to avoid partial writes and concurrent access issues.【F:src/main.py†L20-L87】
- **Background flicker thread is never joined on shutdown.** `MagicFlickerWorker` uses a daemon thread that relies on a stop event, but `_cleanup` closes GPIO devices without waiting for the thread to finish, which could leave a brief race where the worker toggles a closed LED. Consider joining the thread after signaling the stop event and before closing devices.【F:src/main.py†L89-L119】【F:src/main.py†L205-L294】
- **Config rewriting via regex is brittle.** The web UI updates `config.py` with a complex regex that assumes the dataclass field order and spacing. Any manual edits to `config.py` could cause the substitution to fail or misrewrite pins. A safer approach would be to parse the dataclass values (e.g., `ast`), or centralize pin configuration in a structured file (YAML/JSON) the UI can update deterministically.【F:src/web_server.py†L165-L187】
- **Pin validation stops at BCM lookup.** `pins_update` rejects non-numeric or non-GPIO physical pins but does not enforce that pins are unique or that they differ from power/ground once `PHYSICAL_TO_BCM` is extended. Duplicated pin assignments could silently overwrite each other in `config.py`. Consider validating uniqueness before writing.【F:src/web_server.py†L254-L283】

### Dependency Review
- `requirements.txt` leaves all versions unpinned. Pinning to tested versions of Flask and gpiozero reduces supply-chain risk and avoids unexpected API changes (e.g., Flask >=2.3 vs 3.x).【F:requirements.txt†L1-L2】
- `gpiozero` typically depends on `RPi.GPIO` or `lgpio` at runtime. The README covers apt installs, but the Python requirements do not list these runtime backends. Adding explicit extras or documentation for the expected backend would make deployments more reproducible, especially when installing via pip only.【F:requirements.txt†L1-L2】【F:README.md†L30-L62】

### Lint & Maintainability
- The UI repeatedly instantiates a `Button` in `read_lid_switch_state` for each page load; while closed immediately, it still touches GPIO and may log warnings on boards without the configured pin. Caching the state or guarding hardware access behind a feature flag could avoid noisy logs in development.【F:src/web_server.py†L108-L124】
- Safety toggles are enforced at the routing layer, but the backend service doesn’t log when safety is disabled on startup beyond the printed state. Consider aligning logging/telemetry between the web UI and daemon for easier troubleshooting.【F:src/main.py†L205-L279】【F:src/web_server.py†L204-L252】

## Tests / Checks Performed
- ✅ `python -m compileall src` (syntax check)【41d572†L1-L6】
