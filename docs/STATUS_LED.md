# Status LED (GPIO12) Guide

## Intent
Provide a single external status LED on **BCM GPIO 12** that reflects booting, ready, and fault states without race conditions. A dedicated daemon owns the GPIO line and continuously evaluates system health to keep the LED accurate.

## Setup
1. Wire the LED: **GPIO12 → resistor (330Ω–1kΩ) → LED anode**, LED cathode → **GND**.
2. Ensure the new systemd unit files are installed:
   - `jv-status-led.service`
   - `jv-poweroff.service` (used by the UI shutdown button)
3. Enable and start the LED daemon:
   ```sh
   sudo systemctl enable --now jv-status-led.service
   ```
4. Verify the service is running:
   ```sh
   sudo systemctl status jv-status-led.service
   ```

## LED Patterns
- **BOOTING**: 1 Hz blink (0.5s ON / 0.5s OFF)
- **READY**: solid ON when the main app service is active
- **FAULT — Service failed**: 2 quick blinks then pause
- **FAULT — Wi-Fi not connected**: 3 quick blinks then pause
- **FAULT — No internet**: 4 quick blinks then pause
- **FAULT — Disk low**: 5 quick blinks then pause

Fault priority (highest wins):
1. Disk low
2. Service failed
3. Wi-Fi not connected
4. No internet

## Why this design
- A single daemon owns GPIO12 to avoid competing access from multiple processes.
- Continuous checks ensure the LED state reflects real-time system health (Wi-Fi drop, service crash, disk pressure).
- systemd ordering replaces brittle sleep-based sequencing.

## Assumptions
- The primary app service is `magic_lid.service`.
- `iwgetid` is available for SSID discovery (installed via `wireless-tools`).
- The LED is wired active-high with a resistor, and GPIO12 is free.

## Manual verification checklist
- Boot: observe 1 Hz blink.
- When app running: LED becomes solid ON.
- Stop app service: `sudo systemctl stop magic_lid.service` → 2-blink fault.
- Disconnect Wi-Fi: 3-blink fault.
- Break internet route (Wi-Fi still connected): 4-blink fault.
- Simulate disk low by raising the threshold constant: 5-blink fault.
- Click Shutdown in the web UI: system powers off safely.
