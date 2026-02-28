import numpy as np
from config import (
    BODY_ANGLE_THRESHOLD, STILLNESS_FRAMES, STILLNESS_VARIANCE,
    FALL_HIP_Y_MAX, STAND_HIP_Y_MIN, RESET_COOLDOWN_FRAMES
)


class FallDetector:
    def __init__(self):
        self.angle_flagged = False
        self.drop_flagged = False
        self.fall_confirmed = False
        self.stillness_buffer = []
        self.prev_hip_y = None
        self.cooldown_counter = 0
        print("[GuardianEye] Fall detector initialized.")

    def reset(self):
        self.angle_flagged = False
        self.drop_flagged = False
        self.fall_confirmed = False
        self.stillness_buffer = []
        self.prev_hip_y = None
        self.cooldown_counter = RESET_COOLDOWN_FRAMES
        print("[GuardianEye] Fall detector reset.")

    def get_body_angle(self, keypoints):
        try:
            shoulder = np.array([
                (keypoints["left_shoulder"][0] + keypoints["right_shoulder"][0]) / 2,
                (keypoints["left_shoulder"][1] + keypoints["right_shoulder"][1]) / 2,
            ])
            hip = np.array([
                (keypoints["left_hip"][0] + keypoints["right_hip"][0]) / 2,
                (keypoints["left_hip"][1] + keypoints["right_hip"][1]) / 2,
            ])
            spine = hip - shoulder
            vertical = np.array([0, 1])
            cos_angle = np.dot(spine, vertical) / (np.linalg.norm(spine) * np.linalg.norm(vertical) + 1e-6)
            angle = np.degrees(np.arccos(np.clip(cos_angle, -1, 1)))
            return angle
        except Exception:
            return None

    def check_drop_velocity(self, keypoints, frame_height):
        hip_y = (keypoints["left_hip"][1] + keypoints["right_hip"][1]) / 2
        if self.prev_hip_y is not None:
            delta = self.prev_hip_y - hip_y  # negative = moving up in pixel space = dropping
            if delta > frame_height * 0.08:  # dropped more than 8% of frame height in one frame
                self.prev_hip_y = hip_y
                return True
        self.prev_hip_y = hip_y
        return False

    def check_stillness(self, keypoints):
        pos = np.array([
            keypoints["left_hip"][0], keypoints["left_hip"][1],
            keypoints["right_hip"][0], keypoints["right_hip"][1],
            keypoints["left_shoulder"][0], keypoints["left_shoulder"][1],
        ])
        self.stillness_buffer.append(pos)
        if len(self.stillness_buffer) > STILLNESS_FRAMES:
            self.stillness_buffer.pop(0)
        if len(self.stillness_buffer) < STILLNESS_FRAMES:
            return False
        variance = np.var(np.array(self.stillness_buffer), axis=0).mean()
        return variance < STILLNESS_VARIANCE

    def process_frame(self, keypoints, frame_height):
        if keypoints is None:
            return "CLEAR"

        if self.cooldown_counter > 0:
            self.cooldown_counter -= 1
            return "CLEAR"

        # Calculate bounding box of all keypoints
        xs = [keypoints[k][0] for k in keypoints]
        ys = [keypoints[k][1] for k in keypoints]
        body_width = max(xs) - min(xs)
        body_height = max(ys) - min(ys)

        # Aspect ratio: standing person is tall (height > width)
        # Fallen person is wide (width > height)
        if body_height < 1:
            return "CLEAR"

        aspect_ratio = body_width / body_height  # >1 = wide = fallen, <1 = tall = standing

        angle = self.get_body_angle(keypoints)
        angle_str = f"{angle:.1f}" if angle is not None else "None"
        print(f"[FallDetector] aspect={aspect_ratio:.2f} body_w={body_width:.0f} body_h={body_height:.0f} angle={angle_str}")

        if self.fall_confirmed:
            # Reset when person is upright again (tall and narrow)
            if aspect_ratio < 0.8:
                self.reset()
                return "CLEAR"
            return "FALL"

        # Flag if person is wider than tall (aspect ratio > 1.2)
        if aspect_ratio > 1.2:
            self.angle_flagged = True

        if self.check_drop_velocity(keypoints, frame_height):
            self.drop_flagged = True

        if self.angle_flagged or self.drop_flagged:
            if self.check_stillness(keypoints):
                if aspect_ratio > 1.2:
                    self.fall_confirmed = True
                    print("[GuardianEye] FALL CONFIRMED")
                    return "FALL"
                else:
                    self.angle_flagged = False
                    self.drop_flagged = False
                    self.stillness_buffer = []
            return "ALERT"

        return "CLEAR"
