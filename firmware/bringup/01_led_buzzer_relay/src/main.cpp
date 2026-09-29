/**
 * @file main.cpp
 * @brief Stage 01 Isolated Hardware Bring-Up: Discrete Actuators
 * 
 * Target Hardware:
 *   - ESP32-WROOM-32 (38-pin Dev Module, CP2102 USB-UART on COM3)
 *   - Green LED (GPIO 19)
 *   - Yellow LED (GPIO 21)
 *   - Red LED (GPIO 22)
 *   - 5V Buzzer (GPIO 23)
 *   - 5V Relay Module (GPIO 27)
 * 
 * Safety & Isolation Rules:
 *   - ZERO dependencies on Wi-Fi, MQTT, sensors, FSM, AIS, or CV subsystems.
 *   - ZERO modifications to existing production firmware or frozen Python code.
 *   - Relay operates in DRY-CONTACT mode only (NO AC mains or water pumps connected).
 *   - All LEDs MUST have current-limiting resistors (220 ohm to 330 ohm).
 */

#include <Arduino.h>

// -----------------------------------------------------------------------------
// Authoritative Pin Definitions (matches PinConfig.h & device_config.json)
// -----------------------------------------------------------------------------
constexpr int PIN_LED_GREEN  = 19;
constexpr int PIN_LED_YELLOW = 21;
constexpr int PIN_LED_RED    = 22;
constexpr int PIN_BUZZER     = 23;
constexpr int PIN_RELAY      = 27;

// -----------------------------------------------------------------------------
// Timing Constants (Milliseconds)
// -----------------------------------------------------------------------------
constexpr unsigned long DELAY_LED_ON_MS       = 1200;
constexpr unsigned long DELAY_INTER_STEP_MS   = 600;
constexpr unsigned long DELAY_BUZZER_PULSE_MS = 150;
constexpr unsigned long DELAY_BUZZER_GAP_MS   = 120;
constexpr unsigned long DELAY_RELAY_HOLD_MS   = 1500;
constexpr unsigned long DELAY_CYCLE_PAUSE_MS  = 3000;

// -----------------------------------------------------------------------------
// Test Tracking
// -----------------------------------------------------------------------------
static unsigned long cycleCount = 0;

/**
 * @brief Safe default initialization for all actuator GPIO pins.
 * 
 * All pins are configured as OUTPUT.
 * LEDs and Buzzer default to LOW (OFF).
 * Relay defaults to DE-ENERGIZED state.
 */
void initActuatorGPIOs() {
    Serial.println(F("[INIT] Configuring Actuator GPIOs as OUTPUT..."));

    // LEDs
    pinMode(PIN_LED_GREEN, OUTPUT);
    pinMode(PIN_LED_YELLOW, OUTPUT);
    pinMode(PIN_LED_RED, OUTPUT);
    digitalWrite(PIN_LED_GREEN, LOW);
    digitalWrite(PIN_LED_YELLOW, LOW);
    digitalWrite(PIN_LED_RED, LOW);

    // Buzzer
    pinMode(PIN_BUZZER, OUTPUT);
    digitalWrite(PIN_BUZZER, LOW);

    // Relay (Standard relay modules: LOW = Energized / HIGH = Released, or vice-versa)
    // We set LOW initially and test both polarities explicitly.
    pinMode(PIN_RELAY, OUTPUT);
    digitalWrite(PIN_RELAY, LOW);

    Serial.println(F("[INIT] GPIO 19 (Green LED)   -> OUTPUT (LOW)"));
    Serial.println(F("[INIT] GPIO 21 (Yellow LED)  -> OUTPUT (LOW)"));
    Serial.println(F("[INIT] GPIO 22 (Red LED)     -> OUTPUT (LOW)"));
    Serial.println(F("[INIT] GPIO 23 (Buzzer)      -> OUTPUT (LOW)"));
    Serial.println(F("[INIT] GPIO 27 (5V Relay)    -> OUTPUT (LOW)"));
    Serial.println(F("[INIT] All outputs initialized in safe resting states.\n"));
}

/**
 * @brief Test Green LED (Normal/Healthy Indicator)
 */
void testGreenLED() {
    Serial.println(F("  [STEP 1/6] Testing GREEN LED (GPIO 19)..."));
    Serial.println(F("             -> State: HIGH (ON)"));
    digitalWrite(PIN_LED_GREEN, HIGH);
    delay(DELAY_LED_ON_MS);

    Serial.println(F("             -> State: LOW  (OFF)"));
    digitalWrite(PIN_LED_GREEN, LOW);
    delay(DELAY_INTER_STEP_MS);
}

/**
 * @brief Test Yellow LED (Warning/Elevated Risk Indicator)
 */
void testYellowLED() {
    Serial.println(F("  [STEP 2/6] Testing YELLOW LED (GPIO 21)..."));
    Serial.println(F("             -> State: HIGH (ON)"));
    digitalWrite(PIN_LED_YELLOW, HIGH);
    delay(DELAY_LED_ON_MS);

    Serial.println(F("             -> State: LOW  (OFF)"));
    digitalWrite(PIN_LED_YELLOW, LOW);
    delay(DELAY_INTER_STEP_MS);
}

/**
 * @brief Test Red LED (Critical/Hazard Alert Indicator)
 */
void testRedLED() {
    Serial.println(F("  [STEP 3/6] Testing RED LED (GPIO 22)..."));
    Serial.println(F("             -> State: HIGH (ON)"));
    digitalWrite(PIN_LED_RED, HIGH);
    delay(DELAY_LED_ON_MS);

    Serial.println(F("             -> State: LOW  (OFF)"));
    digitalWrite(PIN_LED_RED, LOW);
    delay(DELAY_INTER_STEP_MS);
}

/**
 * @brief Test Buzzer (Audible Alarm Indicator)
 * Generates two distinct, brief pulses to verify acoustic transducer function.
 */
void testBuzzer() {
    Serial.println(F("  [STEP 4/6] Testing BUZZER (GPIO 23)..."));

    // Pulse 1
    Serial.println(F("             -> Chirp 1 (HIGH)"));
    digitalWrite(PIN_BUZZER, HIGH);
    delay(DELAY_BUZZER_PULSE_MS);
    digitalWrite(PIN_BUZZER, LOW);
    delay(DELAY_BUZZER_GAP_MS);

    // Pulse 2
    Serial.println(F("             -> Chirp 2 (HIGH)"));
    digitalWrite(PIN_BUZZER, HIGH);
    delay(DELAY_BUZZER_PULSE_MS);
    digitalWrite(PIN_BUZZER, LOW);
    delay(DELAY_INTER_STEP_MS);
}

/**
 * @brief Test 5V Relay Module (Actuator Control Circuit)
 * 
 * Note: Most optocoupled relay breakout boards are ACTIVE-LOW (IN=LOW energizes coil).
 * Some are ACTIVE-HIGH or selectable via jumper. This test transitions between both
 * logic states so you can verify the mechanical click and onboard indicator LED.
 */
void testRelay() {
    Serial.println(F("  [STEP 5/6] Testing 5V RELAY (GPIO 27)..."));
    
    // State 1: HIGH
    Serial.println(F("             -> Driving GPIO 27 = HIGH (Observe relay click/LED)"));
    digitalWrite(PIN_RELAY, HIGH);
    delay(DELAY_RELAY_HOLD_MS);

    // State 2: LOW
    Serial.println(F("             -> Driving GPIO 27 = LOW  (Observe relay click/LED)"));
    digitalWrite(PIN_RELAY, LOW);
    delay(DELAY_RELAY_HOLD_MS);

    delay(DELAY_INTER_STEP_MS);
}

/**
 * @brief Cascade / Traffic Light Sequence Test
 * Tests simultaneous pin driving and rapid transitions.
 */
void testLEDCascade() {
    Serial.println(F("  [STEP 6/6] Testing LED CASCADE / STATUS SEQUENCE..."));

    // Sequential illumination
    Serial.println(F("             -> Green ON"));
    digitalWrite(PIN_LED_GREEN, HIGH);
    delay(300);

    Serial.println(F("             -> Yellow ON"));
    digitalWrite(PIN_LED_YELLOW, HIGH);
    delay(300);

    Serial.println(F("             -> Red ON"));
    digitalWrite(PIN_LED_RED, HIGH);
    delay(600);

    // All off
    Serial.println(F("             -> All LEDs OFF"));
    digitalWrite(PIN_LED_GREEN, LOW);
    digitalWrite(PIN_LED_YELLOW, LOW);
    digitalWrite(PIN_LED_RED, LOW);
    delay(DELAY_INTER_STEP_MS);
}

// -----------------------------------------------------------------------------
// Arduino Entry Points
// -----------------------------------------------------------------------------
void setup() {
    // Initialize hardware serial
    Serial.begin(115200);
    delay(1000); // Allow CP2102 USB-UART bridge to stabilize

    Serial.println();
    Serial.println(F("=========================================================="));
    Serial.println(F("   AquaSentinel-AI: Physical Hardware Bring-Up"));
    Serial.println(F("   Stage 01: Discrete Actuators (LEDs, Buzzer, Relay)"));
    Serial.println(F("=========================================================="));
    Serial.println(F("Target MCU : ESP32-WROOM-32 (CP2102 USB-UART)"));
    Serial.println(F("Baud Rate  : 115200"));
    Serial.println(F("Assigned GPIOs:"));
    Serial.println(F("  - GPIO 19 : Status Green LED"));
    Serial.println(F("  - GPIO 21 : Warning Yellow LED"));
    Serial.println(F("  - GPIO 22 : Critical Red LED"));
    Serial.println(F("  - GPIO 23 : Audio Alarm Buzzer"));
    Serial.println(F("  - GPIO 27 : 5V Optocoupled Relay (Dry Contact)"));
    Serial.println(F("==========================================================\n"));

    initActuatorGPIOs();
}

void loop() {
    cycleCount++;

    Serial.println(F("----------------------------------------------------------"));
    Serial.print(F(">>> STARTING ACTUATOR TEST CYCLE #"));
    Serial.println(cycleCount);
    Serial.println(F("----------------------------------------------------------"));

    testGreenLED();
    testYellowLED();
    testRedLED();
    testBuzzer();
    testRelay();
    testLEDCascade();

    Serial.print(F(">>> COMPLETED TEST CYCLE #"));
    Serial.print(cycleCount);
    Serial.print(F(". Pausing "));
    Serial.print(DELAY_CYCLE_PAUSE_MS / 1000);
    Serial.println(F("s before next cycle...\n"));

    delay(DELAY_CYCLE_PAUSE_MS);
}
