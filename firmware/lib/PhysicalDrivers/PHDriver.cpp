#include "PHDriver.h"

PHDriver::PHDriver(int pin) : _pin(pin), _health(DriverHealth::NOT_INITIALIZED), _initialized(false) {}

bool PHDriver::initialize() {
    pinMode(_pin, INPUT);
    _health = DriverHealth::OK;
    _initialized = true;
    return true;
}

float PHDriver::read() {
    if (!_initialized) {
        _health = DriverHealth::NOT_INITIALIZED;
        return -999.0;
    }
    
    int rawAdc = analogRead(_pin);
    
    // Check hardware bounds (short circuit / floating pin)
    if (rawAdc < 10 || rawAdc > 4080) {
        _health = DriverHealth::ADC_FAILURE;
        return -999.0;
    }
    
    float voltage = rawAdc * (3.3 / 4095.0);
    _health = DriverHealth::OK;
    return voltage; // Returns raw measured voltage
}

bool PHDriver::selfTest() {
    if (!_initialized) {
        _health = DriverHealth::NOT_INITIALIZED;
        return false;
    }
    
    int rawAdc = analogRead(_pin);
    if (rawAdc < 10 || rawAdc > 4080) {
        _health = DriverHealth::ADC_FAILURE;
        return false;
    }
    
    _health = DriverHealth::OK;
    return true;
}

const char* PHDriver::status() {
    switch (_health) {
        case DriverHealth::OK: return "OK";
        case DriverHealth::NOT_INITIALIZED: return "NOT_INITIALIZED";
        case DriverHealth::ADC_FAILURE: return "ADC_FAILURE";
        default: return "UNKNOWN";
    }
}

void PHDriver::shutdown() {
    _health = DriverHealth::NOT_INITIALIZED;
}
