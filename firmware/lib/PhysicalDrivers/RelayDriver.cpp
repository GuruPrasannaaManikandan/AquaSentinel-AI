#include "RelayDriver.h"

RelayDriver::RelayDriver(int pin) : _pin(pin), _state("OFF"), _health(DriverHealth::NOT_INITIALIZED), _initialized(false) {}

bool RelayDriver::initialize() {
    pinMode(_pin, OUTPUT);
    digitalWrite(_pin, HIGH); // Default OFF for active-low board
    _state = "OFF";
    _health = DriverHealth::OK;
    _initialized = true;
    return true;
}

bool RelayDriver::writeState(const char* state) {
    if (!_initialized) {
        _health = DriverHealth::NOT_INITIALIZED;
        return false;
    }
    
    if (strcmp(state, "ON") == 0) {
        digitalWrite(_pin, LOW); // Active-low pull pin down (Relay ON)
        _state = "ON";
    } else {
        digitalWrite(_pin, HIGH); // Active-low pull pin up (Relay OFF)
        _state = "OFF";
    }
    _health = DriverHealth::OK;
    return true;
}

const char* RelayDriver::readState() {
    return _state;
}

bool RelayDriver::selfTest() {
    return _initialized;
}

const char* RelayDriver::status() {
    switch (_health) {
        case DriverHealth::OK: return "OK";
        case DriverHealth::NOT_INITIALIZED: return "NOT_INITIALIZED";
        default: return "UNKNOWN";
    }
}

void RelayDriver::shutdown() {
    writeState("OFF");
    _health = DriverHealth::NOT_INITIALIZED;
}
