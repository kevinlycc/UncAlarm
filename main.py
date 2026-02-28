import cv2
import numpy as np
from pose_estimator import PoseEstimator
from fall_detector import FallDetector
from notifier import send_fall_alert, send_clear_alert
from config import CAMERA_INDEX

def draw_overlay(frame, status, keypoints=None):
    """
    Draws the status banner and keypoints on the frame.
    """
    h, w = frame.shape[:2]

    # Status banner
    if status == "FALL":
        color = (0, 0, 255)      # Red
        label = "FALL DETECTED"
    elif status == "ALERT":
        color = (0, 165, 255)    # Orange
        label = "MONITORING..."
    else:
        color = (0, 200, 0)      # Green
        label = "ALL CLEAR"

    # Draw banner background
    cv2.rectangle(frame, (0, 0), (w, 60), color, -1)

    # Draw status text
    cv2.putText(
        frame, label,
        (20, 42),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.2, (255, 255, 255), 3
    )

    # Draw skeleton if keypoints available
    if keypoints:
        h, w = frame.shape[:2]
        # Draw keypoint dots
        for name, kp in keypoints.items():
            x, y = int(kp[0]), int(kp[1])
            if -50 < x < w+50 and -50 < y < h+50:
                cv2.circle(frame, (x, y), 6, (0, 255, 0), -1)
                cv2.putText(frame, name[:3], (x+5, y-5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 255, 0), 1)
        # Draw skeleton lines
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

    # Initialize components
    pose = PoseEstimator()
    detector = FallDetector()

    # Open camera
    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        print("[GuardianEye] ERROR — Could not open camera. Check CAMERA_INDEX in config.py")
        return

    print("[GuardianEye] Camera opened. Running live detection.")
    print("[GuardianEye] Press Q to quit, R to reset alert.")

    current_status = "CLEAR"
    notification_sent = False

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[GuardianEye] ERROR — Could not read frame from camera.")
            break

        h, w = frame.shape[:2]

        # Get pose keypoints
        keypoints = pose.get_keypoints(frame)

        # Run fall detection
        status = detector.process_frame(keypoints, h)

        # Handle state transitions
        if status == "FALL" and current_status != "FALL":
            current_status = "FALL"
            if not notification_sent:
                send_fall_alert()
                notification_sent = True

        elif status == "CLEAR" and current_status == "FALL":
            current_status = "CLEAR"
            notification_sent = False
            send_clear_alert()
            detector.reset()

        else:
            current_status = status

        # Draw overlay on frame
        frame = draw_overlay(frame, current_status, keypoints)

        # Show the window
        cv2.imshow("GuardianEye — Live Detection", frame)

        # Key controls
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            print("[GuardianEye] Shutting down.")
            break
        elif key == ord("r"):
            print("[GuardianEye] Manual reset triggered.")
            detector.reset()
            current_status = "CLEAR"
            notification_sent = False

    cap.release()
    cv2.destroyAllWindows()
    print("[GuardianEye] System stopped.")


if __name__ == "__main__":
    main()