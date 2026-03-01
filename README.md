# UnderWatch

## Table of Contents
- [About](#about)
- [System Architecture](#system-architecture)
- [Timeline](#timeline)
- [Collaborators](#collaborators)

## About
A privacy first, AI powered elderly monitoring system that detects falls in real time and sends alerts through layered human verification before contacting emergency services.
Built for the Arduino UNO Q — all processing happens on-device, no cloud required.

## System Architecture
Infrared Camera
      ->
Fall Detection
      ->
Confidence Scoring
      ->
Decision State Machine
      ->
User Notification
      ->
Circle Notification
      ->
Emergency Escalation

## 🔐 Privacy Priorities

| Principle | Implementation |
|-----------|----------------|
| **Local Storage** | User information stored locally on-device |
| **Infrared Camera** | Additional anonymity — no identifiable video |
| **Confidence-Based Escalation** | AI confidence scoring before triggering alerts |
| **Multi-Layered Verification** | Human verification at each step before contacting emergency services |
| **No Cloud Processing** | All AI runs on-device via edge computing |
| **Local Network Streaming** | Live feed only accessible on home WiFi |

---

## 🛠️ Hardware

| Component | Purpose |
|-----------|---------|
| Arduino UNO Q (4GB) | Main processing unit |
| USB Webcam | Video input |
| 2x Servo Motors | Pan/tilt camera tracking |
| Push Button | "I'm OK" dismiss |
| Piezo Buzzer | Audio alerts |

---

## 📱 Family Interface

Family members receive push notifications and can view a live feed through a Progressive Web App (PWA) on their phone — no app store download required.

**Features:**
- Real-time video stream
- "I'm OK" remote dismiss
- One-tap emergency call
- Connection status indicator

---


## Timeline
1. Camera Fall Detection
   - AI detects if user has fallen/not fallen.
2. Fall Detection Signal
   - Sends a notification when a fall occurs.
   - Printed words -> lights -> lights and sounds.
3. Signal Off Button
   - A button that resets the program.
4. Inactivity Emergency Contact
   - Sends a notification after total inactivity.
   - Emergency services -> circle members then emergency services.
5. Print Camera Housing
   - Print housing for cameras and servos.
6. Implement Camera Movement
   - Camera movement tracks user.
   - Horizontal tracking -> horizontal and vertical tracking.
7. Implement Circle Member Viewing
   - UI for circle members to see, proceed with, and cancel contact.
   - Display options to proceed/cancel emergency services -> display video clip of fall and options to proceed/cancel.

## Collaborators
| Name        | Role            | GitHub / Identifier |
|-------------|-----------------|---------------------|
| Adam Le     | Software        | adamvl7             |
| Kevin Chhim | Embedded        | kevinlycc           |
| Ryan Ong    | Project Manager | riannongg           |
| Sam Phan    | Tech Ops        | blayyd              |
