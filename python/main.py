# SPDX-FileCopyrightText: Copyright (C) ARDUINO SRL (http://www.arduino.cc)
#
# SPDX-License-Identifier: MPL-2.0

from arduino.app_utils import App
from arduino.app_bricks.web_ui import WebUI
from arduino.app_bricks.video_imageclassification import VideoImageClassification
from datetime import datetime, UTC, timedelta
import json
import collections

# Alert logic state constants
FALL_WINDOW_SECONDS = 10
COUNTDOWN_1_SECONDS = 30
COUNTDOWN_2_SECONDS = 60
ADDITIONAL_TIME_ON_STAND = 30

class FallAlertFlow:
    def __init__(self, ui):
        self.ui = ui
        self.state = "IDLE"  # IDLE, COUNTDOWN_1, NOTIFIED_FAMILY, COUNTDOWN_2, EMERGENCY
        self.start_time = None
        self.last_update_time = None
        self.stands_up_bonus_applied = False

    def update(self, now, is_fall_detected, is_person_standing):
        if self.state == "IDLE":
            return

        elapsed = (now - self.start_time).total_seconds()

        if self.state == "COUNTDOWN_1":
            # State behaviors: Buzzer and LED flashing
            self.ui.send_message("alert_status", f"WARNING: Fall detected. Dismiss or notifying family in {max(0, COUNTDOWN_1_SECONDS - int(elapsed))}s")
            # HW placeholders: buzzer.beep(), led.flash()
            
            if elapsed >= COUNTDOWN_1_SECONDS:
                self.notify_family(now)

        elif self.state == "COUNTDOWN_2":
            current_limit = COUNTDOWN_2_SECONDS + (ADDITIONAL_TIME_ON_STAND if self.stands_up_bonus_applied else 0)
            
            if is_person_standing and not self.stands_up_bonus_applied:
                self.stands_up_bonus_applied = True
                self.ui.send_message("alert_status", "Activity detected! Adding 30s to countdown.")

            self.ui.send_message("alert_status", f"FAMILY NOTIFIED. Calling emergency in {max(0, current_limit - int(elapsed))}s")
            
            if elapsed >= current_limit:
                self.call_emergency()

    def trigger_fall(self, now):
        if self.state == "IDLE":
            self.state = "COUNTDOWN_1"
            self.start_time = now
            self.stands_up_bonus_applied = False
            self.ui.send_message("fall_alert", "LOCAL_WARNING_STARTED")

    def notify_family(self, now):
        self.state = "COUNTDOWN_2"
        self.start_time = now # Reset timer for countdown 2
        self.ui.send_message("fall_alert", "FAMILY_NOTIFIED")
        print("ALERT: Family has been notified of the fall.")

    def call_emergency(self):
        self.state = "EMERGENCY"
        self.ui.send_message("fall_alert", "EMERGENCY_SERVICES_CALLED")
        print("CRITICAL: Calling emergency services!")

    def dismiss(self):
        if self.state != "IDLE":
            self.state = "IDLE"
            self.ui.send_message("fall_alert", "ALERT_DISMISSED")
            print("Alert dismissed.")

ui = WebUI()
alert_flow = FallAlertFlow(ui)
detection_stream = VideoImageClassification(confidence=0.5, debounce_sec=0.0)

# Buffer to store detections for temporal filtering (10 seconds)
detection_history = collections.deque()
last_alert_time = None

ui.on_message("override_th", lambda sid, threshold: detection_stream.override_threshold(threshold))
ui.on_message("dismiss_alert", lambda sid, data: alert_flow.dismiss())

# Example usage: Register a callback for when all objects are detected
def send_detections_to_ui(classifications: dict):
  global last_alert_time
  now = datetime.now(UTC)
  
  # Current detection state
  is_fall_detected = "fall" in classifications
  is_person_detected = "person" in classifications
  
  # Add current detection to history
  detection_history.append((now, is_fall_detected))
  
  # Remove detections older than FALL_WINDOW_SECONDS
  while detection_history and (now - detection_history[0][0]).total_seconds() > FALL_WINDOW_SECONDS:
    detection_history.popleft()

  # Temporal filter for initial trigger
  if len(detection_history) > 0:
    fall_count = sum(1 for _, fallen in detection_history if fallen)
    total_count = len(detection_history)
    window_duration = (detection_history[-1][0] - detection_history[0][0]).total_seconds()
    
    if fall_count > (total_count / 2) and window_duration >= FALL_WINDOW_SECONDS - 1:
      alert_flow.trigger_fall(now)

  # Update the state machine (handles countdowns and status messaging)
  alert_flow.update(now, is_fall_detected, is_person_detected)

  if len(classifications) == 0:
      return

      
  entries = []
  for key, value in classifications.items():
    entry = {
      "content": key,
      "confidence": value,
      "timestamp": datetime.now(UTC).isoformat()
    }
    entries.append(entry)    
  
  if len(entries) > 0:
    msg = json.dumps(entries)
    ui.send_message("classifications", message=msg)

detection_stream.on_detect_all(send_detections_to_ui)

App.run()
