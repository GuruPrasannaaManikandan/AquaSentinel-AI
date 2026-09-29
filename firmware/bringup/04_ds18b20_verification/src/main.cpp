/**
 * @file main.cpp
 * @brief Isolated Hardware Bring-Up: DS18B20 Waterproof Temperature Sensor Verification
 * 
 * Target Hardware:
 *   - Main Board : NodeMCU ESP-32S (38-pin Dev Module, CP2102 on COM3)
 *   - Sensor     : DS18B20 Waterproof Probe (OneWire bus)
 *   - Physical Connections:
 *       Red Wire (VCC)    -> ESP32 3V3 (3.3V Power Rail)
 *       Black Wire (GND)  -> ESP32 GND (Breadboard Common GND)
 *       Yellow Wire (DQ)  -> ESP32 GPIO P33 (Left Header Pin 8)
 *       Pull-up Resistor  -> 4.7 kΩ between P33 (DATA) and 3V3 Rail
 * 
 * Safety & Isolation:
 *   - ZERO dependencies on Wi-Fi, MQTT, CV, AIS, or backend services.
 *   - ZERO actuators activated (no LEDs, buzzer, relay).
 *   - ZERO changes to production firmware (firmware/src/main.cpp).
 * 
 * Behavior:
 *   - Scans OneWire bus on GPIO 33 for DS18B20 ROM address.
 *   - Samples temperature once per second.
 *   - Reports ROM address, raw reading, validation state, and temperature in °C.
 */

#include <Arduino.h>
#include <OneWire.h>
#include <DallasTemperature.h>

// -----------------------------------------------------------------------------
// Hardware Pin Definition (NodeMCU ESP-32S board label P33)
// -----------------------------------------------------------------------------
constexpr int PIN_DS18B20_DATA = 33;  // GPIO 33 (Board silkscreen P33)

// -----------------------------------------------------------------------------
// Timing Constants
// -----------------------------------------------------------------------------
constexpr unsigned long SAMPLE_INTERVAL_MS = 1000;

// -----------------------------------------------------------------------------
// OneWire & DallasTemperature Instances
// -----------------------------------------------------------------------------
OneWire oneWireBus(PIN_DS18B20_DATA);
DallasTemperature dallasSensors(&oneWireBus);

// Storage for sensor ROM address (8 bytes)
DeviceAddress sensorDeviceAddress;
bool sensorFound = false;
unsigned long sampleCount = 0;

/**
 * @brief Formats an 8-byte OneWire address into human-readable hex string.
 */
void printAddress(DeviceAddress addr) {
    for (uint8_t i = 0; i < 8; i++) {
        if (addr[i] < 16) Serial.print(F("0"));
        Serial.print(addr[i], HEX);
        if (i < 7) Serial.print(F(":"));
    }
}

void scanAndIdentifySensor() {
    pinMode(PIN_DS18B20_DATA, INPUT);
    delay(10);
    int rawPinState = digitalRead(PIN_DS18B20_DATA);

    Serial.println(F("----------------------------------------------------------"));
    Serial.print(F("[ELECTRICAL CHECK] GPIO 33 Idle Voltage: "));
    if (rawPinState == HIGH) {
        Serial.println(F("HIGH (Pull-up resistor active ~3.3V) 🟢"));
    } else {
        Serial.println(F("LOW (0V — Pull-up NOT reaching pin or grounded!) 🔴"));
        Serial.println(F("                   -> Check: Is the 3V3 rail connected to ESP32 3V3?"));
        Serial.println(F("                   -> Check: Is 4.7kΩ placed between P33 and 3V3?"));
    }

    uint8_t presence = oneWireBus.reset();
    Serial.print(F("[BUS RESET] OneWire Presence Pulse: "));
    Serial.println(presence == 1 ? F("DETECTED 🟢") : F("NO RESPONSE 🔴"));

    dallasSensors.begin();
    int deviceCount = dallasSensors.getDeviceCount();

    Serial.print(F("[BUS SCAN] Probing OneWire bus on GPIO P33... Found devices: "));
    Serial.println(deviceCount);

    if (deviceCount > 0) {
        if (dallasSensors.getAddress(sensorDeviceAddress, 0)) {
            sensorFound = true;
            Serial.print(F("[STATUS] 🟢 DEVICE DETECTED! ROM Address: "));
            printAddress(sensorDeviceAddress);
            Serial.println();

            if (sensorDeviceAddress[0] == 0x28) {
                Serial.println(F("[TYPE]   🟢 Family Code 0x28 (DS18B20 Confirmed)"));
            } else {
                Serial.print(F("[TYPE]   🟡 Other Family Code: 0x"));
                Serial.println(sensorDeviceAddress[0], HEX);
            }

            // Set 12-bit resolution (0.0625°C precision)
            dallasSensors.setResolution(sensorDeviceAddress, 12);
            Serial.print(F("[CONFIG] Resolution set to: "));
            Serial.print(dallasSensors.getResolution(sensorDeviceAddress));
            Serial.println(F("-bit (Conversion time ~750ms)"));
        } else {
            sensorFound = false;
            Serial.println(F("[STATUS] 🟡 Device count > 0 but failed to retrieve ROM address."));
        }
    } else {
        sensorFound = false;
        Serial.println(F("[STATUS] 🔴 NO DS18B20 DETECTED on GPIO P33."));
        Serial.println(F("         Check: 1) Red to 5V (VIN), Black to GND, Yellow to P33."));
        Serial.println(F("                2) 4.7kΩ pull-up between P33 and 3V3."));
        Serial.println(F("                3) Solid breadboard connections across all 3 probe leads."));
    }
    Serial.println(F("----------------------------------------------------------\n"));
}

void setup() {
    Serial.begin(115200);
    delay(1000); // Allow USB-UART bridge to settle

    Serial.println();
    Serial.println(F("=========================================================="));
    Serial.println(F("   AquaSentinel-AI: Isolated DS18B20 Bring-Up"));
    Serial.println(F("   Waterproof Temperature Sensor Verification"));
    Serial.println(F("=========================================================="));
    Serial.println(F("Board    : NodeMCU ESP-32S (38-pin Dev Module)"));
    Serial.println(F("Data Pin : GPIO P33 (OneWire Bus)"));
    Serial.println(F("Pull-up  : 4.7 kΩ between P33 (DATA) and 3V3"));
    Serial.println(F("Wiring   : Red=5V(VIN), Black=GND, Yellow=P33"));
    Serial.println(F("==========================================================\n"));

    scanAndIdentifySensor();
}

void loop() {
    sampleCount++;

    // If sensor was not found previously, attempt re-detection
    if (!sensorFound) {
        scanAndIdentifySensor();
        delay(SAMPLE_INTERVAL_MS);
        return;
    }

    // Request temperature measurement from all sensors on the bus
    unsigned long startTime = millis();
    dallasSensors.requestTemperatures();
    float tempC = dallasSensors.getTempC(sensorDeviceAddress);
    unsigned long duration = millis() - startTime;

    Serial.print(F("[SAMPLE #"));
    Serial.print(sampleCount);
    Serial.print(F(" | +"));
    Serial.print(millis() / 1000);
    Serial.print(F("s] "));

    // Validate reading against known DS18B20 error conditions
    if (tempC == DEVICE_DISCONNECTED_C) { // -127.0°C
        Serial.println(F("🔴 ERROR: Sensor DISCONNECTED (-127.00 °C)"));
        Serial.println(F("          OneWire communication lost. Verify physical contact."));
        sensorFound = false; // Trigger bus re-scan on next loop
    } else if (tempC == 85.0f) {
        Serial.println(F("🟡 WARNING: 85.00 °C (Power-on Reset default)"));
        Serial.println(F("          Conversion incomplete or VCC voltage drop."));
    } else if (tempC < -55.0f || tempC > 125.0f) {
        Serial.print(F("🔴 OUT-OF-RANGE: "));
        Serial.print(tempC, 2);
        Serial.println(F(" °C (Exceeds hardware specification -55°C to +125°C)"));
    } else {
        // Valid temperature reading
        Serial.print(F("🟢 VALID TEMP: "));
        Serial.print(tempC, 2);
        Serial.print(F(" °C  ("));
        Serial.print((tempC * 9.0f / 5.0f) + 32.0f, 2);
        Serial.print(F(" °F)  [Conv: "));
        Serial.print(duration);
        Serial.println(F("ms]"));
    }

    // Maintain ~1 sample per second pacing
    delay(SAMPLE_INTERVAL_MS);
}
