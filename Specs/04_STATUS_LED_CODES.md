# 04_STATUS_LED_CODES.md
**Jules Verne Magic Box — Status LED Codes (Authoritative Spec)**

Status LED GPIO:
- **GPIO 12**

Definitions:
- “Short blink” = **200 ms ON / 200 ms OFF**
- “Pause” = **LED OFF for 1.0 s**

## Status states (locked)

### Booting
- Pattern: **200 ms ON / 800 ms OFF** (≈1 Hz)

### Ready / Healthy
- Pattern: **Solid ON**

### Service failed to start
- Pattern: **2 short blinks → pause → repeat**

### Wi‑Fi not connected / no network
- Pattern: **2 short blinks → pause → repeat**
- Note: same blink code as “Service failed to start” is acceptable; logs must disambiguate.

### Web server down (service running)
- Pattern: **5 short blinks → pause → repeat**

### GPIO subsystem error (pin init failure)
- Pattern: **7 short blinks → pause → repeat**

### Log export failure
- Pattern: **1 short blink → pause → repeat**

### Unknown / unhandled exception
- Pattern: **800 ms ON / 200 ms OFF** (inverted fast blink)

## Priority rules
If multiple errors apply, show the **highest priority** code:
1) GPIO subsystem error (7)
2) Web server down (5)
3) Log export failure (1) — only while export is attempted; otherwise resume prior fault/ready state
4) Wi‑Fi not connected (2)
5) Service failed to start (2)
6) Unknown exception (inverted fast blink)

## Implementation note (non-binding)
It is acceptable to implement a single “current_status_code” variable updated by health checks and exception handlers, with the LED thread/task rendering the pattern.
