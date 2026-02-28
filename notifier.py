import requests
from config import NTFY_URL

def send_fall_alert():
    try:
        response = requests.post(
            NTFY_URL,
            data="FALL DETECTED! Please check on your family member immediately.".encode("utf-8"),
            headers={
                "Title": "GuardianEye Alert",
                "Priority": "urgent",
                "Tags": "warning,sos"
            },
            timeout=5
        )
        if response.status_code == 200:
            print("[GuardianEye] Push notification sent successfully.")
        else:
            print(f"[GuardianEye] Notification failed. Status: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("[GuardianEye] No internet connection - notification not sent. Local alerts still active.")
    except requests.exceptions.Timeout:
        print("[GuardianEye] Notification timed out. Local alerts still active.")
    except Exception as e:
        print(f"[GuardianEye] Notification error: {e}")

def send_clear_alert():
    try:
        requests.post(
            NTFY_URL,
            data="GuardianEye: Person is upright. Alert resolved.".encode("utf-8"),
            headers={
                "Title": "GuardianEye - All Clear",
                "Priority": "default",
                "Tags": "white_check_mark"
            },
            timeout=5
        )
        print("[GuardianEye] Clear notification sent.")
    except Exception as e:
        print(f"[GuardianEye] Clear notification error: {e}")