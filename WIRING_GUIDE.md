# WIRING_GUIDE.md  
**Wiring the Jules Verne Magic Box (Beginner-Friendly Guide)**

This guide explains how to wire switches and LEDs to the **Raspberry Pi Zero 2 W** for the Jules Verne Magic Box.

It assumes:
- No prior electronics experience
- Fixed GPIO pin assignments (no configuration)
- Simple on/off switches and standard LEDs
- A breadboard or direct wiring

Take your time. Nothing here is fragile if you wire it carefully.

---

## Safety first (read this)

- **Never connect GPIO pins directly to 5V**
- **Always use a resistor with LEDs**
- **Power off the Pi before changing wiring**
- GPIO pins operate at **3.3V logic**

If something does not light up, *do not panic*. Most wiring issues are harmless and easy to fix.

---

## What you will need

### Components
- Raspberry Pi **Zero 2 W**
- Breadboard or jumper wires
- 5 × standard LEDs (3 mm or 5 mm)
- 5 × resistors (220–330 Ω recommended)
- 3 × normally-open momentary or toggle switches
- Jumper wires (male–female or male–male)
- Common **GND** connection

---

## How GPIO works (quick explanation)

- GPIO pins can be **inputs** (reading a switch)
- GPIO pins can be **outputs** (driving an LED)
- Inputs in this project use **internal pull-up resistors**
- That means:
  - Switch **open** = HIGH
  - Switch **closed (to GND)** = LOW

You do **not** need external resistors for switches.

---

## Fixed GPIO pin assignments (v1)

These pins are **hard-coded** and must be wired exactly as listed.

### Inputs
| Function        | GPIO |
|-----------------|------|
| Lid Switch      | 27   |
| Key 1 Switch    | 5    |
| Key 2 Switch    | 6    |

### Outputs
| Function              | GPIO |
|-----------------------|------|
| Status LED            | 12   |
| Message Indicator LED | 4    |
| Magic LED             | 26   |
| Key 1 LED             | 13   |
| Key 2 LED             | 19   |

### Ground
- Use **any GND pin** on the Raspberry Pi

---

## Wiring LEDs (very important)

### LED polarity
LEDs only work one way:

- **Long leg** → GPIO pin (through resistor)
- **Short leg** → GND

If the LED does not light:
- Reverse it
- Check the resistor
- Check the GPIO number

---

### LED wiring pattern (all LEDs)

```
GPIO ── Resistor ── LED ── GND
```

- Resistor value: **220 Ω to 330 Ω**
- One resistor **per LED**

---

### LED connections

| LED Function  | GPIO |
|--------------|------|
| Status LED   | 12   |
| Message LED  | 4    |
| Magic LED    | 26   |
| Key 1 LED    | 13   |
| Key 2 LED    | 19   |

---

## Wiring switches

All switches are wired the same way.

### Switch wiring pattern

```
GPIO ── Switch ── GND
```

- No resistor needed
- Switch must be **normally open**
- When pressed or closed, the switch connects GPIO to GND

---

### Switch connections

| Switch       | GPIO |
|-------------|------|
| Lid Switch  | 27   |
| Key 1       | 5    |
| Key 2       | 6    |

---

## Recommended wiring order

1. Wire **GND** first (common ground rail)
2. Wire the **Status LED (GPIO 12)** and test boot behavior
3. Wire the remaining LEDs
4. Wire switches last
5. Power on and observe behavior

---

## Verifying correct wiring

### Status LED behavior
- Blinking during boot is normal
- Solid ON indicates ready
- Repeating blink patterns indicate faults

### Common mistakes
- LED wired backwards
- Missing resistor
- Using wrong GPIO number
- Forgetting common ground
- Changing wiring while powered

---

## What NOT to do

- Do not connect LEDs without resistors
- Do not connect GPIO to 5V
- Do not hot-swap wires while powered
- Do not guess GPIO pin numbers

---

## Placeholder for wiring diagram

A detailed wiring diagram will be added later.

```
Wiring_Diagram/
└─ diagram_placeholder.png
```

(This file is intentionally not included in the repository.)

---

## Next steps

- Power on the Pi and observe the **Status LED**
- Proceed to **USAGE_GUIDE.md** to learn normal operation
