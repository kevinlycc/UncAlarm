// SPDX-FileCopyrightText: Copyright (C) ARDUINO SRL (http://www.arduino.cc)
// SPDX-License-Identifier: MPL-2.0
// GuardianEye — FaceTime-style frontend logic

const socket = io(`http://${window.location.host}`);
const errorContainer = document.getElementById('error-container');

// ── DOM refs ──
const corners = {
    TL: document.getElementById('cornerTL'),
    TR: document.getElementById('cornerTR'),
    BL: document.getElementById('cornerBL'),
    BR: document.getElementById('cornerBR'),
};
const countdownBar   = document.getElementById('countdownBar');
const countdownMsg   = document.getElementById('countdownMsg');
const countdownNum   = document.getElementById('countdownNum');
const countdownFill  = document.getElementById('countdownFill');
const alertOverlay   = document.getElementById('alertOverlay');
const alertTitle     = document.getElementById('alertTitle');
const alertDesc      = document.getElementById('alertDescription');
const alertTimer     = document.getElementById('alertTimer');
const fallCountBadge = document.getElementById('fallCountBadge');
const logPanel       = document.getElementById('logPanel');
const logBody        = document.getElementById('logBody');
const logToggle      = document.getElementById('logToggle');
const dismissButton  = document.getElementById('dismissButton');

// ── State ──
let fallCount     = 0;
let logEntries    = [];
let logOpen       = false;
let currentStatus = 'safe';
const COUNTDOWN_MAX = 30;

// ── Weighted Temporal Filter ──
const WINDOW_SIZE    = 15;
const FALL_THRESHOLD = 0.60;
const detectionWindow = [];

function pushDetection(isFall, confidence) {
    detectionWindow.push({ isFall, confidence });
    if (detectionWindow.length > WINDOW_SIZE) detectionWindow.shift();

    let weightedFall = 0;
    let totalWeight  = 0;
    detectionWindow.forEach((d, i) => {
        const weight = i + 1;
        totalWeight  += weight;
        if (d.isFall) weightedFall += weight * d.confidence;
    });

    return totalWeight > 0 ? weightedFall / totalWeight : 0;
}

// ── Status config ──
const STATUS = {
    safe: {
        label: 'Not Fallen',
        sub:   'Patient status normal',
        color: '#30d158',
        glow:  '#30d158',
        cls:   'safe',
    },
    alert: {
        label: 'Monitoring',
        sub:   'Unusual movement detected',
        color: '#ff9f0a',
        glow:  '#ff9f0a',
        cls:   'alert',
    },
    fall: {
        label: 'Fallen',
        sub:   'Immediate attention required',
        color: '#ff453a',
        glow:  '#ff453a',
        cls:   'fall',
    },
    emergency: {
        label: 'Emergency',
        sub:   'Escalating to services',
        color: '#ff453a',
        glow:  '#ff453a',
        cls:   'fall',
    },
};

function setStatus(key) {
    const cfg = STATUS[key] || STATUS.safe;
    currentStatus = key;
    const positions = { TL: 'top-left', TR: 'top-right', BL: 'bottom-left', BR: 'bottom-right' };
    Object.entries(corners).forEach(([id, el]) => {
        el.className = `corner ${positions[id]} ${cfg.cls}`;
    });
}

function updateCountdown(seconds) {
    if (seconds === null || seconds <= 0) {
        countdownBar.style.display = 'none';
        return;
    }
    countdownBar.style.display = 'block';

    const pct    = Math.min(100, (seconds / COUNTDOWN_MAX) * 100);
    const urgent = seconds <= 10;

    countdownNum.textContent = `${Math.ceil(seconds)}s`;
    countdownNum.className   = `countdown-num${urgent ? ' urgent' : ''}`;
    countdownFill.style.width = `${pct}%`;
    countdownFill.className   = `countdown-fill${urgent ? ' urgent' : ''}`;
}

function addLog(msg, type) {
    const time = new Date().toLocaleTimeString();
    logEntries.unshift({ msg, type, time });
    renderLog();
}

function renderLog() {
    if (!logEntries.length) {
        logBody.innerHTML = '<div class="log-empty">No events yet</div>';
        return;
    }
    logBody.innerHTML = logEntries.map(e => `
        <div class="log-entry ${e.type}">
            <span class="log-entry-msg">${e.msg}</span>
            <span class="log-entry-time">${e.time}</span>
        </div>
    `).join('');
}

// ── Socket events (mirrors existing main.py events exactly) ──
socket.on('connect', () => {
    if (errorContainer) errorContainer.style.display = 'none';
});

socket.on('disconnect', () => {
    if (errorContainer) {
        errorContainer.textContent = 'Connection to the board lost. Please check the connection.';
        errorContainer.style.display = 'block';
    }
});

socket.on('fall_alert', (state) => {
    switch (state) {
        case 'LOCAL_WARNING_STARTED':
            setStatus('fall');
            showAlert('Fall Detected', 'A fall has been detected. Press dismiss if you are okay.');
            fallCount++;
            fallCountBadge.textContent = `${fallCount} fall${fallCount !== 1 ? 's' : ''} today`;
            fallCountBadge.style.display = 'block';
            addLog('Fall detected', 'fall');
            break;

        case 'FAMILY_NOTIFIED':
            showAlert('Family Notified', 'Timed out. Family has been contacted. Help is on the way.');
            alertTitle.style.color = '#ff9f0a';
            addLog('Family notified', 'fall');
            break;

        case 'EMERGENCY_SERVICES_CALLED':
            showAlert('Emergency Called', 'Emergency services have been contacted.');
            alertTitle.style.color = '#ff453a';
            setStatus('emergency');
            addLog('Emergency escalated', 'fall');
            break;

        case 'ALERT_DISMISSED':
            hideAlert();
            setStatus('safe');
            updateCountdown(null);
            addLog('Alert dismissed', 'clear');
            break;
    }
});

socket.on('alert_status', (statusText) => {
    // extract countdown seconds e.g. "...in 24s"
    const match = statusText.match(/(\d+)s/);
    if (match) {
        const secs = parseInt(match[1]);
        alertTimer.textContent = secs;
        updateCountdown(secs);
    }
    if (statusText.includes('Activity detected') || statusText.includes('stood')) {
        setStatus('alert');
        countdownMsg.textContent = 'Standing detected — extended countdown';
    }
});

socket.on('classifications', (message) => {
    try {
        const detections = JSON.parse(message);
        const fallDet   = detections.find(d => d.content?.toLowerCase() === 'fall');
        const personDet = detections.find(d => d.content?.toLowerCase() === 'person');

        const isFall = !!fallDet;
        const conf   = fallDet?.confidence ?? personDet?.confidence ?? 0.5;

        const score = pushDetection(isFall, conf);
        const weightedFall = score >= FALL_THRESHOLD;

        if (currentStatus !== 'emergency') {
            if (weightedFall)        setStatus('fall');
            else if (personDet)      setStatus('safe');
        }
    } catch (e) { }
});

// ── UI interactions ──
logToggle.addEventListener('click', () => {
    logOpen = !logOpen;
    logPanel.classList.toggle('open', logOpen);
    logToggle.textContent = logOpen ? 'Hide Log' : 'Event Log';
});

dismissButton.addEventListener('click', () => {
    socket.emit('dismiss_alert', {});
    hideAlert();
    setStatus('safe');
    updateCountdown(null);
    addLog('Alert dismissed by user', 'clear');
});

function showAlert(title, desc) {
    alertOverlay.style.display = 'flex';
    alertOverlay.classList.add('active');
    alertTitle.textContent = title;
    alertDesc.textContent  = desc;
    alertTitle.style.color = '#ff453a';
}

function hideAlert() {
    alertOverlay.style.display = 'none';
    alertOverlay.classList.remove('active');
}

// ── Servo Control ──
const PAN_MIN = 20, PAN_MAX = 160, PAN_CENTER = 90;
const TILT_MIN = 40, TILT_MAX = 130, TILT_CENTER = 80;
const SERVO_STEP = 12; // degrees per button press

let currentPan  = PAN_CENTER;
let currentTilt = TILT_CENTER;

function sendServoMove() {
    socket.emit('servo_move', { pan: currentPan, tilt: currentTilt });
}

function setupServoPad() {
    const actions = {
        btnLeft:   () => { currentPan  = Math.max(PAN_MIN,  currentPan  - SERVO_STEP); sendServoMove(); },
        btnRight:  () => { currentPan  = Math.min(PAN_MAX,  currentPan  + SERVO_STEP); sendServoMove(); },
        btnUp:     () => { currentTilt = Math.min(TILT_MAX, currentTilt + SERVO_STEP); sendServoMove(); },
        btnDown:   () => { currentTilt = Math.max(TILT_MIN, currentTilt - SERVO_STEP); sendServoMove(); },
        btnCenter: () => { currentPan = PAN_CENTER; currentTilt = TILT_CENTER; sendServoMove(); },
    };

    Object.entries(actions).forEach(([id, fn]) => {
        const btn = document.getElementById(id);
        if (!btn) return;

        // Click
        btn.addEventListener('click', fn);

        // Hold to repeat
        let holdInterval = null;
        btn.addEventListener('mousedown', () => {
            btn.classList.add('pressed');
            holdInterval = setInterval(fn, 120);
        });
        btn.addEventListener('touchstart', (e) => {
            e.preventDefault();
            btn.classList.add('pressed');
            fn();
            holdInterval = setInterval(fn, 120);
        });
        const stopHold = () => {
            btn.classList.remove('pressed');
            clearInterval(holdInterval);
        };
        btn.addEventListener('mouseup',   stopHold);
        btn.addEventListener('mouseleave', stopHold);
        btn.addEventListener('touchend',  stopHold);
    });

    // Keyboard arrow keys
    document.addEventListener('keydown', (e) => {
        switch(e.key) {
            case 'ArrowLeft':  actions.btnLeft();   e.preventDefault(); break;
            case 'ArrowRight': actions.btnRight();  e.preventDefault(); break;
            case 'ArrowUp':    actions.btnUp();     e.preventDefault(); break;
            case 'ArrowDown':  actions.btnDown();   e.preventDefault(); break;
            case ' ':          actions.btnCenter(); e.preventDefault(); break;
        }
    });
}

setupServoPad();

socket.on('hardware_cmd', (cmd) => {
    // Python can't use pyserial, so the QRB2210 forwards
    // hardware commands back through the socket to the browser,
    // which echoes them — the sketch reads via Serial on STM32 side
    console.log('[HW CMD]', cmd);
});


setStatus('safe');
renderLog();