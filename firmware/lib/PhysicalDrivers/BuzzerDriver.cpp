#include "BuzzerDriver.h"

BuzzerDriver::BuzzerDriver(int pin) : _pin(pin), _state("OFF"), _health(DriverHealth::NOT_INITIALIZED), _initialized(false) {}

bool BuzzerDriver::initialize() {
    pinMode(_pin, OUTPUT);
    digitalWrite(_pin, LOW);
    _state = "OFF";
    _health = DriverHealth::OK;
    _initialized = true;
    return true;
}

bool BuzzerDriver::writeState(const char* state) {
    if (!_initialized) {
        _health = DriverHealth::NOT_INITIALIZED;
        return false;
    }
    
    if (strcmp(state, "ON") == 0) {
        digitalWrite(_pin, HIGH); // Base drive ON
        _state = "ON";
    } else {
        digitalWrite(_pin, LOW);
        _state = "OFF";
    }
    _health = DriverHealth::OK;
    return true;
}

const char* BuzzerDriver::readState() {
    return _state;
}

bool BuzzerDriver::selfTest() {
    return _initialized;
}

const char* BuzzerDriver::status() {
    switch (_health) {
        case DriverHealth::OK: return "OK";
        case DriverHealth::NOT_INITIALIZED: return "NOT_INITIALIZED";
        default: return "UNKNOWN";
    }
}

void BuzzerDriver::shutdown() {
    writeState("OFF");
    _health = DriverHealth::NOT_INITIALIZED;
}
