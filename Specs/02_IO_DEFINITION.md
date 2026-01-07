# 02_IO_DEFINITION.md
**Jules Verne Magic Box — I/O Definition (Authoritative Spec)**

## Fixed GPIO mapping (locked, non-configurable)
### Inputs (normally open switches, wired GPIO → GND)
- **GPIO 27**: Lid switch (I1)
- **GPIO 05**: Key 1 switch (I2)
- **GPIO 06**: Key 2 switch (I3)

Input electrical requirements:
- Use **internal pull-up**
- Logical convention:
  - Switch open = HIGH (not pressed)
  - Switch closed to GND = LOW (pressed)

### Outputs (standard single-color LEDs, wired GPIO → resistor → LED → GND)
- **GPIO 12**: Status LED (O1)
- **GPIO 04**: Message/Indicator LED (O2)
- **GPIO 13**: Key 1 LED (O3)
- **GPIO 19**: Key 2 LED (O4)
- **GPIO 26**: Magic LED (O6)

Output requirements:
- Each LED has its **own** resistor (recommended 220–330Ω)
- Default state on boot: all non-status LEDs OFF (unless dictated by state machine)

### System outputs (non-GPIO)
- **O5**: Persistent rolling log (runtime + installer + service lifecycle)

## Web UI controls (inputs to the system state machine)
- I4: **Message/Object Received** (toggle ON/OFF)
- I5: **GPIO Enable/Disable** (toggle ON/OFF)
- I6: **Export Logs** (button/action)
- I7: **Show Logs** (button/action)

## GPIO master gate (I5)
When I5 = OFF, the controller must force **interactive LEDs OFF**:
- Gate set: **{O2, O3, O4, O6}**
- Status LED (O1) must remain active regardless of I5.
