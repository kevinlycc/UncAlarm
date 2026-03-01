// UnderWatch - MCU Sketch for Arduino UNO Q (STM32U585)
// Controls pan/tilt servos, button input, buzzer alerts, and LED status
// Communicates with Linux MPU via Arduino Bridge

#include "Arduino_RouterBridge.h"
#include <Servo.h>

// ============== PIN DEFINITIONS ==============
#define PAN_SERVO_PIN 9
#define TILT_SERVO_PIN 10
#define BUTTON_PIN 2          // Push button (internal pull-up)
#define BUZZER_PIN 3          // Piezo buzzer

// ============== SERVO CONFIG ==============
Servo panServo;
Servo tiltServo;
int currentPan = 90;
int currentTilt = 90;
const float SMOOTHING = 0.15;  // Lower = smoother but slower

// ============== STATUS ==============
enum Status { CLEAR, ALERT, FALL, COUNTDOWN, SOS };
Status currentStatus = CLEAR;

// ============== BUTTON ==============
bool lastButtonState = HIGH;
unsigned long lastDebounceTime = 0;
const unsigned long DEBOUNCE_DELAY = 50;

// ============== COUNTDOWN ==============
bool countdownActive = false;
unsigned long lastBeepTime = 0;
int beepInterval = 1000;

// ============== SETUP ==============
void setup() {
    Serial.begin(115200);
    
    // Servos
    panServo.attach(PAN_SERVO_PIN);
    tiltServo.attach(TILT_SERVO_PIN);
    panServo.write(90);
    tiltServo.write(90);
    
    // Button (internal pull-up)
    pinMode(BUTTON_PIN, INPUT_PULLUP);
    
    // Buzzer
    pinMode(BUZZER_PIN, OUTPUT);
    digitalWrite(BUZZER_PIN, LOW);
    
    // LED
    pinMode(LED_BUILTIN, OUTPUT);
    
    // Bridge communication with MPU
    Bridge.begin();
    
    // Register functions callable from Python
    Bridge.provide("set_servo_position", set_servo_position);
    Bridge.provide("set_status", set_status);
    Bridge.provide("center_servos", center_servos);
    Bridge.provide("start_countdown", start_countdown);
    Bridge.provide("stop_countdown", stop_countdown);
    Bridge.provide("trigger_sos", trigger_sos);
    Bridge.provide("beep", beep);
    
    // Startup beep
    beep(1000, 100);
    delay(100);
    beep(1500, 100);
    
    Serial.println("[MCU] UnderWatch ready");
}

// ============== MAIN LOOP ==============
void loop() {
    handleButton();
    
    if (countdownActive) {
        handleCountdownBeep();
    }
    
    updateLED();
    
    delay(20);
}

// ============== SERVO CONTROL ==============
// Called by Python: Bridge.call("set_servo_position", pan, tilt)
void set_servo_position(int pan_angle, int tilt_angle) {
    pan_angle = constrain(pan_angle, 0, 180);
    tilt_angle = constrain(tilt_angle, 0, 180);
    
    // Smooth movement
    currentPan = currentPan + (pan_angle - currentPan) * SMOOTHING;
    currentTilt = currentTilt + (tilt_angle - currentTilt) * SMOOTHING;
    
    panServo.write((int)currentPan);
    tiltServo.write((int)currentTilt);
}

// Called by Python: Bridge.call("center_servos")
void center_servos() {
    currentPan = 90;
    currentTilt = 90;
    panServo.write(90);
    tiltServo.write(90);
}

// ============== STATUS CONTROL ==============
// Called by Python: Bridge.call("set_status", status)
// status: 0=CLEAR, 1=ALERT, 2=FALL, 3=COUNTDOWN, 4=SOS
void set_status(int status) {
    currentStatus = (Status)status;
}

// ============== COUNTDOWN ==============
// Called by Python: Bridge.call("start_countdown")
void start_countdown() {
    countdownActive = true;
    beepInterval = 1000;
    lastBeepTime = millis();
}

// Called by Python: Bridge.call("stop_countdown")
void stop_countdown() {
    countdownActive = false;
    noTone(BUZZER_PIN);
}

void handleCountdownBeep() {
    unsigned long now = millis();
    
    if (now - lastBeepTime >= beepInterval) {
        tone(BUZZER_PIN, 1500, 100);
        lastBeepTime = now;
        
        // Speed up over time (min 200ms)
        if (beepInterval > 200) {
            beepInterval -= 50;
        }
    }
}

// ============== SOS ==============
// Called by Python: Bridge.call("trigger_sos")
void trigger_sos() {
    // Loud alarm pattern
    for (int i = 0; i < 5; i++) {
        tone(BUZZER_PIN, 2000, 200);
        delay(300);
    }
}

// ============== BUZZER ==============
// Called by Python: Bridge.call("beep", frequency, duration)
void beep(int frequency, int duration) {
    tone(BUZZER_PIN, frequency, duration);
}

// ============== BUTTON ==============
void handleButton() {
    bool reading = digitalRead(BUTTON_PIN);
    
    if (reading != lastButtonState) {
        lastDebounceTime = millis();
    }
    
    if ((millis() - lastDebounceTime) > DEBOUNCE_DELAY) {
        // Button released (LOW -> HIGH with pull-up)
        if (lastButtonState == LOW && reading == HIGH) {
            Serial.println("[MCU] Button pressed - dismissing");
            Bridge.call("button_dismiss");
            
            // Confirmation beep
            beep(2000, 100);
            delay(100);
            beep(2500, 150);
        }
    }
    
    lastButtonState = reading;
}

// ============== LED STATUS ==============
void updateLED() {
    switch (currentStatus) {
        case CLEAR:
            digitalWrite(LED_BUILTIN, HIGH);  // Solid on
            break;
        case ALERT:
            digitalWrite(LED_BUILTIN, (millis() / 500) % 2);  // Slow blink
            break;
        case FALL:
            digitalWrite(LED_BUILTIN, (millis() / 250) % 2);  // Medium blink
            break;
        case COUNTDOWN:
            digitalWrite(LED_BUILTIN, (millis() / 100) % 2);  // Fast blink
            break;
        case SOS:
            digitalWrite(LED_BUILTIN, (millis() / 50) % 2);   // Rapid flash
            break;
    }
}
