import cv2
import base64
from datetime import datetime
from flask import Flask
from flask_socketio import SocketIO, emit
from flask_cors import CORS

app = Flask(__name__)
app.config['SECRET_KEY'] = 'guardianeye-secret'
CORS(app, origins="*")
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

state = {
    'status': 'CLEAR',
    'alert_log': [],
    'frame_b64': None,
    'countdown': None,
    'nose_pos': None,
}

def emit_status(status):
    state['status'] = status
    if status in ('FALL', 'EMERGENCY'):
        entry = {
            'time': datetime.now().strftime('%H:%M:%S'),
            'message': 'Fall detected' if status == 'FALL' else 'Emergency escalated',
            'type': 'fall'
        }
        state['alert_log'].insert(0, entry)
        if len(state['alert_log']) > 50:
            state['alert_log'].pop()
    elif status == 'CLEAR' and len(state['alert_log']) > 0 and state['alert_log'][0]['type'] == 'fall':
        entry = {
            'time': datetime.now().strftime('%H:%M:%S'),
            'message': 'Alert resolved',
            'type': 'clear'
        }
        state['alert_log'].insert(0, entry)
    socketio.emit('status_update', {
        'status': status,
        'alert_log': state['alert_log'][:20]
    })

def emit_countdown(seconds):
    state['countdown'] = seconds
    socketio.emit('countdown', {'seconds': seconds})

def emit_keypoint(nose_x_pct, nose_y_pct):
    state['nose_pos'] = {'x': nose_x_pct, 'y': nose_y_pct}
    socketio.emit('keypoint', {'x': nose_x_pct, 'y': nose_y_pct})

def emit_frame(frame):
    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 60])
    b64 = base64.b64encode(buffer).decode('utf-8')
    state['frame_b64'] = b64
    socketio.emit('frame', {'image': b64})

@socketio.on('connect')
def on_connect():
    emit('status_update', {'status': state['status'], 'alert_log': state['alert_log'][:20]})
    emit('countdown', {'seconds': state['countdown']})
    if state['frame_b64']:
        emit('frame', {'image': state['frame_b64']})

def run_server():
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)

if __name__ == '__main__':
    run_server()
