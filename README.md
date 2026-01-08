Jules Verne Magic Box

A narrative-driven, physical puzzle box controller built on Raspberry Pi

The Jules Verne Magic Box is a small, headless Raspberry Pi–based controller designed to bring physical puzzle boxes, artifacts, and story-driven installations to life.

It combines simple physical inputs (lid switch, keys), visual outputs (LEDs), and a minimal web interface into a deterministic, reliable system suitable for long-term installations, classroom use, or maker projects where magic should feel intentional, not glitchy.

This repository contains everything needed to build, wire, install, and operate the controller—excluding physical schematics and images, which are intentionally added later by hand.

What this project is (and is not)

This project is:

A fixed-hardware, fixed-GPIO controller for a physical box or artifact

Designed for Raspberry Pi Zero 2 W

Headless, reliable, and service-based

Friendly to non-Linux users during setup

Explicitly documented so behavior is predictable

This project is not:

A general-purpose IoT framework

A configurable GPIO playground

A containerized or cloud-dependent system

A desktop application

A “figure it out as you go” prototype

Every design choice here favors clarity over flexibility.

High-level behavior

At runtime, the system:

Monitors physical switches:

Lid open/closed

Two independent keys

Drives LEDs:

Status / fault indicator

Message indicator

Key 1 LED

Key 2 LED

“Magic” effect LED

Exposes a local web UI for:

Viewing system state

Enabling/disabling interactive outputs

Triggering log export

Viewing logs

Signals all fault conditions via the Status LED, even if:

Wi-Fi is down

The web UI is unreachable

Logs cannot be accessed

If the Pi boots successfully, the box always communicates its health visually.

Hardware assumptions (fixed)

Target board: Raspberry Pi Zero 2 W

Networking: Onboard Wi-Fi only

Power: USB (wall adapter or battery pack)

Operation: Headless after install

GPIO pins are fixed and non-configurable. This is intentional and documented.

Repository structure
/
├─ README.md
├─ AGENTS.md
│
├─ INSTALL_WINDOWS.md        # Step-by-step Pi setup (no Linux experience required)
├─ WIRING_GUIDE.md           # GPIO wiring for beginners
├─ USAGE_GUIDE.md            # How to use the box (9th-grade reading level)
│
├─ Tests/                    # Placeholder for future automated tests
│  └─ README.md
│
├─ Wiring_Diagram/           # Placeholder for schematics (added manually later)
│  └─ README.md
│
├─ specs/                    # Authoritative system specifications
│  ├─ 01_CONTROLLER_INTENT.md
│  ├─ 02_IO_DEFINITION.md
│  ├─ 03_BEHAVIOR_TRUTH_TABLE.md
│  ├─ 04_STATUS_LED_CODES.md
│  ├─ 05_LOGGING_AND_PERSISTENCE.md
│
├─ src/                      # All runtime code and installer scripts
│  ├─ installer.sh
│  ├─ uninstall.sh
│  ├─ magicbox/
│  └─ systemd/
│
└─ assets/                   # Image placeholders only (no binaries)
   └─ README.md

Getting started (recommended order)

Read this file to understand the system at a high level

Follow INSTALL_WINDOWS.md to prepare the SD card and Pi

Use WIRING_GUIDE.md to connect switches and LEDs

Power on the Pi and observe the Status LED

Read USAGE_GUIDE.md to understand normal operation

If something doesn’t behave as expected, the Status LED is the first thing to check.

Design philosophy (why this is so strict)

This project deliberately avoids:

Runtime pin reassignment

Virtual environments

Containers

Dynamic configuration files

Silent failure modes

Those features are powerful—but they also hide problems.

Here, everything is explicit:

Hardware is fixed

Behavior is documented

Failures are visible

Logs persist across reboots

Updates can be reasoned about

This makes the system suitable for:

Educational use

Public or semi-public installations

Long-running props

Storytelling artifacts that must feel intentional

Service checks and logs (commands)

Use these commands on the Pi to manage the service and view logs:

```bash
sudo systemctl status magicbox.service --no-pager
sudo systemctl restart magicbox.service
sudo journalctl -u magicbox.service -n 200 --no-pager
ls -la /var/log/magicbox/
ls -la /boot/firmware/
```

The web UI runs on port 5000 by default:

- `http://<pi_ip_address>:5000/`
- `http://<hostname>.local:5000/`

Next steps

Proceed to INSTALL_WINDOWS.md to set up your Pi

If you are contributing code or using GPT-Codex, read AGENTS.md

If you want to understand the system deeply, start with the files in specs/
