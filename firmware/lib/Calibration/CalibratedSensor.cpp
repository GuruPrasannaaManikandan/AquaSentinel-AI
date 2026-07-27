#include "CalibratedSensor.h"
#include <string.h>

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
    float rawValue = _rawSensor->read();
    
    // If raw reading represents a physical hardware error, bypass calibration
    if (rawValue == -999.0f) {
        _lastValidation = ValidationState::FAULT;
        _lastValue = -999.0f;
        return -999.0f;
    }

    // Apply Calibration convert
    float calibratedValue = _manager->calibrate(_type, rawValue);
    
    // Apply Validation check
    _lastValidation = _manager->validate(_type, calibratedValue);
    _lastValue = calibratedValue;

    return calibratedValue;
}

bool CalibratedSensor::selfTest() {
    bool ok = _rawSensor->selfTest();
    if (!ok) {
        _lastValidation = ValidationState::FAULT;
        return false;
    }
    return true;
}

const char* CalibratedSensor::status() {
    // If raw hardware driver flags internal faults, override validation states
    if (strcmp(_rawSensor->status(), "FAULT") == 0) {
        return "FAULT";
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
