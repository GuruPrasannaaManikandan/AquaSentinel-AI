#include "TurbidityDriver.h"

TurbidityDriver::TurbidityDriver(int pin) : _pin(pin), _health(DriverHealth::NOT_INITIALIZED), _initialized(false) {}

bool TurbidityDriver::initialize() {
    pinMode(_pin, INPUT);
    _health = DriverHealth::OK;
    _initialized = true;
    return true;
}

float TurbidityDriver::read() {
    if (!_initialized) {
        _health = DriverHealth::NOT_INITIALIZED;
        return -999.0;
    }
    
    int rawAdc = analogRead(_pin);
    
    // Physical voltage divider: 33k (top) / 22k (bottom)
    // Vadc = Vout * (22 / (33 + 22)) = Vout * 0.400
    // Reconstruction multiplier: 1 / 0.400 = 2.500f
    float vadc = rawAdc * (3.3f / 4095.0f);
    float vout = vadc * 2.500f;
    _health = DriverHealth::OK;
    Serial.print("[TURBIDITY-DRIVER] GPIO");
    Serial.print(_pin);
    Serial.print(" rawAdc=");
    Serial.print(rawAdc);
    Serial.print(" vadc=");
    Serial.print(vadc);
    Serial.print(" vout=");
    Serial.println(vout);
    return vout; // Returns reconstructed module-side voltage (0.0V - 5.0V range)
}

bool TurbidityDriver::selfTest() {
    if (!_initialized) {
        _health = DriverHealth::NOT_INITIALIZED;
        return false;
    }
    
    int rawAdc = analogRead(_pin);
    _health = DriverHealth::OK;
    return true;
}

const char* TurbidityDriver::status() {
    switch (_health) {
        case DriverHealth::OK: return "UNVERIFIED_UNCALIBRATED";
        case DriverHealth::NOT_INITIALIZED: return "NOT_INITIALIZED";
        case DriverHealth::ADC_FAILURE: return "ADC_FAILURE";
        default: return "UNKNOWN";
    }
}

void TurbidityDriver::shutdown() {
    _health = DriverHealth::NOT_INITIALIZED;
}
