# 03_BEHAVIOR_TRUTH_TABLE.md
**Jules Verne Magic Box — Behavior Truth Table (Authoritative Spec)**

This file defines the **required behavior** for inputs and outputs.
All behavior must respect the GPIO master gate (I5) as described in `02_IO_DEFINITION.md`.

## State definitions
- I4 (Message/Object Received): logical story/event state
- I5 (GPIO Enable): software master gate for interactive LEDs

## Rules (authoritative)

### I1 — Lid switch (GPIO 27)
- Lid CLOSED → **No action**
- Lid OPEN → If **I4 = ON** then trigger **Magic LED** random flash pattern for **30 seconds**

Magic LED flash requirements:
- Uses GPIO 26
- Pattern: random ON/OFF pulses with randomized intervals (human-mystical, not rhythmic)
- Must stop automatically after 30 seconds
- Must be cancellable/interruptible by new triggers without crashing

### I2 — Key 1 switch (GPIO 05)
- Key 1 switch CLOSED → **Key 1 LED ON** (GPIO 13)
- Key 1 switch OPEN → **Key 1 LED OFF**

### I3 — Key 2 switch (GPIO 06)
- Key 2 switch CLOSED → **Key 2 LED ON** (GPIO 19)
- Key 2 switch OPEN → **Key 2 LED OFF**

### I4 — Web toggle: Message/Object Received
- I4 = ON → **Message LED ON** (GPIO 04)
- I4 = OFF → **Message LED OFF**

Note: I4 also gates the **Magic LED trigger** on lid-open.

### I5 — Web toggle: GPIO Enable/Disable
- I5 = ON → interactive LEDs may respond to inputs (subject to rules above)
- I5 = OFF → force **{Message LED, Key1 LED, Key2 LED, Magic LED} OFF** at all times
- Status LED is **never** disabled

### I6 — Web action: Export Logs
- On click: create an export bundle on the Pi and trigger a browser download **OR**
  write a copy to `/boot/firmware/` (Windows-readable) as specified in `05_LOGGING_AND_PERSISTENCE.md`.

### I7 — Web action: Show Logs
- On click/toggle: show recent log content in the web UI (tailing a bounded number of lines)

### I8 — System state: Pi booted / service health
- Status LED must represent boot/ready/fault as specified in `04_STATUS_LED_CODES.md`.

## Startup and default states
- On service start, default:
  - I4 = OFF
  - I5 = ON (recommended default) **unless explicitly set otherwise in code constants**
  - Non-status LEDs OFF until rules apply
