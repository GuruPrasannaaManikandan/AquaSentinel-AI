/**
 * @file main.cpp
 * @brief Isolated Hardware Bring-Up: Physical LED Verification
 * 
 * Target Hardware:
 *   - NodeMCU ESP-32S (38-pin Dev Module, CP2102 USB-UART on COM3)
 *   - GREEN  LED -> GPIO P25 (Pin 25) via 330 ohm series resistor
 *   - YELLOW LED -> GPIO P26 (Pin 26) via 330 ohm series resistor
 *   - RED    LED -> GPIO P27 (Pin 27) via 330 ohm series resistor
 *   - Common Cathodes -> Breadboard GND rail -> ESP32 GND
 *   - 3.3V rail -> ESP32 3V3
 * 
 * Safety & Isolation:
 *   - Zero Wi-Fi / MQTT / Sensor / CV / AIS initialization.
 *   - Zero buzzer or relay actuation.
 *   - Strict digital output configuration, starting LOW.
 *   - 100% isolated from production firmware.
 * 
 * Test Sequence:
 *   1. All LEDs OFF.
 *   2. GREEN ON for 1 second.
 *   3. GREEN OFF.
 *   4. YELLOW ON for 1 second.
 *   5. YELLOW OFF.
 *   6. RED ON for 1 second.
 *   7. RED OFF.
 *   8. All LEDs OFF for 1 second.
 *   9. Repeat continuously.
 */

#include <Arduino.h>

// -----------------------------------------------------------------------------
// Hardware Pin Definitions (Physical NodeMCU ESP-32S P-Labels)
// -----------------------------------------------------------------------------
constexpr int PIN_LED_GREEN  = 25;  // Board label P25
constexpr int PIN_LED_YELLOW = 26;  // Board label P26
constexpr int PIN_LED_RED    = 27;  // Board label P27

// -----------------------------------------------------------------------------
// Timing Constants (Milliseconds)
// -----------------------------------------------------------------------------
constexpr unsigned long DURATION_LED_ON_MS  = 1000;  // 1 second ON
constexpr unsigned long DURATION_ALL_OFF_MS = 1000;  // 1 second all OFF

// -----------------------------------------------------------------------------
// Test Cycle Counter
// -----------------------------------------------------------------------------
static unsigned long testCycle = 0;

void setup() {
    // 1. Initialize hardware serial for real-time diagnostic reporting
    Serial.begin(115200);
    delay(1000); // Allow USB-UART bridge to settle

    Serial.println();
    Serial.println(F("=========================================================="));
    Serial.println(F("   AquaSentinel-AI: Physical Hardware LED Bring-Up"));
    Serial.println(F("=========================================================="));
    Serial.println(F("Board  : NodeMCU ESP-32S (38-pin Dev Module)"));
    Serial.println(F("Port   : COM3 @ 115200 baud"));
    Serial.println(F("Target GPIOs:"));
    Serial.println(F("  - GPIO P25 : GREEN  LED (330 ohm to GND)"));
    Serial.println(F("  - GPIO P26 : YELLOW LED (330 ohm to GND)"));
    Serial.println(F("  - GPIO P27 : RED    LED (330 ohm to GND)"));
    Serial.println(F("Safety : No buzzer, No relay, No sensors, No Wi-Fi"));
    Serial.println(F("==========================================================\n"));

    // 2. Configure P25, P26, P27 as digital outputs and start all LOW
    pinMode(PIN_LED_GREEN, OUTPUT);
    pinMode(PIN_LED_YELLOW, OUTPUT);
    pinMode(PIN_LED_RED, OUTPUT);

    digitalWrite(PIN_LED_GREEN, LOW);
    digitalWrite(PIN_LED_YELLOW, LOW);
    digitalWrite(PIN_LED_RED, LOW);

    Serial.println(F("[INIT] Configured P25, P26, P27 as OUTPUT -> Set all LOW."));
    Serial.println(F("[INIT] Verification sequence starting...\n"));
}

void loop() {
    testCycle++;

    Serial.println(F("----------------------------------------------------------"));
    Serial.print(F(">>> STARTING LED TEST SEQUENCE — CYCLE #"));
    Serial.println(testCycle);
    Serial.println(F("----------------------------------------------------------"));

    // Step 1: All LEDs OFF
    Serial.println(F("[STEP 1] All LEDs OFF"));
    digitalWrite(PIN_LED_GREEN, LOW);
    digitalWrite(PIN_LED_YELLOW, LOW);
    digitalWrite(PIN_LED_RED, LOW);

    // Step 2: GREEN ON for 1 second
    Serial.println(F("[STEP 2] GREEN LED (P25) -> ON  (1 second)"));
    digitalWrite(PIN_LED_GREEN, HIGH);
    delay(DURATION_LED_ON_MS);

    // Step 3: GREEN OFF
    Serial.println(F("[STEP 3] GREEN LED (P25) -> OFF"));
    digitalWrite(PIN_LED_GREEN, LOW);

    // Step 4: YELLOW ON for 1 second
    Serial.println(F("[STEP 4] YELLOW LED (P26) -> ON  (1 second)"));
    digitalWrite(PIN_LED_YELLOW, HIGH);
    delay(DURATION_LED_ON_MS);

    // Step 5: YELLOW OFF
    Serial.println(F("[STEP 5] YELLOW LED (P26) -> OFF"));
    digitalWrite(PIN_LED_YELLOW, LOW);

    // Step 6: RED ON for 1 second
    Serial.println(F("[STEP 6] RED LED (P27) -> ON  (1 second)"));
    digitalWrite(PIN_LED_RED, HIGH);
    delay(DURATION_LED_ON_MS);

    // Step 7: RED OFF
    Serial.println(F("[STEP 7] RED LED (P27) -> OFF"));
    digitalWrite(PIN_LED_RED, LOW);

    // Step 8: All LEDs OFF for 1 second
    Serial.println(F("[STEP 8] All LEDs OFF (1 second pause)"));
    digitalWrite(PIN_LED_GREEN, LOW);
    digitalWrite(PIN_LED_YELLOW, LOW);
    digitalWrite(PIN_LED_RED, LOW);
    delay(DURATION_ALL_OFF_MS);

    // Step 9: Repeat continuously (handled by loop())
    Serial.print(F(">>> CYCLE #"));
    Serial.print(testCycle);
    Serial.println(F(" COMPLETE.\n"));
}
