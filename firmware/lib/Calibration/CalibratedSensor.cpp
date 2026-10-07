#include "CalibratedSensor.h"
#include <string.h>

namespace {
// Drivers that already convert to engineering units (or deliberately report raw
// voltage) are passed through untouched instead of re-scaled here.
bool isPassThroughStatus(const char* st) {
    return strcmp(st, "UNVERIFIED_UNCALIBRATED") == 0 ||
           strcmp(st, "PH_ESTIMATE") == 0 ||
           strcmp(st, "PH_CALIBRATED") == 0;
}

// Wiring faults detected by the driver itself; surfaced verbatim.
bool isDriverFaultStatus(const char* st) {
    return strcmp(st, "ADC_SATURATED") == 0 || strcmp(st, "NO_SIGNAL") == 0;
}
}

CalibratedSensor::CalibratedSensor(ISensor* rawSensor, SensorType type, CalibrationManager* manager)
    : _rawSensor(rawSensor), _type(type), _manager(manager), _lastValidation(ValidationState::FAULT), _lastValue(-999.0f) {
}

CalibratedSensor::~CalibratedSensor() {
    delete _rawSensor; // Releasing the wrapped raw driver object
}

bool CalibratedSensor::initialize() {
    bool ok = _rawSensor->initialize();
    _lastValidation = ok ? ValidationState::VALID : ValidationState::FAULT;
    return ok;
}

float CalibratedSensor::read() {
    // If raw sensor is unavailable/deferred, pass through -999.0f without claiming fault
    if (strcmp(_rawSensor->status(), "UNAVAILABLE") == 0) {
        _lastValue = -999.0f;
        return -999.0f;
    }

    float rawValue = _rawSensor->read();
    
    // If raw reading represents a physical hardware error, bypass calibration
    if (rawValue == -999.0f) {
        _lastValidation = ValidationState::FAULT;
        _lastValue = -999.0f;
        return -999.0f;
    }

    // Pass through drivers that convert their own units (pH) or report raw voltage
    // (turbidity), so we do NOT apply a second, made-up conversion.
    if (isPassThroughStatus(_rawSensor->status())) {
        _lastValue = rawValue;
        if (_type == SensorType::PH) {
            _lastValidation = _manager->validate(_type, rawValue);
        }
        return rawValue;
    }

    // Apply Calibration convert
    float calibratedValue = _manager->calibrate(_type, rawValue);
    
    // Apply Validation check
    _lastValidation = _manager->validate(_type, calibratedValue);
    _lastValue = calibratedValue;

    return calibratedValue;
}

bool CalibratedSensor::selfTest() {
    if (strcmp(_rawSensor->status(), "UNAVAILABLE") == 0) {
        return true;
    }

    bool ok = _rawSensor->selfTest();
    if (!ok) {
        _lastValidation = ValidationState::FAULT;
        return false;
    }
    return true;
}

const char* CalibratedSensor::status() {
    // If raw hardware driver flags internal faults or unverified states, override validation states
    if (strcmp(_rawSensor->status(), "FAULT") == 0) {
        return "FAULT";
    }
    if (isPassThroughStatus(_rawSensor->status()) || isDriverFaultStatus(_rawSensor->status())) {
        return _rawSensor->status();
    }
    if (strcmp(_rawSensor->status(), "UNAVAILABLE") == 0) {
        return "UNAVAILABLE";
    }

    switch (_lastValidation) {
        case ValidationState::VALID:    return "OK";
        case ValidationState::WARNING:  return "WARNING";
        case ValidationState::CRITICAL: return "CRITICAL";
        case ValidationState::FAULT:    return "FAULT";
    }
    return "FAULT";
}

void CalibratedSensor::shutdown() {
    _rawSensor->shutdown();
    _lastValidation = ValidationState::FAULT;
}
