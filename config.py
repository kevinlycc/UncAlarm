# GuardianEye Configuration
# Tune these values during testing without touching core logic

# Fall Detection Thresholds
BODY_ANGLE_THRESHOLD = 60       # degrees from vertical to flag a fall
DROP_VELOCITY_THRESHOLD = 0.30  # % of frame height dropped per 0.5s
STILLNESS_FRAMES = 12           # frames of stillness required to confirm fall
STILLNESS_VARIANCE = 50         # coordinates are in pixels not normalized
FALL_HIP_Y_MAX = 180            # hip Y must be BELOW this to be considered fallen (pixel value)
STAND_HIP_Y_MIN = 210           # hip Y must be ABOVE this to confirm person has stood up
RESET_COOLDOWN_FRAMES = 30      # frames to wait before allowing re-detection after reset

# Camera
CAMERA_INDEX = 0                # 0 = default webcam

# Serial Communication (STM32 MCU)
SERIAL_PORT = "COM3"            # Windows default, change if needed
BAUD_RATE = 9600

# Ntfy Push Notifications
NTFY_TOPIC = "guardianeye-CHANGEME"   # replace with your random channel name
NTFY_URL = f"https://ntfy.sh/{NTFY_TOPIC}"

# Flask Dashboard
FLASK_PORT = 5000
FLASK_HOST = "0.0.0.0"
