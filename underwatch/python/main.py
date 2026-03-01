# SPDX-FileCopyrightText: Copyright (C) ARDUINO SRL (http://www.arduino.cc)
# SPDX-License-Identifier: MPL-2.0

from arduino.app_utils import App
from arduino.app_bricks.web_ui import WebUI
from arduino.app_bricks.video_imageclassification import VideoImageClassification
from datetime import datetime, UTC
import json
import requests
import threading

# ── Tunable constants ──────────────────────────────────────────────────────────
FALL_CONFIRM_SECONDS     = 5.0
FALL_CLEAR_SECONDS       = 1.5
COUNTDOWN_1_SECONDS      = 30
COUNTDOWN_2_SECONDS      = 60
ADDITIONAL_TIME_ON_STAND = 30
NTFY_TOPIC               = "underWatch2026"
# ──────────────────────────────────────────────────────────────────────────────

# ── Ntfy ──────────────────────────────────────────────────────────────────────
def send_ntfy(title, message, priority="default", tags=""):
    def _send():
        try:
            requests.post(
                f"https://ntfy.sh/{NTFY_TOPIC}",
                headers={
                    "Title":        title.encode("ascii", errors="ignore").decode(),
                    "Priority":     priority,
                    "Tags":         tags,
                    "Content-Type": "text/plain; charset=utf-8",
                },
                data=message.encode("utf-8"),
                timeout=5
            )
            print(f"[Ntfy] Sent: {title}")
        except Exception as e:
            print(f"[Ntfy] Failed: {e}")
    threading.Thread(target=_send, daemon=True).start()

# ── Fall Alert Flow ───────────────────────────────────────────────────────────
class FallAlertFlow:
    def __init__(self, ui):
        self.ui = ui
        self.state = "IDLE"
        self.start_time = None
        self.stands_up_bonus_applied = False

    def update(self, now, is_fall_detected, is_person_standing):
        if self.state == "IDLE":
            return
        elapsed = (now - self.start_time).total_seconds()

        if self.state == "COUNTDOWN_1":
            remaining = max(0, COUNTDOWN_1_SECONDS - int(elapsed))
            self.ui.send_message("alert_status",
                f"WARNING: Fall detected. Dismiss or notifying family in {remaining}s")
            if elapsed >= COUNTDOWN_1_SECONDS:
                self.notify_family(now)

        elif self.state == "COUNTDOWN_2":
            current_limit = COUNTDOWN_2_SECONDS + (ADDITIONAL_TIME_ON_STAND if self.stands_up_bonus_applied else 0)
            if is_person_standing and not self.stands_up_bonus_applied:
                self.stands_up_bonus_applied = True
                self.ui.send_message("alert_status", "Activity detected! Adding 30s to countdown.")
            remaining = max(0, current_limit - int(elapsed))
            self.ui.send_message("alert_status",
                f"FAMILY NOTIFIED. Calling emergency in {remaining}s")
            if elapsed >= current_limit:
                self.call_emergency()

    def trigger_fall(self, now):
        if self.state == "IDLE":
            self.state = "COUNTDOWN_1"
            self.start_time = now
            self.stands_up_bonus_applied = False
            self.ui.send_message("fall_alert", "LOCAL_WARNING_STARTED")
            print("[UnderWatch] Fall confirmed — countdown started.")
            send_ntfy(
                title    = "UnderWatch - Fall Detected",
                message  = f"Fall detected at {now.strftime('%I:%M %p')}. Emergency in {COUNTDOWN_1_SECONDS}s unless dismissed.",
                priority = "high", tags = "warning,sos"
            )

    def notify_family(self, now):
        self.state = "COUNTDOWN_2"
        self.start_time = now
        self.ui.send_message("fall_alert", "FAMILY_NOTIFIED")
        print("[UnderWatch] Family notified.")
        send_ntfy(
            title    = "UnderWatch - Family Notified",
            message  = f"Alert not dismissed. Family notified. Emergency in {COUNTDOWN_2_SECONDS}s.",
            priority = "urgent", tags = "rotating_light,sos"
        )

    def call_emergency(self):
        self.state = "EMERGENCY"
        self.ui.send_message("fall_alert", "EMERGENCY_SERVICES_CALLED")
        print("[UnderWatch] CRITICAL: Calling emergency services!")
        send_ntfy(
            title    = "UnderWatch - EMERGENCY",
            message  = "Emergency services contacted. Go to patient immediately.",
            priority = "urgent", tags = "rotating_light,fire,sos"
        )

    def dismiss(self, now=None):
        if self.state != "IDLE":
            self.state = "IDLE"
            self.ui.send_message("fall_alert", "ALERT_DISMISSED")
            print("[UnderWatch] Alert dismissed.")
            send_ntfy(
                title    = "UnderWatch - Alert Resolved",
                message  = "Fall alert dismissed. Patient is okay.",
                priority = "default", tags = "white_check_mark"
            )

# ── Fall Streak Tracker ───────────────────────────────────────────────────────
class FallStreakTracker:
    def __init__(self):
        self.fall_streak_start  = None
        self.clear_streak_start = None
        self.confirmed          = False
        self.recent_confidences = []

    def reset(self):
        self.fall_streak_start  = None
        self.clear_streak_start = None
        self.confirmed          = False
        self.recent_confidences = []
        print("[StreakTracker] Reset.")

    def update(self, now, is_fall, confidence=0.0):
        triggered = False
        if is_fall:
            self.clear_streak_start = None
            self.recent_confidences.append((now, confidence))
            self.recent_confidences = [(t, c) for t, c in self.recent_confidences if (now - t).total_seconds() <= FALL_CONFIRM_SECONDS]
            if not self.confirmed:
                if self.fall_streak_start is None:
                    self.fall_streak_start = now
                    print("[StreakTracker] Fall streak started.")
                else:
                    streak = (now - self.fall_streak_start).total_seconds()
                    print(f"[StreakTracker] Fall streak: {streak:.1f}s / {FALL_CONFIRM_SECONDS}s needed")
                    if streak >= FALL_CONFIRM_SECONDS:
                        avg_confidence = sum(c for _, c in self.recent_confidences) / len(self.recent_confidences) if self.recent_confidences else 0.0
                        if avg_confidence > 0.9:
                            self.confirmed = True
                            triggered = True
                            print(f"[StreakTracker] Fall CONFIRMED after {streak:.1f}s. Avg confidence: {avg_confidence:.2f}")
                        else:
                            print(f"[StreakTracker] Streak reached but avg conf ({avg_confidence:.2f}) <= 0.9. Waiting...")
        else:
            self.fall_streak_start = None
            self.recent_confidences = []
            if self.confirmed:
                if self.clear_streak_start is None:
                    self.clear_streak_start = now
                else:
                    streak = (now - self.clear_streak_start).total_seconds()
                    if streak >= FALL_CLEAR_SECONDS:
                        self.confirmed = False
                        self.clear_streak_start = None
                        print(f"[StreakTracker] Fall cleared.")
        return triggered

# ── Setup ─────────────────────────────────────────────────────────────────────
ui               = WebUI()
alert_flow       = FallAlertFlow(ui)
streak_tracker   = FallStreakTracker()
detection_stream = VideoImageClassification(confidence=0.5, debounce_sec=0.0)

ui.on_message("override_th",   lambda sid, threshold: detection_stream.override_threshold(threshold))
ui.on_message("dismiss_alert", lambda sid, data: (alert_flow.dismiss(), streak_tracker.reset()))
ui.on_message("servo_move",    lambda sid, data: print(f"[Servo] pan={data.get('pan')} tilt={data.get('tilt')} (hardware not connected)"))

# ── Detection callback ────────────────────────────────────────────────────────
def send_detections_to_ui(classifications: dict):
    now = datetime.now(UTC)

    is_fall_detected   = "fall"   in classifications
    is_person_standing = "person" in classifications
    fall_confidence    = classifications.get("fall", 0.0)

    fall_triggered = streak_tracker.update(now, is_fall_detected, fall_confidence)
    if fall_triggered:
        alert_flow.trigger_fall(now)

    alert_flow.update(now, is_fall_detected, is_person_standing)

    if not classifications:
        return

    entries = [
        {"content": key, "confidence": value, "timestamp": now.isoformat()}
        for key, value in classifications.items()
    ]
    ui.send_message("classifications", message=json.dumps(entries))

detection_stream.on_detect_all(send_detections_to_ui)
App.run()