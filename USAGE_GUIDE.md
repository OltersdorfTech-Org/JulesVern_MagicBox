# USAGE_GUIDE.md  
**Using the Jules Verne Magic Box**  
*(Written for high-school level readers and up)*

This guide explains how to **use** the Jules Verne Magic Box once it is installed and wired.

You do **not** need to understand computers, Linux, or electronics to use the box.  
Everything important is communicated through **lights** and a **simple web page**.

If something ever seems wrong, start by checking the **Status LED**.

---

## What the box does

The Jules Verne Magic Box responds to:
- Opening and closing the lid
- Inserting or removing keys
- A small web interface for caretakers or operators

It uses LEDs to communicate:
- Whether the system is healthy
- Whether a message or object has been received
- Whether keys are present
- When a special “magic” moment is triggered

---

## The LEDs (what the lights mean)

### Status LED (most important)

The **Status LED** tells you the health of the system.

- **Blinking during startup**  
  The box is booting. This is normal.

- **Solid ON**  
  The box is ready and working normally.

- **Repeating blink patterns**  
  Something needs attention.

If the Status LED is blinking in a repeating pattern, the box is telling you what is wrong.  
Caretakers can look up the blink pattern in the documentation.

---

### Message / Indicator LED

This light turns ON when the system has been told that:
- A message has arrived
- An object has been received
- A story event is active

This LED is controlled from the web interface.

---

### Key LEDs (Key 1 and Key 2)

Each key has its own light.

- **LED ON** → that key is inserted or active
- **LED OFF** → that key is not present

Keys only light when the system is enabled.

---

### Magic LED

The **Magic LED** is special.

It only activates when:
- The lid is opened
- AND the “Message/Object Received” toggle is ON

When triggered, the Magic LED flashes in a random pattern for a short time.

This is intentional.  
It is meant to feel mysterious, not mechanical.

---

## The lid

- Opening the lid by itself does nothing special
- The lid becomes meaningful **only** when a message or object has been marked as received

This prevents accidental activation.

---

## The web interface (caretaker controls)

The web interface is used by caretakers, builders, or operators.

It is **not required** for normal box interaction.

### Accessing the web interface
- Open a browser on the same Wi‑Fi network
- Go to the Pi’s address (for example):
  - `http://jv-magicbox.local`
  - or `http://192.168.x.x`

---

### Web controls explained

#### Message / Object Received (ON / OFF)
- ON → enables story interaction
- OFF → box remains idle

This does **not** turn the system on or off — it controls story state.

---

#### GPIO Enable / Disable
- ON → LEDs respond to keys and lid
- OFF → interactive LEDs are forced OFF

The Status LED is **never disabled**.

---

#### Show Logs
- Displays recent system messages
- Used for troubleshooting

---

#### Export Logs
- Saves a copy of system logs
- Logs are written to `/boot/firmware/MAGICBOX_LOGS/` by the service (root)
- Remove the SD card and read `MAGICBOX_LOGS/` on Windows

This is for caretakers, not users.

---

## Normal use flow (example)

1. Box is powered on
2. Status LED becomes solid ON
3. Caretaker sets “Message/Object Received” to ON
4. User opens the lid
5. Magic LED activates briefly
6. Keys light as they are inserted
7. Box remains idle until the next event

Nothing needs to be rushed.

---

## What NOT to do

- Do not unplug power while the box is running
- Do not press random web buttons without understanding them
- Do not rewire the box while powered
- Do not ignore repeating Status LED blink patterns

The box is patient. Treat it gently.

---

## If something looks wrong

1. Look at the **Status LED**
2. Wait at least 30 seconds after power-up
3. If blinking repeats, note the pattern
4. A caretaker can check logs if needed

Most problems are temporary and safe.

---

## Final note

This box is designed to:
- Feel intentional
- Behave predictably
- Communicate clearly
- Avoid surprises

If it feels calm and deliberate, it is working as designed.
