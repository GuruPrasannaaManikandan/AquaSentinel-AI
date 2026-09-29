/**
 * @file main.cpp
 * @brief Phase T1–T8: Isolated Turbidity Sensor Hardware Verification Sketch
 * 
 * Target: MAIN ESP32 (NodeMCU ESP-32S) via Silicon Labs CP210x on COM3
 * ADC Pin: GPIO34 / P34 (Input-only, ADC1_CH6)
 * Circuit:
 *   Turbidity VCC -> ESP32 5V/VIN
 *   Turbidity GND -> Common GND
 *   Turbidity OUT -> 33 kΩ -> P34 (ADC Junction) -> 22 kΩ -> GND
 *   Divider Ratio: V_P34 = 22/(33+22) * V_OUT = 0.400 * V_OUT
 * 
 * Rules:
 *   - Strictly isolated bring-up firmware
 *   - 100 samples per measurement window
 *   - Reports Min, Max, Avg, Median, StdDev, Saturation Count, V_P34, V_OUT
 *   - No conversion directly to NTU
 *   - No production code modified
 */

#include <Arduino.h>
#include <math.h>

#define TURBIDITY_PIN        34
#define WINDOW_SAMPLES       100
#define SAMPLE_INTERVAL_MS   10

// Physical Voltage Divider
const float R_TOP = 33000.0; // 33 kΩ
const float R_BOT = 22000.0; // 22 kΩ
const float DIVIDER_RATIO = R_BOT / (R_TOP + R_BOT); // 0.400

struct WindowMetrics {
    int minRaw;
    int maxRaw;
    float avgRaw;
    float medianRaw;
    float stdRaw;
    int satCount;
    int zeroCount;
    float avgMilliVolts;
    float vP34;
    float vOut;
};

// Global baseline storage
bool dryBaselineValid = false;
float dryOverallMean = 0.0;
float dryOverallMedian = 0.0;
int dryOverallMin = 4095;
int dryOverallMax = 0;
float dryOverallStd = 0.0;
int dryTotalSaturation = 0;

// Repeatability trial storage (up to 5 trials)
struct TrialRecord {
    float meanRaw;
    float medianRaw;
    float vP34;
    float vOut;
};
TrialRecord trials[5];
int trialCount = 0;

// Simple integer comparator for sorting
int compareInts(const void* a, const void* b) {
    return (*(int*)a - *(int*)b);
}

WindowMetrics collectWindow(int sampleCount = WINDOW_SAMPLES, int intervalMs = SAMPLE_INTERVAL_MS) {
    int samples[WINDOW_SAMPLES];
    uint32_t sumRaw = 0;
    uint32_t sumMilliVolts = 0;
    int satCount = 0;
    int zeroCount = 0;

    for (int i = 0; i < sampleCount; i++) {
        int raw = analogRead(TURBIDITY_PIN);
        uint32_t mv = analogReadMilliVolts(TURBIDITY_PIN);
        samples[i] = raw;
        sumRaw += raw;
        sumMilliVolts += mv;

        if (raw >= 4095) satCount++;
        if (raw <= 5) zeroCount++;

        delay(intervalMs);
    }

    float avgRaw = (float)sumRaw / sampleCount;
    float avgMilliVolts = (float)sumMilliVolts / sampleCount;

    // Standard deviation
    float sumSqDiff = 0.0;
    for (int i = 0; i < sampleCount; i++) {
        float diff = (float)samples[i] - avgRaw;
        sumSqDiff += diff * diff;
    }
    float stdRaw = sqrt(sumSqDiff / (sampleCount - 1));

    // Sort to compute median, min, max
    qsort(samples, sampleCount, sizeof(int), compareInts);
    int minRaw = samples[0];
    int maxRaw = samples[sampleCount - 1];
    float medianRaw;
    if (sampleCount % 2 == 0) {
        medianRaw = (samples[(sampleCount / 2) - 1] + samples[sampleCount / 2]) / 2.0;
    } else {
        medianRaw = samples[sampleCount / 2];
    }

    float vP34 = avgMilliVolts / 1000.0;
    float vOut = (DIVIDER_RATIO > 0.0) ? (vP34 / DIVIDER_RATIO) : 0.0;

    WindowMetrics m;
    m.minRaw = minRaw;
    m.maxRaw = maxRaw;
    m.avgRaw = avgRaw;
    m.medianRaw = medianRaw;
    m.stdRaw = stdRaw;
    m.satCount = satCount;
    m.zeroCount = zeroCount;
    m.avgMilliVolts = avgMilliVolts;
    m.vP34 = vP34;
    m.vOut = vOut;

    return m;
}

void printBanner() {
    Serial.println("========================================");
    Serial.println("AquaSentinel Turbidity Verification");
    Serial.println("GPIO P34");
    Serial.println("========================================");
}

void printElectricalConfig() {
    Serial.println("----------------------------------------");
    Serial.println("[ELECTRICAL CIRCUIT CONFIGURATION]");
    Serial.println("  Turbidity VCC       : 5V (from ESP32 VIN)");
    Serial.println("  Turbidity GND       : Common Breadboard GND");
    Serial.println("  Turbidity OUT       : Pin 34 via Resistor Divider");
    Serial.printf("  Divider Resistors   : R1(Top)=%.0f Ω, R2(Bot)=%.0f Ω\n", R_TOP, R_BOT);
    Serial.printf("  Divider Ratio       : %.3f (V_P34 = 0.400 * V_OUT)\n", DIVIDER_RATIO);
    Serial.println("  ESP32 ADC Pin       : GPIO34 / P34 (Input-only, ADC1_CH6)");
    Serial.println("  ADC Resolution      : 12-bit (0 – 4095)");
    Serial.println("  ADC Attenuation     : 11dB (0 – 3.1V Full Scale)");
    Serial.println("  Max Safe P34 Input  : 3.3V (Divider protects up to 8.25V OUT)");
    Serial.println("----------------------------------------");
}

void printWindowMetrics(int windowNum, const WindowMetrics& m) {
    Serial.printf("[WINDOW #%02d] N=%d | Raw ADC: Min=%4d Max=%4d Avg=%6.1f Med=%6.1f Std=%4.1f | Sat=%d | V_P34=%5.3fV | Est V_OUT=%5.3fV\n",
                  windowNum, WINDOW_SAMPLES,
                  m.minRaw, m.maxRaw, m.avgRaw, m.medianRaw, m.stdRaw,
                  m.satCount, m.vP34, m.vOut);

    // Safety checks
    if (m.maxRaw >= 4090) {
        Serial.printf("  >>> [ELECTRICAL WARNING] ADC near saturation (Max Raw=%d)! <<<\n", m.maxRaw);
    }
    if (m.minRaw <= 10) {
        Serial.printf("  >>> [ELECTRICAL WARNING] ADC near zero (Min Raw=%d)! Check sensor power. <<<\n", m.minRaw);
    }
}

// -----------------------------------------------------------------
// PHASE T4: DRY / AIR BASELINE PROTOCOL
// -----------------------------------------------------------------
void runDryBaselineProtocol() {
    Serial.println("\n========================================");
    Serial.println("PHASE T4 — DRY / AIR BASELINE PROTOCOL");
    Serial.println("IMPORTANT: Ensure probe is COMPLETELY DRY and in air.");
    Serial.println("Collecting 5 consecutive 100-sample windows...");
    Serial.println("========================================");

    const int NUM_WINDOWS = 5;
    WindowMetrics windows[NUM_WINDOWS];
    float sumAvg = 0.0;
    float sumMed = 0.0;
    int overallMin = 4095;
    int overallMax = 0;
    float sumVar = 0.0;
    int totalSat = 0;
    float sumMv = 0.0;

    for (int w = 1; w <= NUM_WINDOWS; w++) {
        windows[w - 1] = collectWindow();
        printWindowMetrics(w, windows[w - 1]);

        sumAvg += windows[w - 1].avgRaw;
        sumMed += windows[w - 1].medianRaw;
        sumVar += (windows[w - 1].stdRaw * windows[w - 1].stdRaw);
        if (windows[w - 1].minRaw < overallMin) overallMin = windows[w - 1].minRaw;
        if (windows[w - 1].maxRaw > overallMax) overallMax = windows[w - 1].maxRaw;
        totalSat += windows[w - 1].satCount;
        sumMv += windows[w - 1].avgMilliVolts;
    }

    dryOverallMean = sumAvg / NUM_WINDOWS;
    dryOverallMedian = sumMed / NUM_WINDOWS;
    dryOverallMin = overallMin;
    dryOverallMax = overallMax;
    dryOverallStd = sqrt(sumVar / NUM_WINDOWS);
    dryTotalSaturation = totalSat;
    dryBaselineValid = true;

    float overallVp34 = (sumMv / NUM_WINDOWS) / 1000.0;
    float overallVout = overallVp34 / DIVIDER_RATIO;
    float satPct = ((float)totalSat / (NUM_WINDOWS * WINDOW_SAMPLES)) * 100.0;

    Serial.println("----------------------------------------");
    Serial.println("DRY BASELINE — NOT CALIBRATION");
    Serial.printf("  Windows Collected    : %d (500 total samples)\n", NUM_WINDOWS);
    Serial.printf("  Overall Mean Raw ADC : %.2f\n", dryOverallMean);
    Serial.printf("  Overall Median Raw   : %.2f\n", dryOverallMedian);
    Serial.printf("  Overall Min / Max    : %d / %d (Span: %d)\n", dryOverallMin, dryOverallMax, dryOverallMax - dryOverallMin);
    Serial.printf("  Pooled Standard Dev  : %.2f\n", dryOverallStd);
    Serial.printf("  Saturation Count     : %d (%.2f%%)\n", dryTotalSaturation, satPct);
    Serial.printf("  Mean P34 Voltage     : %.3f V\n", overallVp34);
    Serial.printf("  Estimated Mean V_OUT : %.3f V\n", overallVout);
    Serial.println("----------------------------------------");

    // Phase T4 Pass/Fail Criteria: Non-zero, unsaturated, stable signal within linear ADC range
    bool pass = (totalSat == 0 && dryOverallMean > 20.0 && dryOverallMean < 4000.0 && dryOverallStd < 100.0);
    Serial.printf("DRY BASELINE STATUS    : %s\n", pass ? "PASS" : "FAIL");
    Serial.println("========================================");
}

// -----------------------------------------------------------------
// PHASE T5: WATER RESPONSE TEST PROTOCOL
// -----------------------------------------------------------------
void runWaterResponseProtocol() {
    Serial.println("\n========================================");
    Serial.println("PHASE T5 — CLEAN WATER RESPONSE TEST");
    Serial.println("IMPORTANT: Ensure probe is submerged in clean water.");
    Serial.println("Collecting 5 consecutive 100-sample windows...");
    Serial.println("========================================");

    if (!dryBaselineValid) {
        Serial.println("WARNING: Dry baseline has not been captured yet. Run 'd' first for accurate delta.");
    }

    const int NUM_WINDOWS = 5;
    WindowMetrics windows[NUM_WINDOWS];
    float sumAvg = 0.0;
    float sumMed = 0.0;
    int overallMin = 4095;
    int overallMax = 0;
    float sumVar = 0.0;
    int totalSat = 0;
    float sumMv = 0.0;

    for (int w = 1; w <= NUM_WINDOWS; w++) {
        windows[w - 1] = collectWindow();
        printWindowMetrics(w, windows[w - 1]);

        sumAvg += windows[w - 1].avgRaw;
        sumMed += windows[w - 1].medianRaw;
        sumVar += (windows[w - 1].stdRaw * windows[w - 1].stdRaw);
        if (windows[w - 1].minRaw < overallMin) overallMin = windows[w - 1].minRaw;
        if (windows[w - 1].maxRaw > overallMax) overallMax = windows[w - 1].maxRaw;
        totalSat += windows[w - 1].satCount;
        sumMv += windows[w - 1].avgMilliVolts;
    }

    float waterMean = sumAvg / NUM_WINDOWS;
    float waterMedian = sumMed / NUM_WINDOWS;
    float waterStd = sqrt(sumVar / NUM_WINDOWS);
    float waterVp34 = (sumMv / NUM_WINDOWS) / 1000.0;
    float waterVout = waterVp34 / DIVIDER_RATIO;

    Serial.println("----------------------------------------");
    Serial.println("WATER RESPONSE SUMMARY — NOT CALIBRATION");
    Serial.printf("  Windows Collected    : %d (500 total samples)\n", NUM_WINDOWS);
    Serial.printf("  Water Mean Raw ADC   : %.2f\n", waterMean);
    Serial.printf("  Water Median Raw     : %.2f\n", waterMedian);
    Serial.printf("  Water Min / Max      : %d / %d (Span: %d)\n", overallMin, overallMax, overallMax - overallMin);
    Serial.printf("  Water Standard Dev   : %.2f\n", waterStd);
    Serial.printf("  Water Mean P34 Volt  : %.3f V\n", waterVp34);
    Serial.printf("  Water Est Mean V_OUT : %.3f V\n", waterVout);

    if (dryBaselineValid) {
        float meanShift = waterMean - dryOverallMean;
        float medianShift = waterMedian - dryOverallMedian;
        float voltShift = waterVout - (dryOverallMean * 3.3 / 4095.0 / DIVIDER_RATIO);

        Serial.println("----------------------------------------");
        Serial.println("[COMPARISON AGAINST DRY BASELINE]");
        Serial.printf("  Mean Raw Shift       : %+.2f ADC counts\n", meanShift);
        Serial.printf("  Median Raw Shift     : %+.2f ADC counts\n", medianShift);
        Serial.printf("  Estimated V_OUT Shift: %+.3f V\n", voltShift);

        // A distinct optical response in liquid is observed when optical transmission changes
        bool distinct = (fabs(meanShift) >= 20.0);
        Serial.println("----------------------------------------");
        if (distinct) {
            Serial.println("RESULT: LIQUID RESPONSE DETECTED");
        } else {
            Serial.println("RESULT: NO DISTINCT LIQUID RESPONSE DETECTED");
        }
    } else {
        Serial.println("RESULT: WATER RESPONSE MEASURED (Dry baseline unavailable for delta)");
    }
    Serial.println("========================================");
}

// -----------------------------------------------------------------
// PHASE T6: CONTROLLED MOVEMENT TEST
// -----------------------------------------------------------------
void runMovementTest() {
    Serial.println("\n========================================");
    Serial.println("PHASE T6 — CONTROLLED MOVEMENT TEST");
    Serial.println("1) Observe 3 baseline settled windows.");
    Serial.println("2) Move probe slightly while submerged for 3 windows.");
    Serial.println("3) Keep probe stationary again for 3 settled windows.");
    Serial.println("========================================");

    Serial.println("\n[PART 1: Stationary Baseline (3 windows)]");
    for (int w = 1; w <= 3; w++) {
        WindowMetrics m = collectWindow();
        printWindowMetrics(w, m);
    }

    Serial.println("\n[PART 2: Gentle Movement Active (3 windows)]");
    Serial.println(">>> MOVE PROBE GENTLY IN WATER NOW <<<");
    for (int w = 1; w <= 3; w++) {
        WindowMetrics m = collectWindow();
        printWindowMetrics(w + 3, m);
    }

    Serial.println("\n[PART 3: Probe Settled Again (3 windows)]");
    Serial.println(">>> STOP MOVING PROBE - KEEP STATIONARY <<<");
    for (int w = 1; w <= 3; w++) {
        WindowMetrics m = collectWindow();
        printWindowMetrics(w + 6, m);
    }

    Serial.println("----------------------------------------");
    Serial.println("PHASE T6 MOVEMENT TEST COMPLETE");
    Serial.println("========================================");
}

// -----------------------------------------------------------------
// PHASE T7: REPEATABILITY TRIAL RECORDING
// -----------------------------------------------------------------
void recordRepeatabilityTrial() {
    trialCount++;
    if (trialCount > 5) trialCount = 5;

    Serial.println("\n========================================");
    Serial.printf("PHASE T7 — REPEATABILITY TRIAL #%d\n", trialCount);
    Serial.println("Submerge probe in clean water. Collecting 3 windows...");
    Serial.println("========================================");

    float sumAvg = 0.0;
    float sumMed = 0.0;
    float sumMv = 0.0;
    for (int w = 1; w <= 3; w++) {
        WindowMetrics m = collectWindow();
        printWindowMetrics(w, m);
        sumAvg += m.avgRaw;
        sumMed += m.medianRaw;
        sumMv += m.avgMilliVolts;
    }

    float tMean = sumAvg / 3.0;
    float tMed = sumMed / 3.0;
    float tVp34 = (sumMv / 3.0) / 1000.0;
    float tVout = tVp34 / DIVIDER_RATIO;

    trials[trialCount - 1].meanRaw = tMean;
    trials[trialCount - 1].medianRaw = tMed;
    trials[trialCount - 1].vP34 = tVp34;
    trials[trialCount - 1].vOut = tVout;

    Serial.println("----------------------------------------");
    Serial.printf("[TRIAL #%d SUMMARY]\n", trialCount);
    Serial.printf("  Mean Raw ADC : %.2f\n", tMean);
    Serial.printf("  Median Raw   : %.2f\n", tMed);
    Serial.printf("  V_P34        : %.3f V\n", tVp34);
    Serial.printf("  Est V_OUT    : %.3f V\n", tVout);

    if (trialCount >= 2) {
        Serial.println("----------------------------------------");
        Serial.println("[REPEATABILITY COMPARISON ACROSS ALL RECORDED TRIALS]");
        float trialMin = 9999.0;
        float trialMax = 0.0;
        float sumTrials = 0.0;
        for (int i = 0; i < trialCount; i++) {
            Serial.printf("  Trial #%d: Mean=%.1f ADC | V_P34=%.3fV | Est V_OUT=%.3fV\n",
                          i + 1, trials[i].meanRaw, trials[i].vP34, trials[i].vOut);
            if (trials[i].meanRaw < trialMin) trialMin = trials[i].meanRaw;
            if (trials[i].meanRaw > trialMax) trialMax = trials[i].meanRaw;
            sumTrials += trials[i].meanRaw;
        }
        float trialSpread = trialMax - trialMin;
        float trialMeanAvg = sumTrials / trialCount;
        float spreadPct = (trialSpread / trialMeanAvg) * 100.0;
        Serial.printf("  Max Spread   : %.1f ADC counts (%.2f%% of mean)\n", trialSpread, spreadPct);
        bool repeatable = (spreadPct < 10.0);
        Serial.printf("  REPEATABILITY: %s\n", repeatable ? "PASS (Spread < 10%)" : "FAIL (High variance)");
    }
    Serial.println("========================================");
}

// -----------------------------------------------------------------
// ARDUINO SETUP & LOOP
// -----------------------------------------------------------------
void setup() {
    Serial.begin(115200);
    delay(1000);

    // Configure ADC on GPIO34
    pinMode(TURBIDITY_PIN, INPUT);
    analogReadResolution(12);
    analogSetPinAttenuation(TURBIDITY_PIN, ADC_11db);

    printBanner();
    printElectricalConfig();

    Serial.println("\n[READY] Interactive commands available via Serial Monitor:");
    Serial.println("  'd' -> Run Phase T4 Dry / Air Baseline protocol (5 windows)");
    Serial.println("  'w' -> Run Phase T5 Clean Water Response protocol (5 windows)");
    Serial.println("  'm' -> Run Phase T6 Controlled Movement Test");
    Serial.println("  'r' -> Run Phase T7 Repeatability Trial (record and compare)");
    Serial.println("  'b' -> Print electrical and hardware configuration");
    Serial.println("  'c' -> Toggle continuous streaming mode (default: ON)");
    Serial.println("========================================\n");
}

bool continuousMode = true;
int streamWindowCount = 0;

void loop() {
    if (Serial.available() > 0) {
        char cmd = (char)Serial.read();
        if (cmd == 'd' || cmd == 'D') {
            runDryBaselineProtocol();
        } else if (cmd == 'w' || cmd == 'W') {
            runWaterResponseProtocol();
        } else if (cmd == 'm' || cmd == 'M') {
            runMovementTest();
        } else if (cmd == 'r' || cmd == 'R') {
            recordRepeatabilityTrial();
        } else if (cmd == 'b' || cmd == 'B') {
            printElectricalConfig();
        } else if (cmd == 'c' || cmd == 'C') {
            continuousMode = !continuousMode;
            Serial.printf("[MODE] Continuous streaming %s.\n", continuousMode ? "ENABLED" : "DISABLED");
        }
    }

    if (continuousMode) {
        streamWindowCount++;
        WindowMetrics m = collectWindow();
        printWindowMetrics(streamWindowCount, m);
    } else {
        delay(100);
    }
}
