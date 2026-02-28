import cv2
import numpy as np
import time
from pose_estimator import PoseEstimator
from fall_detector import FallDetector
from notifier import send_fall_alert, send_clear_alert
from mcu_comm import connect, send_command, disconnect
from config import CAMERA_INDEX
from server import socketio, emit_status, emit_frame, emit_countdown, emit_keypoint, run_server
import threading

INITIAL_COUNTDOWN = 30   # seconds before escalation
STANDUP_BONUS     = 30   # added when person stands up
REFALL_PENALTY    = 30   # subtracted when person falls again after standing

def draw_overlay(frame, status, keypoints=None, countdown=None):
    h, w = frame.shape[:2]

    # Status banner color
    if status == "FALL" or status == "COUNTDOWN":
        color = (0, 0, 255)
        label = "FALL DETECTED"
    elif status == "ALERT":
        color = (0, 165, 255)
        label = "MONITORING..."
    elif status == "STOOD_UP":
        color = (0, 140, 255)
        label = "STOOD UP — CONFIRM OK?"
    else:
        color = (0, 200, 0)
        label = "ALL CLEAR"

    cv2.rectangle(frame, (0, 0), (w, 60), color, -1)
    cv2.putText(frame, label, (20, 42),
                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)

    # Countdown overlay
    if countdown is not None and countdown > 0:
        urgency = (0, 0, 255) if countdown <= 10 else (0, 100, 255)
        text = f"EMERGENCY IN: {int(countdown)}s"
        cv2.rectangle(frame, (0, 60), (w, 110), (20, 20, 20), -1)
        cv2.putText(frame, text, (20, 98),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, urgency, 2)
        # Progress bar
        bar_w = int(w * (countdown / INITIAL_COUNTDOWN))
        bar_w = min(bar_w, w)
        cv2.rectangle(frame, (0, 108), (bar_w, 114), urgency, -1)

    # Skeleton
    if keypoints:
        for name, kp in keypoints.items():
            x, y = int(kp[0]), int(kp[1])
            if -50 < x < w+50 and -50 < y < h+50:
                cv2.circle(frame, (x, y), 6, (0, 255, 0), -1)
                cv2.putText(frame, name[:3], (x+5, y-5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 255, 0), 1)
        bones = [
            ("left_shoulder", "right_shoulder"),
            ("left_shoulder", "left_elbow"),
            ("right_shoulder", "right_elbow"),
            ("left_shoulder", "left_hip"),
            ("right_shoulder", "right_hip"),
            ("left_hip", "right_hip"),
            ("left_hip", "left_knee"),
            ("right_hip", "right_knee"),
            ("left_knee", "left_ankle"),
            ("right_knee", "right_ankle"),
        ]
        for a, b in bones:
            if a in keypoints and b in keypoints:
                x1, y1 = int(keypoints[a][0]), int(keypoints[a][1])
                x2, y2 = int(keypoints[b][0]), int(keypoints[b][1])
                if -50 < x1 < w+50 and -50 < y1 < h+50 and -50 < x2 < w+50 and -50 < y2 < h+50:
                    cv2.line(frame, (x1, y1), (x2, y2), (255, 255, 0), 2)

    return frame


def main():
    print("[GuardianEye] Starting system...")
    connect()

    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    pose = PoseEstimator()
    detector = FallDetector()

    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        print("[GuardianEye] ERROR — Could not open camera.")
        return

    print("[GuardianEye] Camera opened. Running live detection.")
    print("[GuardianEye] Press Q to quit, R to cancel alert.")

    # State machine
    current_status   = "CLEAR"
    notification_sent = False
    countdown_end    = None   # time.time() when escalation fires
    stood_up         = False  # did person stand up after the fall?

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[GuardianEye] ERROR — Could not read frame.")
            break

        h, w = frame.shape[:2]
        keypoints = pose.get_keypoints(frame)
        if keypoints and "nose" in keypoints:
            nose_x_pct = keypoints["nose"][0] / w
            nose_y_pct = keypoints["nose"][1] / h
            emit_keypoint(nose_x_pct, nose_y_pct)
        det_status = detector.process_frame(keypoints, h)

        # ── TRANSITION LOGIC ──────────────────────────────────────────

        if current_status == "CLEAR":
            if det_status == "FALL":
                # New fall detected
                current_status = "COUNTDOWN"
                stood_up = False
                countdown_end = time.time() + INITIAL_COUNTDOWN
                if not notification_sent:
                    send_fall_alert()
                    send_command("FALL")
                    notification_sent = True
                print(f"[GuardianEye] FALL — countdown started ({INITIAL_COUNTDOWN}s)")

            elif det_status == "ALERT":
                current_status = "ALERT"

            else:
                current_status = "CLEAR"

        elif current_status == "ALERT":
            if det_status == "FALL":
                current_status = "COUNTDOWN"
                stood_up = False
                countdown_end = time.time() + INITIAL_COUNTDOWN
                if not notification_sent:
                    send_fall_alert()
                    send_command("FALL")
                    notification_sent = True
                print(f"[GuardianEye] FALL — countdown started ({INITIAL_COUNTDOWN}s)")
            elif det_status == "CLEAR":
                current_status = "CLEAR"

        elif current_status == "COUNTDOWN":
            remaining = countdown_end - time.time()

            if det_status == "CLEAR" and not stood_up:
                # Person stood up for the first time — add bonus
                stood_up = True
                countdown_end += STANDUP_BONUS
                remaining = countdown_end - time.time()
                current_status = "STOOD_UP"
                print(f"[GuardianEye] Person stood up — +{STANDUP_BONUS}s added ({remaining:.0f}s remaining)")

            elif remaining <= 0:
                # Timer expired — escalate
                print("[GuardianEye] COUNTDOWN EXPIRED — ESCALATING TO EMERGENCY")
                current_status = "FALL"
                send_command("FALL")
                emit_status("EMERGENCY")

        elif current_status == "STOOD_UP":
            remaining = countdown_end - time.time()

            if det_status == "FALL":
                # Fell again after standing — subtract penalty
                stood_up = False
                countdown_end -= REFALL_PENALTY
                remaining = countdown_end - time.time()
                current_status = "COUNTDOWN"
                print(f"[GuardianEye] Person fell again — -{REFALL_PENALTY}s ({remaining:.0f}s remaining)")

            elif det_status == "CLEAR" and remaining > 0:
                # Still standing, still counting down
                pass

            elif remaining <= 0:
                print("[GuardianEye] COUNTDOWN EXPIRED — ESCALATING TO EMERGENCY")
                current_status = "FALL"
                send_command("FALL")
                emit_status("EMERGENCY")

        elif current_status == "FALL":
            # Latched — only manual R press resets
            pass

        # ── COUNTDOWN VALUE TO DISPLAY ────────────────────────────────
        countdown_display = None
        if current_status in ("COUNTDOWN", "STOOD_UP") and countdown_end:
            countdown_display = max(0, countdown_end - time.time())

        # ── EMIT TO DASHBOARD ─────────────────────────────────────────
        emit_status(current_status)
        if countdown_display is not None:
            emit_countdown(countdown_display)
        else:
            emit_countdown(None)

        # ── DRAW & SHOW ───────────────────────────────────────────────
        frame = draw_overlay(frame, current_status, keypoints, countdown_display)
        emit_frame(frame)
        cv2.imshow("GuardianEye — Live Detection", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            print("[GuardianEye] Shutting down.")
            break
        elif key == ord("r"):
            print("[GuardianEye] Manual cancel — alert cleared.")
            detector.reset()
            current_status = "CLEAR"
            notification_sent = False
            countdown_end = None
            stood_up = False
            send_clear_alert()
            send_command("CLEAR")
            emit_status("CLEAR")
            emit_countdown(None)

    cap.release()
    disconnect()
    cv2.destroyAllWindows()
    print("[GuardianEye] System stopped.")


if __name__ == "__main__":
    main()
