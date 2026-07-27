#include "LEDDriver.h"

LEDDriver::LEDDriver(int pin) : _pin(pin), _state("OFF"), _health(DriverHealth::NOT_INITIALIZED), _initialized(false) {}

bool LEDDriver::initialize() {
    pinMode(_pin, OUTPUT);
    digitalWrite(_pin, LOW);
    _state = "OFF";
    _health = DriverHealth::OK;
    _initialized = true;
    return true;
}

bool LEDDriver::writeState(const char* state) {
    if (!_initialized) {
        _health = DriverHealth::NOT_INITIALIZED;
        return false;
    }
    
    if (strcmp(state, "ON") == 0) {
        digitalWrite(_pin, HIGH);
        _state = "ON";
    } else {
        digitalWrite(_pin, LOW);
        _state = "OFF";
    }
    _health = DriverHealth::OK;
    return true;
}

const char* LEDDriver::readState() {
    return _state;
}

bool LEDDriver::selfTest() {
    return _initialized;
}

const char* LEDDriver::status() {
    switch (_health) {
        case DriverHealth::OK: return "OK";
        case DriverHealth::NOT_INITIALIZED: return "NOT_INITIALIZED";
        default: return "UNKNOWN";
    }
}

void LEDDriver::shutdown() {
    writeState("OFF");
    _health = DriverHealth::NOT_INITIALIZED;
}
