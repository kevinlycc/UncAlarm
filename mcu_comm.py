import serial
import serial.tools.list_ports
from config import SERIAL_PORT, BAUD_RATE

_ser = None

def connect():
    global _ser
    try:
        _ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print(f"[MCU] Connected to Arduino on {SERIAL_PORT}")
        return True
    except Exception as e:
        print(f"[MCU] Could not connect to Arduino: {e}")
        print("[MCU] Running without hardware alerts.")
        return False

def send_command(command):
    global _ser
    if _ser and _ser.is_open:
        try:
            _ser.write(f"{command}\n".encode())
        except Exception as e:
            print(f"[MCU] Send error: {e}")

def disconnect():
    global _ser
    if _ser and _ser.is_open:
        _ser.close()
        print("[MCU] Disconnected from Arduino.")