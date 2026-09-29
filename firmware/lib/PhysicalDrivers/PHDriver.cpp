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
    
    // Physical voltage divider: 33k (top) / 22k (bottom)
    // Vadc = Vmodule * (22 / (33 + 22)) = Vmodule * 0.400
    // Reconstruction multiplier: 1 / 0.400 = 2.500f
    float vadc = rawAdc * (3.3f / 4095.0f);
    float vmodule = vadc * 2.500f;
    _health = DriverHealth::OK;
    Serial.print("[PH-DRIVER] GPIO");
    Serial.print(_pin);
    Serial.print(" rawAdc=");
    Serial.print(rawAdc);
    Serial.print(" vadc=");
    Serial.print(vadc);
    Serial.print(" vmodule=");
    Serial.println(vmodule);
    return vmodule; // Returns reconstructed module-side voltage (0.0V - 5.0V range)
}

bool PHDriver::selfTest() {
    if (!_initialized) {
        Serial.println("[PH-TEST] SelfTest failed: Not initialized!");
        _health = DriverHealth::NOT_INITIALIZED;
        return false;
    }
    
    int rawAdc = analogRead(_pin);
    Serial.print("[PH-TEST] selfTest rawAdc=");
    Serial.println(rawAdc);
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
