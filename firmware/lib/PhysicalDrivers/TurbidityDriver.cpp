#include "TurbidityDriver.h"
#include "AnalogSampler.h"
#include <Preferences.h>

static const char* TURB_NVS_NAMESPACE = "turb_cal";

TurbidityDriver::TurbidityDriver(int pin)
    : _pin(pin), _health(DriverHealth::NOT_INITIALIZED), _initialized(false),
      _status("NOT_INITIALIZED"), _lastRaw(0), _lastPinVoltage(0.0f),
      _lastModuleVoltage(-999.0f), _clearWaterVoltage(0.0f) {}

bool TurbidityDriver::initialize() {
    AnalogSampler::configurePin(_pin);
    Preferences prefs;
    if (prefs.begin(TURB_NVS_NAMESPACE, true)) {
        _clearWaterVoltage = prefs.getFloat("vclear", 0.0f);
        prefs.end();
    }
    _health = DriverHealth::OK;
    _initialized = true;
    _status = "UNVERIFIED_UNCALIBRATED";
    if (hasClearWaterReference()) {
        Serial.printf("[TURB-CAL] GPIO%d clear-water reference: %.3f V\n", _pin, _clearWaterVoltage);
    } else {
        Serial.printf("[TURB-CAL] GPIO%d clear-water reference not set (send TURB_CLEAR with probe in clear water)\n", _pin);
    }
    return true;
}

void TurbidityDriver::sample() {
    AnalogSample s = AnalogSampler::readMedian(_pin, 31);
    _lastRaw = s.raw;
    _lastPinVoltage = s.volts;
    _lastModuleVoltage = s.volts * DIVIDER_GAIN;
}

float TurbidityDriver::read() {
    if (!_initialized) {
        _health = DriverHealth::NOT_INITIALIZED;
        _status = "NOT_INITIALIZED";
        return -999.0f;
    }

    sample();

    float result = _lastModuleVoltage;
    if (_lastRaw >= AnalogSampler::SATURATION_RAW) {
        _health = DriverHealth::ADC_FAILURE;
        _status = "ADC_SATURATED";
        result = -999.0f;
    } else if (_lastRaw <= AnalogSampler::NO_SIGNAL_RAW) {
        _health = DriverHealth::ADC_FAILURE;
        _status = "NO_SIGNAL";
        result = -999.0f;
    } else {
        _health = DriverHealth::OK;
        _status = "UNVERIFIED_UNCALIBRATED";
    }

    Serial.printf("[TURBIDITY-DRIVER] GPIO%d rawAdc=%d vadc=%.3f vout=%.3f ntu_est=%.1f status=%s\n",
                  _pin, _lastRaw, _lastPinVoltage, _lastModuleVoltage, ntuEstimate(), _status);
    return result;
}

float TurbidityDriver::ntuEstimate() const {
    if (!_initialized || _health != DriverHealth::OK || _lastModuleVoltage <= 0.0f) {
        return -1.0f;
    }
    float v = _lastModuleVoltage;
    if (hasClearWaterReference()) {
        // Output is proportional to transmitted light: map clear water onto 4.2 V.
        v = v * (CURVE_CLEAR_V / _clearWaterVoltage);
    }
    if (v >= CURVE_CLEAR_V) return 0.0f;
    if (v < 2.5f) return 3000.0f; // beyond the curve's range
    float ntu = -1120.4f * v * v + 5742.3f * v - 4352.9f;
    return ntu < 0.0f ? 0.0f : ntu;
}

bool TurbidityDriver::captureClearWaterReference() {
    if (!_initialized) return false;
    sample();
    if (_lastRaw >= AnalogSampler::SATURATION_RAW || _lastRaw <= AnalogSampler::NO_SIGNAL_RAW) {
        Serial.printf("[TURB-CAL] REJECTED: ADC raw=%d is not a usable signal.\n", _lastRaw);
        return false;
    }
    _clearWaterVoltage = _lastModuleVoltage;
    Preferences prefs;
    if (prefs.begin(TURB_NVS_NAMESPACE, false)) {
        prefs.putFloat("vclear", _clearWaterVoltage);
        prefs.end();
    }
    Serial.printf("[TURB-CAL] Clear-water reference stored: %.3f V (saved to flash)\n", _clearWaterVoltage);
    return true;
}

void TurbidityDriver::resetClearWaterReference() {
    _clearWaterVoltage = 0.0f;
    Preferences prefs;
    if (prefs.begin(TURB_NVS_NAMESPACE, false)) {
        prefs.putFloat("vclear", 0.0f);
        prefs.end();
    }
    Serial.println("[TURB-CAL] Clear-water reference cleared.");
}

bool TurbidityDriver::selfTest() {
    if (!_initialized) {
        _health = DriverHealth::NOT_INITIALIZED;
        return false;
    }
    return true;
}

const char* TurbidityDriver::status() {
    return _status;
}

void TurbidityDriver::shutdown() {
    _health = DriverHealth::NOT_INITIALIZED;
    _status = "NOT_INITIALIZED";
    _initialized = false;
}
