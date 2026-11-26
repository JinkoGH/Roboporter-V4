#include <Servo.h>
#include <stdlib.h>
#include <string.h>

// --- Pin Definitions (Update if Nurul/Cenk specify alternate PWM pins) ---
constexpr uint8_t LEFT_ESC_PIN = 9;
constexpr uint8_t RIGHT_ESC_PIN = 10;

// --- Mtronics Viper Marine 15A ESC PWM Bounds (microseconds) ---
constexpr int PWM_MIN_US = 1000;      // Full reverse
constexpr int PWM_NEUTRAL_US = 1500;  // Neutral / Stop / Arming pulse
constexpr int PWM_MAX_US = 2000;      // Full forward

// --- Safety & Timing Constants ---
constexpr unsigned long SERIAL_BAUD = 115200;
constexpr unsigned long FAILSAFE_TIMEOUT_MS = 250;  // <250 ms watchdog requirement
constexpr unsigned long TELEMETRY_PERIOD_MS = 40;   // 25 Hz telemetry output
constexpr unsigned long ESC_ARM_DELAY_MS = 2500;    // 2.5 s neutral pulse to arm ESC

Servo leftEsc;
Servo rightEsc;

// Serial frame buffer for "<L_speed,R_speed\n>"
constexpr size_t RX_BUF_SIZE = 48;
char rxBuffer[RX_BUF_SIZE];
size_t rxIndex = 0;
bool inFrame = false;

unsigned long lastValidCmdMs = 0;
unsigned long lastTelemetryMs = 0;
bool failsafeEngaged = true;

// Placeholder encoder counters for Task 4.1 (replaced by ISRs in Task 4.2)
volatile long leftTicks = 0;
volatile long rightTicks = 0;

// constexpr uint8_t LEFT_ENC_A = 2;
// constexpr uint8_t LEFT_ENC_B = 3;
// constexpr uint8_t RIGHT_ENC_A = 18;
// constexpr uint8_t RIGHT_ENC_B = 19;

// // 4x Quadrature state lookup table: index = (prevState << 2) | currState
// const int8_t QEM_TABLE[16] = {
//    0, -1,  1,  0,
//    1,  0,  0, -1,
//   -1,  0,  0,  1,
//    0,  1, -1,  0
// };

// volatile uint8_t prevLeftState = 0;
// volatile uint8_t prevRightState = 0;

// void updateLeftEncoder() {
//   uint8_t curr = (digitalRead(LEFT_ENC_A) << 1) | digitalRead(LEFT_ENC_B);
//   leftTicks += QEM_TABLE[(prevLeftState << 2) | curr];
//   prevLeftState = curr;
// }

// void updateRightEncoder() {
//   uint8_t curr = (digitalRead(RIGHT_ENC_A) << 1) | digitalRead(RIGHT_ENC_B);
//   // Negate (-=) if right motor is physically mirrored on the chassis
//   rightTicks += QEM_TABLE[(prevRightState << 2) | curr];
//   prevRightState = curr;
// }

float clampFloat(float val, float low, float high) {
  if (val < low) return low;
  if (val > high) return high;
  return val;
}

int speedToMicroseconds(float normSpeed) {
  float clamped = clampFloat(normSpeed, -1.0f, 1.0f);
  // Deadband around 0.0 to prevent ESC crawl
  if (clamped > -0.01f && clamped < 0.01f) {
    return PWM_NEUTRAL_US;
  }
  return PWM_NEUTRAL_US + static_cast<int>(clamped * 500.0f);
}

void applyNeutralFailsafe() {
  leftEsc.writeMicroseconds(PWM_NEUTRAL_US);
  rightEsc.writeMicroseconds(PWM_NEUTRAL_US);
}

void parsePacket(const char* packet) {
  // Expected format: "L_speed,R_speed" (e.g., "0.500,-0.250")
  char* commaPtr = strchr(packet, ',');
  if (commaPtr == nullptr) {
    return;
  }

  float leftCmd = static_cast<float>(strtod(packet, nullptr));
  float rightCmd = static_cast<float>(strtod(commaPtr + 1, nullptr));

  int leftUs = speedToMicroseconds(leftCmd);
  int rightUs = speedToMicroseconds(rightCmd);

  leftEsc.writeMicroseconds(leftUs);
  rightEsc.writeMicroseconds(rightUs);

  lastValidCmdMs = millis();
  failsafeEngaged = false;
  digitalWrite(LED_BUILTIN, HIGH);
}

void readSerialStream() {
  while (Serial.available() > 0) {
    char c = static_cast<char>(Serial.read());
    if (c == '<') {
      inFrame = true;
      rxIndex = 0;
    } else if (c == '>' && inFrame) {
      rxBuffer[rxIndex] = '\0';
      parsePacket(rxBuffer);
      inFrame = false;
      rxIndex = 0;
    } else if (inFrame) {
      if (rxIndex < RX_BUF_SIZE - 1) {
        rxBuffer[rxIndex++] = c;
      } else {
        // Buffer overflow protection: discard malformed frame
        inFrame = false;
        rxIndex = 0;
      }
    }
  }
}

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);

  Serial.begin(SERIAL_BAUD);

  leftEsc.attach(LEFT_ESC_PIN, PWM_MIN_US, PWM_MAX_US);
  rightEsc.attach(RIGHT_ESC_PIN, PWM_MIN_US, PWM_MAX_US);

  // Arm Mtronics ESCs by holding neutral 1500 us pulse on boot
  applyNeutralFailsafe();
  delay(ESC_ARM_DELAY_MS);

  lastValidCmdMs = millis();
  lastTelemetryMs = millis();
}

void loop() {
  readSerialStream();

  unsigned long now = millis();

  // Microcontroller-level <250 ms serial timeout failsafe
  if ((now - lastValidCmdMs) > FAILSAFE_TIMEOUT_MS) {
    if (!failsafeEngaged) {
      applyNeutralFailsafe();
      failsafeEngaged = true;
      digitalWrite(LED_BUILTIN, LOW);
    }
  }

  // Stream structured telemetry back to arduino_bridge_node at 25 Hz
  if ((now - lastTelemetryMs) >= TELEMETRY_PERIOD_MS) {
    lastTelemetryMs = now;
    noInterrupts();
    long lCopy = leftTicks;
    long rCopy = rightTicks;
    interrupts();

    Serial.print('<');
    Serial.print(lCopy);
    Serial.print(',');
    Serial.print(rCopy);
    Serial.println(",0.00>");
  }
}