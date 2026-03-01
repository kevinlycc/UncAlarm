# MCU - Arduino Sketch for STM32U585

This sketch runs on the STM32U585 microcontroller side of the Arduino UNO Q. It handles real-time I/O while the Linux MPU runs the AI.

## Wiring

```
Arduino UNO Q (STM32 Pins)
│
├── D2  ◄── Push Button (other leg to GND)
├── D3  ──► Buzzer (+)
├── D9  ──► Pan Servo (signal)
├── D10 ──► Tilt Servo (signal)
├── 5V  ──► Servo VCC (both servos)
└── GND ──► Common ground (button, buzzer, servos)
```

## Button Wiring

The button uses the internal pull-up resistor. Connect:
- One leg → Pin D2
- Opposite leg (diagonal) → GND

No external resistor needed.

## Bridge Functions

The MPU (Python) can call these functions:

| Function | Parameters | Description |
|----------|------------|-------------|
| `set_servo_position` | `pan, tilt` (0-180) | Move camera servos |
| `center_servos` | none | Return servos to 90° |
| `set_status` | `0-4` | Update LED pattern |
| `start_countdown` | none | Start beeping countdown |
| `stop_countdown` | none | Stop beeping |
| `trigger_sos` | none | Play SOS alarm |
| `beep` | `freq, duration` | Single beep |

The MCU calls back to Python:
- `button_dismiss` — when button is pressed

## Status LED Patterns

| Status | Value | LED Pattern |
|--------|-------|-------------|
| CLEAR | 0 | Solid on |
| ALERT | 1 | Slow blink (500ms) |
| FALL | 2 | Medium blink (250ms) |
| COUNTDOWN | 3 | Fast blink (100ms) |
| SOS | 4 | Rapid flash (50ms) |

## Upload

Using Arduino App Lab:
```bash
arduino-app-cli sketch upload ./mcu
```

Or via Arduino IDE, select board: **Arduino UNO Q (STM32U585)**
