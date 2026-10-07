#ifndef PH_DRIVER_H
#define PH_DRIVER_H

#include "interfaces/ISensor.h"
#include "config/DriverHealth.h"
#include <Arduino.h>

/**
 * @brief Analog pH module driver (Gravity SEN0161 / PH-4502C style amplifier).
 *
 * Signal chain: module Po -> 33k/22k divider (x0.400) -> ESP32 ADC pin.
 * Conversion: pH = 7.0 + slope * (V_module - neutralVoltage)
 *   - Defaults reproduce the DFRobot SEN0161 formula (pH = 3.5 * V), i.e.
 *     slope = +3.5 pH/V and neutralVoltage = 2.0 V.
 *   - A PH-4502C usually needs a negative slope (about -5.7 pH/V); set it with
 *     the PH_SLOPE serial command.
 * Calibration without buffer solution: short the probe BNC (centre pin to
 * shield, which is exactly pH 7.00 / 0 mV) and send PH_CAL7. A second known
 * point (PH_CAL <pH>) refines the slope. Values persist in NVS flash.
 *
 * read() returns pH (already converted) and status() reports:
 *   PH_CALIBRATED  - neutral point measured by the user
 *   PH_ESTIMATE    - running on default coefficients
 *   ADC_SATURATED  - ADC pin is at full scale (wiring/divider problem), value -999
 *   NO_SIGNAL      - ADC pin reads ~0 V (Po not connected), value -999
 */
class PHDriver : public ISensor {
private:
    int _pin;
    DriverHealth _health;
    bool _initialized;
    const char* _status;
    float _neutralVoltage;
    float _slopePhPerVolt;
    bool _userCalibrated;
    int _lastRaw;
    float _lastPinVoltage;
    float _lastModuleVoltage;
    float _lastPh;

    void sample();
    void loadCalibration();
    void saveCalibration();

public:
    static constexpr float DIVIDER_GAIN = 2.5f;   // 1 / (22k / (33k + 22k))
    static constexpr float DEFAULT_NEUTRAL_V = 2.0f;
    static constexpr float DEFAULT_SLOPE = 3.5f;

    PHDriver(int pin);
    bool initialize() override;
    float read() override; // Returns pH, or -999 when the signal is unusable
    bool selfTest() override;
    const char* status() override;
    void shutdown() override;

    // Calibration helpers (driven by serial commands in main.cpp)
    bool calibrateNeutral();             // probe shorted or in pH 7 reference
    bool calibratePoint(float knownPh);  // second reference point -> slope
    void setSlope(float slopePhPerVolt);
    void resetCalibration();
    void printCalibration();

    int lastRaw() const { return _lastRaw; }
    float lastPinVoltage() const { return _lastPinVoltage; }
    float lastModuleVoltage() const { return _lastModuleVoltage; }
    float neutralVoltage() const { return _neutralVoltage; }
    float slope() const { return _slopePhPerVolt; }
    bool isUserCalibrated() const { return _userCalibrated; }
};

#endif
