#include "PHDriver.h"
#include "AnalogSampler.h"
#include <Preferences.h>

static const char* PH_NVS_NAMESPACE = "ph_cal";

PHDriver::PHDriver(int pin)
    : _pin(pin), _health(DriverHealth::NOT_INITIALIZED), _initialized(false),
      _status("NOT_INITIALIZED"), _neutralVoltage(DEFAULT_NEUTRAL_V),
      _slopePhPerVolt(DEFAULT_SLOPE), _userCalibrated(false), _lastRaw(0),
      _lastPinVoltage(0.0f), _lastModuleVoltage(0.0f), _lastPh(-999.0f) {}

bool PHDriver::initialize() {
    AnalogSampler::configurePin(_pin);
    loadCalibration();
    _health = DriverHealth::OK;
    _initialized = true;
    _status = _userCalibrated ? "PH_CALIBRATED" : "PH_ESTIMATE";
    printCalibration();
    return true;
}

void PHDriver::loadCalibration() {
    Preferences prefs;
    if (!prefs.begin(PH_NVS_NAMESPACE, true)) {
        return; // namespace not created yet -> defaults
    }
    _neutralVoltage = prefs.getFloat("v7", DEFAULT_NEUTRAL_V);
    _slopePhPerVolt = prefs.getFloat("slope", DEFAULT_SLOPE);
    _userCalibrated = prefs.getBool("cal", false);
    prefs.end();
}

void PHDriver::saveCalibration() {
    Preferences prefs;
    if (!prefs.begin(PH_NVS_NAMESPACE, false)) {
        Serial.println("[PH-CAL] ERROR: could not open NVS to save calibration");
        return;
    }
    prefs.putFloat("v7", _neutralVoltage);
    prefs.putFloat("slope", _slopePhPerVolt);
    prefs.putBool("cal", _userCalibrated);
    prefs.end();
}

void PHDriver::sample() {
    AnalogSample s = AnalogSampler::readMedian(_pin, 31);
    _lastRaw = s.raw;
    _lastPinVoltage = s.volts;
    _lastModuleVoltage = s.volts * DIVIDER_GAIN;
}

float PHDriver::read() {
    if (!_initialized) {
        _health = DriverHealth::NOT_INITIALIZED;
        _status = "NOT_INITIALIZED";
        return -999.0f;
    }

    sample();

    if (_lastRaw >= AnalogSampler::SATURATION_RAW) {
        // Pin at full scale: through a 0.4x divider a 5 V module can only reach ~2 V,
        // so this is a wiring fault (missing divider, Po on the wrong pin, short to 3V3).
        _health = DriverHealth::ADC_FAILURE;
        _status = "ADC_SATURATED";
        _lastPh = -999.0f;
    } else if (_lastRaw <= AnalogSampler::NO_SIGNAL_RAW) {
        _health = DriverHealth::ADC_FAILURE;
        _status = "NO_SIGNAL";
        _lastPh = -999.0f;
    } else {
        _health = DriverHealth::OK;
        _status = _userCalibrated ? "PH_CALIBRATED" : "PH_ESTIMATE";
        _lastPh = 7.0f + _slopePhPerVolt * (_lastModuleVoltage - _neutralVoltage);
    }

    Serial.printf("[PH-DRIVER] GPIO%d rawAdc=%d vadc=%.3f vmodule=%.3f ph=%.2f status=%s\n",
                  _pin, _lastRaw, _lastPinVoltage, _lastModuleVoltage, _lastPh, _status);
    return _lastPh;
}

bool PHDriver::calibrateNeutral() {
    if (!_initialized) return false;
    sample();
    if (_lastRaw >= AnalogSampler::SATURATION_RAW || _lastRaw <= AnalogSampler::NO_SIGNAL_RAW) {
        Serial.printf("[PH-CAL] REJECTED: ADC raw=%d is %s. Fix wiring before calibrating.\n",
                      _lastRaw, _lastRaw >= AnalogSampler::SATURATION_RAW ? "saturated" : "at zero");
        return false;
    }
    _neutralVoltage = _lastModuleVoltage;
    _userCalibrated = true;
    saveCalibration();
    Serial.printf("[PH-CAL] pH 7.00 point stored: V7=%.3f V (saved to flash)\n", _neutralVoltage);
    printCalibration();
    return true;
}

bool PHDriver::calibratePoint(float knownPh) {
    if (!_initialized) return false;
    if (!_userCalibrated) {
        Serial.println("[PH-CAL] REJECTED: run PH_CAL7 first (short the BNC), then PH_CAL <pH>.");
        return false;
    }
    if (fabsf(knownPh - 7.0f) < 1.0f) {
        Serial.println("[PH-CAL] REJECTED: second point must be at least 1 pH away from 7.");
        return false;
    }
    sample();
    float dv = _lastModuleVoltage - _neutralVoltage;
    if (_lastRaw >= AnalogSampler::SATURATION_RAW || fabsf(dv) < 0.02f) {
        Serial.printf("[PH-CAL] REJECTED: voltage change %.3f V too small or ADC saturated.\n", dv);
        return false;
    }
    _slopePhPerVolt = (knownPh - 7.0f) / dv;
    saveCalibration();
    Serial.printf("[PH-CAL] Slope set from pH %.2f point: %.3f pH/V (saved to flash)\n", knownPh, _slopePhPerVolt);
    printCalibration();
    return true;
}

void PHDriver::setSlope(float slopePhPerVolt) {
    if (fabsf(slopePhPerVolt) < 0.5f || fabsf(slopePhPerVolt) > 20.0f) {
        Serial.println("[PH-CAL] REJECTED: slope must be between 0.5 and 20 pH/V (sign allowed).");
        return;
    }
    _slopePhPerVolt = slopePhPerVolt;
    saveCalibration();
    printCalibration();
}

void PHDriver::resetCalibration() {
    _neutralVoltage = DEFAULT_NEUTRAL_V;
    _slopePhPerVolt = DEFAULT_SLOPE;
    _userCalibrated = false;
    saveCalibration();
    Serial.println("[PH-CAL] Calibration reset to defaults.");
    printCalibration();
}

void PHDriver::printCalibration() {
    Serial.printf("[PH-CAL] GPIO%d V7=%.3f V slope=%.3f pH/V calibrated=%s\n",
                  _pin, _neutralVoltage, _slopePhPerVolt, _userCalibrated ? "YES" : "NO (estimate)");
}

bool PHDriver::selfTest() {
    if (!_initialized) {
        Serial.println("[PH-TEST] SelfTest failed: Not initialized!");
        _health = DriverHealth::NOT_INITIALIZED;
        return false;
    }
    sample();
    Serial.printf("[PH-TEST] selfTest rawAdc=%d vmodule=%.3f\n", _lastRaw, _lastModuleVoltage);
    // A saturated or dead pin is reported through status(); the ADC itself works.
    return true;
}

const char* PHDriver::status() {
    return _status;
}

void PHDriver::shutdown() {
    _health = DriverHealth::NOT_INITIALIZED;
    _status = "NOT_INITIALIZED";
    _initialized = false;
}
