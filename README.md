# UnderWatch

**Privacy-first, edge-AI elderly monitoring system that detects falls in real time.**

Built for the Arduino UNO Q — all processing happens on-device, no cloud required.

## Features

- **Real-time fall detection** — MediaPipe pose estimation running locally
- **Privacy first** — Video never leaves the device
- **Camera tracking** — Pan/tilt servos follow the person
- **Smart escalation** — Layered verification before contacting emergency services
- **Live monitoring** — Family can view feed via local PWA
- **Push notifications** — Alerts via ntfy.sh (no app needed)

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       ARDUINO UNO Q                             │
│  ┌──────────────────────────────┐  ┌─────────────────────────┐  │
│  │   Qualcomm QRB2210 (Linux)   │  │   STM32U585 (MCU)       │  │
│  │                              │  │                         │  │
│  │   • MediaPipe Pose           │  │   • Servo control       │  │
│  │   • Fall detection           │◄─►   • Buzzer alerts       │  │
│  │   • Web server               │  │   • Button input        │  │
│  │   • Notifications            │  │   • LED status          │  │
│  └──────────────────────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
         │                                       │
         ▼                                       ▼
    USB Camera                           Physical Controls
   (Logitech Brio)                    (Button, Buzzer, Servos)
```

## Alert Flow

```
         Person Falls
              │
              ▼
    ┌─────────────────────┐
    │   COUNTDOWN #1      │ ◄─── Buzzer beeping
    │   (30 seconds)      │      LED flashing
    └─────────┬───────────┘
              │
    ┌─────────┴─────────┐
    │                   │
[BUTTON]            (timeout)
    │                   │
    ▼                   ▼
 DISMISS ✓      Family Notified
                        │
              ┌─────────┴─────────┐
              │                   │
    ┌─────────▼─────────┐         │
    │   COUNTDOWN #2    │    [APP DISMISS]
    │   (60 seconds)    │         │
    │   • +30s if       │         │
    │     person stands │         ▼
    └─────────┬─────────┘      DISMISS ✓
              │
           (timeout)
              │
              ▼
      Emergency Services
```

## Privacy Priorities

| Principle | Implementation |
|-----------|----------------|
| **Local Storage** | User information stored locally on-device |
| **Infrared Camera** | Additional anonymity — no identifiable video |
| **Confidence-Based Escalation** | AI confidence scoring before triggering alerts |
| **Multi-Layered Verification** | Human verification at each step before contacting emergency services |
| **No Cloud Processing** | All AI runs on-device via edge computing |
| **Local Network Streaming** | Live feed only accessible on home WiFi |

## Hardware

| Component | Purpose |
|-----------|---------|
| Arduino UNO Q (4GB) | Main processing unit |
| USB Webcam | Video input |
| 2x Servo Motors | Pan/tilt camera tracking |
| Push Button | "I'm OK" dismiss |
| Piezo Buzzer | Audio alerts |

## Family Interface

Family members receive push notifications and can view a live feed through a Progressive Web App (PWA) on their phone — no app store download required.

**Features:**
- Real-time video stream
- "I'm OK" remote dismiss
- One-tap emergency call
- Connection status indicator

## Quick Start

```bash
# Clone the repo
git clone https://github.com/kevinlycc/UnderWatch.git

# Install dependencies
pip install -r requirements.txt

# Configure your ntfy topic
# Edit config.py and set NTFY_TOPIC

# Run
python main.py
```

## Timeline

- [x] Camera fall detection with AI
- [x] Fall detection signal (buzzer + LED)
- [x] Signal off button
- [x] Inactivity emergency contact escalation
- [x] Camera movement tracking (pan/tilt)
- [ ] Print camera housing
- [ ] Circle member viewing UI with video playback

## Team

| Name | Role | GitHub |
|------|------|--------|
| Adam Le | Software | [@adamvl7](https://github.com/adamvl7) |
| Kevin Chhim | Embedded | [@kevinlycc](https://github.com/kevinlycc) |
| Ryan Ong | Project Manager | [@riannongg](https://github.com/riannongg) |
| Sam Phan | Tech Ops | [@blayyd](https://github.com/blayyd) |

<p align="center">
  Built with ❤️ at UCI IrvineHacks 2026
</p>
