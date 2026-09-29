/**
 * @file main.cpp
 * @brief Stage 05B: Uncontrolled Mineral-Water Response Test — NOT CALIBRATION
 * 
 * Target Hardware:
 *   - NodeMCU ESP-32S (38-pin Dev Module, ESP32-D0WD-V3)
 *   - Serial Port : COM3 @ 115200 baud
 *   - Analog Pin  : GPIO32 / ADC1_CH4 (Header Pin P32)
 * 
 * Physical Circuit (Confirmed & Preserved):
 *   - pH module V+     -> ESP32 5V/VIN
 *   - pH module G      -> Common Breadboard GND Rail -> ESP32 GND
 *   - pH module Po     -> 33 kΩ (R1) -> P32 Junction
 *   - P32 Junction     -> 22 kΩ (R2) -> Common Breadboard GND Rail
 *   - P32 Junction     -> ESP32 P32
 * 
 * Exact Equations:
 *   - V_P32 = V_Po * (22 / (33 + 22)) = V_Po * 0.4000
 *   - For non-saturated samples (raw < 4090):
 *       Estimated V_Po = V_P32 * 2.5000
 * 
 * Test Configuration:
 *   - 200 samples @ 250 ms = 50.0 seconds continuous capture
 */

#include <Arduino.h>

constexpr int PIN_PH_ADC = 32;                 // GPIO32 / ADC1_CH4
constexpr float DIVIDER_RATIO = 22.0f / 55.0f; // 0.4000
constexpr float INVERSE_RATIO = 55.0f / 22.0f; // 2.5000

constexpr float ADC_VREF_V = 3.30f;
constexpr float ADC_MAX_COUNT = 4095.0f;
constexpr uint32_t SATURATION_THRESHOLD = 4090;

constexpr unsigned long SAMPLE_INTERVAL_MS = 250;
constexpr int TOTAL_SAMPLES = 200; // 200 * 250ms = 50.0 seconds

// Data storage for post-test statistical calculations
uint16_t rawArray[TOTAL_SAMPLES];
float vadcArray[TOTAL_SAMPLES];
int sampleIndex = 0;
bool testComplete = false;

void printBanner() {
    Serial.println();
    Serial.println(F("=================================================================="));
    Serial.println(F("   AquaSentinel-AI: Isolated Hardware Bring-Up — Stage 05B"));
    Serial.println(F("   UNCONTROLLED MINERAL-WATER RESPONSE TEST — NOT CALIBRATION"));
    Serial.println(F("=================================================================="));
    Serial.println(F("[CIRCUIT PARAMETERS]"));
    Serial.println(F("  Target Pin         : GPIO32 / ADC1_CH4 (Header Pin P32)"));
    Serial.println(F("  Upper Resistor R1  : 33 kΩ (Po to P32)"));
    Serial.println(F("  Lower Resistor R2  : 22 kΩ (P32 to GND)"));
    Serial.printf("  Divider Transfer   : V_P32 = V_Po * %.4f\n", DIVIDER_RATIO);
    Serial.printf("  Inverse Ratio      : Estimated V_Po = V_P32 * %.4f\n", INVERSE_RATIO);
    Serial.println(F("  Target Window      : 50.0 seconds (200 samples @ 250ms)"));
    Serial.println(F("------------------------------------------------------------------"));
    Serial.println(F("Sample | Time(s) | Raw ADC | Vadc (at P32) | Estimated Po | Status"));
    Serial.println(F("-------+---------+---------+---------------+--------------+--------"));
}

void setup() {
    Serial.begin(115200);
    delay(1000); // Allow USB-UART bridge to settle

    pinMode(PIN_PH_ADC, INPUT);
    analogSetPinAttenuation(PIN_PH_ADC, ADC_11db);
    analogReadResolution(12);

    printBanner();
}

void loop() {
    if (sampleIndex < TOTAL_SAMPLES) {
        uint32_t raw = analogRead(PIN_PH_ADC);
        uint32_t calMilliVolts = analogReadMilliVolts(PIN_PH_ADC);
        float vadc = (float)calMilliVolts / 1000.0f;
        if (calMilliVolts == 0 && raw > 0) {
            vadc = ((float)raw / ADC_MAX_COUNT) * ADC_VREF_V;
        }

        rawArray[sampleIndex] = (uint16_t)raw;
        vadcArray[sampleIndex] = vadc;
        sampleIndex++;

        float elapsedSec = (float)sampleIndex * ((float)SAMPLE_INTERVAL_MS / 1000.0f);

        if (raw >= SATURATION_THRESHOLD) {
            Serial.printf(" #%03d  |  %4.1fs  |  %4u   |    %5.3f V    |   [CLIPPED]  | SATURATED 🔴\n",
                          sampleIndex, elapsedSec, raw, vadc);
        } else {
            float vpo = vadc * INVERSE_RATIO;
            Serial.printf(" #%03d  |  %4.1fs  |  %4u   |    %5.3f V    |   %5.3f V    | SAFE 🟢\n",
                          sampleIndex, elapsedSec, raw, vadc, vpo);
        }

        delay(SAMPLE_INTERVAL_MS);

        if (sampleIndex == TOTAL_SAMPLES) {
            testComplete = true;

            // Compute statistics
            uint32_t rawMin = 4096, rawMax = 0;
            uint64_t rawSum = 0;
            int satCount = 0;

            float vadcMin = 999.0f, vadcMax = -999.0f;
            float vadcSum = 0.0f;

            uint32_t nonSatMin = 4096, nonSatMax = 0;
            uint64_t nonSatSum = 0;
            int nonSatCount = 0;

            for (int i = 0; i < TOTAL_SAMPLES; i++) {
                uint16_t r = rawArray[i];
                float v = vadcArray[i];

                if (r < rawMin) rawMin = r;
                if (r > rawMax) rawMax = r;
                rawSum += r;

                if (v < vadcMin) vadcMin = v;
                if (v > vadcMax) vadcMax = v;
                vadcSum += v;

                if (r >= SATURATION_THRESHOLD) {
                    satCount++;
                } else {
                    if (r < nonSatMin) nonSatMin = r;
                    if (r > nonSatMax) nonSatMax = r;
                    nonSatSum += r;
                    nonSatCount++;
                }
            }

            float rawMean = (float)rawSum / (float)TOTAL_SAMPLES;
            float vadcMean = vadcSum / (float)TOTAL_SAMPLES;
            float satPercent = ((float)satCount / (float)TOTAL_SAMPLES) * 100.0f;

            // Simple bubble sort copy for median calculation
            uint16_t sortedRaw[TOTAL_SAMPLES];
            memcpy(sortedRaw, rawArray, sizeof(sortedRaw));
            for (int i = 0; i < TOTAL_SAMPLES - 1; i++) {
                for (int j = 0; j < TOTAL_SAMPLES - i - 1; j++) {
                    if (sortedRaw[j] > sortedRaw[j + 1]) {
                        uint16_t temp = sortedRaw[j];
                        sortedRaw[j] = sortedRaw[j + 1];
                        sortedRaw[j + 1] = temp;
                    }
                }
            }
            float rawMedian = (TOTAL_SAMPLES % 2 == 0)
                ? (float)(sortedRaw[TOTAL_SAMPLES / 2 - 1] + sortedRaw[TOTAL_SAMPLES / 2]) / 2.0f
                : (float)sortedRaw[TOTAL_SAMPLES / 2];

            // Standard deviation calculation
            double varianceSum = 0;
            for (int i = 0; i < TOTAL_SAMPLES; i++) {
                double diff = (double)rawArray[i] - (double)rawMean;
                varianceSum += diff * diff;
            }
            float rawStDev = sqrt(varianceSum / (double)(TOTAL_SAMPLES - 1));

            Serial.println(F("-------+---------+---------+---------------+--------------+--------"));
            Serial.println();
            Serial.println(F("=================================================================="));
            Serial.println(F("   STAGE 05B STATISTICAL REPORT (50-SECOND WINDOW, 200 SAMPLES)"));
            Serial.println(F("=================================================================="));
            Serial.printf("TEST TYPE            : UNCONTROLLED MINERAL-WATER RESPONSE TEST — NOT CALIBRATION\n");
            Serial.printf("Total Samples Taken  : %d\n", TOTAL_SAMPLES);
            Serial.printf("Sampling Duration    : ~50.0 seconds\n");
            Serial.println(F("------------------------------------------------------------------"));
            Serial.println(F("[RAW ADC METRICS]"));
            Serial.printf("  Min                : %u\n", rawMin);
            Serial.printf("  Max                : %u\n", rawMax);
            Serial.printf("  Mean               : %.2f\n", rawMean);
            Serial.printf("  Median             : %.2f\n", rawMedian);
            Serial.printf("  Standard Deviation : %.2f\n", rawStDev);
            Serial.printf("  Saturation Count   : %d / %d (%.1f%%)\n", satCount, TOTAL_SAMPLES, satPercent);
            Serial.println(F("------------------------------------------------------------------"));
            Serial.println(F("[ADC VOLTAGE METRICS (at P32)]"));
            Serial.printf("  Min                : %.3f V\n", vadcMin);
            Serial.printf("  Max                : %.3f V\n", vadcMax);
            Serial.printf("  Mean               : %.3f V\n", vadcMean);
            Serial.println(F("------------------------------------------------------------------"));
            if (nonSatCount > 0) {
                float nonSatVadcMean = ((float)nonSatSum / (float)nonSatCount / ADC_MAX_COUNT) * ADC_VREF_V;
                float nonSatPoMean = (vadcSum / (float)TOTAL_SAMPLES) * INVERSE_RATIO;
                Serial.println(F("[ESTIMATED Po (Non-Saturated Samples: Vadc * 2.500)]"));
                Serial.printf("  Non-Sat Count      : %d\n", nonSatCount);
                Serial.printf("  Estimated Po Min   : %.3f V\n", vadcMin * INVERSE_RATIO);
                Serial.printf("  Estimated Po Max   : %.3f V\n", (satCount > 0 ? (nonSatMax / ADC_MAX_COUNT * ADC_VREF_V * INVERSE_RATIO) : (vadcMax * INVERSE_RATIO)));
                Serial.printf("  Estimated Po Mean  : %.3f V\n", nonSatPoMean);
            }
            Serial.println(F("=================================================================="));
            Serial.println(F("[TEST COMPLETE] Halting diagnostic. Entering idle state.\n"));
        }
    } else {
        delay(1000);
    }
}
