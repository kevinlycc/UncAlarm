import cv2
import numpy as np
import urllib.request
import os

MODEL_PATH = "pose_landmarker_full.task"
MODEL_URL = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/latest/pose_landmarker_full.task"

class PoseEstimator:
    def __init__(self):
        print("[GuardianEye] Loading MediaPipe Pose model...")

        # Download model if not present
        if not os.path.exists(MODEL_PATH):
            print("[GuardianEye] Downloading pose model (~30MB)...")
            urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
            print("[GuardianEye] Model downloaded.")

        from mediapipe.tasks import python as mp_python
        from mediapipe.tasks.python import vision as mp_vision
        from mediapipe.tasks.python.vision import RunningMode

        base_options = mp_python.BaseOptions(model_asset_path=MODEL_PATH)
        options = mp_vision.PoseLandmarkerOptions(
            base_options=base_options,
            running_mode=RunningMode.VIDEO,
            min_pose_detection_confidence=0.5,
            min_pose_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self.landmarker = mp_vision.PoseLandmarker.create_from_options(options)
        self.frame_timestamp_ms = 0
        print("[GuardianEye] Model loaded successfully.")

    def get_keypoints(self, frame):
        try:
            import mediapipe as mp
            h, w = frame.shape[:2]
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

            self.frame_timestamp_ms += 33  # ~30fps
            result = self.landmarker.detect_for_video(mp_image, self.frame_timestamp_ms)

            if not result.pose_landmarks or len(result.pose_landmarks) == 0:
                return None

            lm = result.pose_landmarks[0]

            def px(idx):
                p = lm[idx]
                return [p.x * w, p.y * h, p.z, p.visibility]

            keypoints = {
                "nose":           px(0),
                "left_shoulder":  px(11),
                "right_shoulder": px(12),
                "left_elbow":     px(13),
                "right_elbow":    px(14),
                "left_hip":       px(23),
                "right_hip":      px(24),
                "left_knee":      px(25),
                "right_knee":     px(26),
                "left_ankle":     px(27),
                "right_ankle":    px(28),
            }

            hip_y = (lm[23].y + lm[24].y) / 2 * h
            print(f"[PoseEstimator] Person detected. Hip Y: {hip_y:.1f}")
            return keypoints

        except Exception as e:
            print(f"[PoseEstimator] Error during inference: {e}")
            return None

    def get_midpoint(self, point_a, point_b):
        return ((point_a[0] + point_b[0]) / 2,
                (point_a[1] + point_b[1]) / 2)