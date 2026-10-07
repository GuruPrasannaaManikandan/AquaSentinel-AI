#ifndef TURBIDITY_DRIVER_H
#define TURBIDITY_DRIVER_H

#include "interfaces/ISensor.h"
#include "config/DriverHealth.h"
#include <Arduino.h>

/**
 * @brief Analog turbidity module driver (DFRobot SEN0189 style, 5 V supply).
 *
 * Signal chain: module OUT -> 33k/22k divider (x0.400) -> ESP32 ADC pin.
 * read() returns the reconstructed module output voltage (0 - 5 V); higher
 * voltage means clearer water. ntuEstimate() converts it with the DFRobot
 * curve. Because the module output depends on supply voltage and the
 * trimpot, put the probe in clear water and send TURB_CLEAR once: the clear
 * water voltage is then scaled to the curve's 0 NTU point (4.2 V) and saved.
 *
 * status(): UNVERIFIED_UNCALIBRATED (normal, voltage reported),
 *           ADC_SATURATED / NO_SIGNAL (wiring fault, value -999).
 */
class TurbidityDriver : public ISensor {
private:
    int _pin;
    DriverHealth _health;
    bool _initialized;
    const char* _status;
    int _lastRaw;
    float _lastPinVoltage;
    float _lastModuleVoltage;
    float _clearWaterVoltage; // 0 when no reference has been captured

    void sample();

public:
    static constexpr float DIVIDER_GAIN = 2.5f;
    static constexpr float CURVE_CLEAR_V = 4.2f; // DFRobot curve: ~0 NTU at 4.2 V

    TurbidityDriver(int pin);
    bool initialize() override;
    float read() override; // Returns module output voltage (V), or -999 on wiring fault
    bool selfTest() override;
    const char* status() override;
    void shutdown() override;

    float ntuEstimate() const;          // -1 when no valid reading
    bool captureClearWaterReference();  // TURB_CLEAR serial command
    void resetClearWaterReference();
    bool hasClearWaterReference() const { return _clearWaterVoltage > 0.0f; }
    float clearWaterVoltage() const { return _clearWaterVoltage; }
    int lastRaw() const { return _lastRaw; }
    float lastPinVoltage() const { return _lastPinVoltage; }
    float lastModuleVoltage() const { return _lastModuleVoltage; }
};

#endif
