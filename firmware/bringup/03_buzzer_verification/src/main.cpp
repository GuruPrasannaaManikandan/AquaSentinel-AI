/**
 * @file main.cpp
 * @brief Isolated Hardware Bring-Up: MB12A05 2-Pin Buzzer Verification
 * 
 * Target Hardware:
 *   - Main Board : NodeMCU ESP-32S (38-pin Dev Module, CP2102 USB-UART on COM3)
 *   - Buzzer     : MB12A05 2-pin buzzer
 *   - Wiring:
 *       Buzzer (+) (Long pin / marked '+')  -> ESP32 GPIO P14 (Pin 12 on left header)
 *       Buzzer (-) (Short pin)               -> Common GND Rail -> ESP32 GND
 * 
 * Safety & Isolation:
 *   - ZERO dependencies on Wi-Fi, MQTT, sensors, FSM, AIS, or CV subsystems.
 *   - ZERO modifications to production firmware or permanent configuration files.
 *   - Configures GPIO 14 as OUTPUT, starting LOW.
 * 
 * Test Pattern:
 *   - Pulse 1: Short Beep (150 ms ON, 150 ms OFF)
 *   - Pulse 2: Short Beep (150 ms ON, 150 ms OFF)
 *   - Pulse 3: Long Beep  (500 ms ON, 500 ms OFF)
 *   - Silent Pause: 2000 ms
 *   - Repeat continuously
 */

#include <Arduino.h>

// -----------------------------------------------------------------------------
// Hardware Pin Definition (NodeMCU ESP-32S board label P14)
// -----------------------------------------------------------------------------
constexpr int PIN_BUZZER = 14;  // GPIO 14 (Physical board label P14)

// -----------------------------------------------------------------------------
// Timing Constants (Milliseconds)
// -----------------------------------------------------------------------------
constexpr unsigned long DURATION_SHORT_BEEP_MS = 150;
constexpr unsigned long DURATION_SHORT_GAP_MS  = 150;
constexpr unsigned long DURATION_LONG_BEEP_MS  = 500;
constexpr unsigned long DURATION_LONG_GAP_MS   = 500;
constexpr unsigned long DURATION_CYCLE_REST_MS = 2000;

// -----------------------------------------------------------------------------
// Cycle Tracking
// -----------------------------------------------------------------------------
static unsigned long cycleCount = 0;

void setup() {
    // 1. Initialize hardware serial at 115200 baud
    Serial.begin(115200);
    delay(1000); // Allow USB-UART bridge to settle

    Serial.println();
    Serial.println(F("=========================================================="));
    Serial.println(F("   AquaSentinel-AI: Isolated Buzzer Bring-Up"));
    Serial.println(F("   Device: MB12A05 2-Pin Buzzer on GPIO P14"));
    Serial.println(F("=========================================================="));
    Serial.println(F("Target MCU : NodeMCU ESP-32S (38-pin Dev Module)"));
    Serial.println(F("Baud Rate  : 115200 baud on COM3"));
    Serial.println(F("Pin Config : GPIO P14 -> OUTPUT (Default LOW)"));
    Serial.println(F("Wiring Check:"));
    Serial.println(F("  - Buzzer (+) -> ESP32 GPIO P14"));
    Serial.println(F("  - Buzzer (-) -> Breadboard Common GND -> ESP32 GND"));
    Serial.println(F("==========================================================\n"));

    // 2. Configure GPIO 14 as digital output and start LOW
    pinMode(PIN_BUZZER, OUTPUT);
    digitalWrite(PIN_BUZZER, LOW);

    Serial.println(F("[INIT] GPIO P14 configured as OUTPUT. Initial state: LOW (OFF)."));
    Serial.println(F("[INIT] NOTE: Serial messages confirm GPIO pin toggling."));
    Serial.println(F("[INIT] Physical audible sound MUST be confirmed by hearing.\n"));
}

void loop() {
    cycleCount++;

    Serial.println(F("----------------------------------------------------------"));
    Serial.print(F(">>> STARTING BUZZER TEST CYCLE #"));
    Serial.println(cycleCount);
    Serial.println(F("----------------------------------------------------------"));

    // Pulse 1: Short Beep
    Serial.println(F("[STEP 1/3] Chirp 1: GPIO 14 -> HIGH (150ms)"));
    digitalWrite(PIN_BUZZER, HIGH);
    delay(DURATION_SHORT_BEEP_MS);

    Serial.println(F("           Chirp 1: GPIO 14 -> LOW  (150ms gap)"));
    digitalWrite(PIN_BUZZER, LOW);
    delay(DURATION_SHORT_GAP_MS);

    // Pulse 2: Short Beep
    Serial.println(F("[STEP 2/3] Chirp 2: GPIO 14 -> HIGH (150ms)"));
    digitalWrite(PIN_BUZZER, HIGH);
    delay(DURATION_SHORT_BEEP_MS);

    Serial.println(F("           Chirp 2: GPIO 14 -> LOW  (150ms gap)"));
    digitalWrite(PIN_BUZZER, LOW);
    delay(DURATION_SHORT_GAP_MS);

    // Pulse 3: Long Beep
    Serial.println(F("[STEP 3/3] Alert Tone: GPIO 14 -> HIGH (500ms)"));
    digitalWrite(PIN_BUZZER, HIGH);
    delay(DURATION_LONG_BEEP_MS);

    Serial.println(F("           Alert Tone: GPIO 14 -> LOW  (End of pulse)"));
    digitalWrite(PIN_BUZZER, LOW);
    delay(DURATION_LONG_GAP_MS);

    // Rest interval
    Serial.print(F(">>> CYCLE #"));
    Serial.print(cycleCount);
    Serial.print(F(" FINISHED. Silent pause for "));
    Serial.print(DURATION_CYCLE_REST_MS / 1000);
    Serial.println(F("s before next pattern...\n"));

    delay(DURATION_CYCLE_REST_MS);
}
