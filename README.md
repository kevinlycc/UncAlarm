# UnderWatch

## Table of Contents
- [About](#about)
- [System Architecture](#system-architecture)
- [Timeline](#timeline)
- [Collaborators](#collaborators)

## About
A privacy first, AI powered elderly monitoring system that detects falls in real time and sends alerts through layered human verification before contacting emergency servies. 

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

## Privacy Priorities
- User information stored locally.
- Infrared camera for additional anonymity.
- Confidence based escalation.
- Mulilayered human verification. 

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
