#include "MockDrivers.h"

// -----------------------------------------------------------------
// Mock Temperature
// -----------------------------------------------------------------
MockTemperatureSensor::MockTemperatureSensor(int pin) : _pin(pin), _status("UNINITIALIZED") {}
bool MockTemperatureSensor::initialize() {
    _status = "OK";
    return true;
}
float MockTemperatureSensor::read() {
    return 24.5; // Mock temperature Celsius
}
bool MockTemperatureSensor::selfTest() {
    return true;
}
const char* MockTemperatureSensor::status() {
    return _status;
}
void MockTemperatureSensor::shutdown() {}

// -----------------------------------------------------------------
// Mock Salinity
// -----------------------------------------------------------------
MockSalinitySensor::MockSalinitySensor(int pin) : _pin(pin), _status("UNINITIALIZED") {}
bool MockSalinitySensor::initialize() {
    _status = "OK";
    return true;
}
float MockSalinitySensor::read() {
    return 0.2; // Mock salinity ppt (Freshwater)
}
bool MockSalinitySensor::selfTest() {
    return true;
}
const char* MockSalinitySensor::status() {
    return _status;
}
void MockSalinitySensor::shutdown() {}

// -----------------------------------------------------------------
// Mock pH
// -----------------------------------------------------------------
MockPHSensor::MockPHSensor(int pin) : _pin(pin), _status("UNINITIALIZED") {}
bool MockPHSensor::initialize() {
    _status = "OK";
    return true;
}
float MockPHSensor::read() {
    return 7.2; // Mock pH
}
bool MockPHSensor::selfTest() {
    return true;
}
const char* MockPHSensor::status() {
    return _status;
}
void MockPHSensor::shutdown() {}

// -----------------------------------------------------------------
// Mock Turbidity
// -----------------------------------------------------------------
MockTurbiditySensor::MockTurbiditySensor(int pin) : _pin(pin), _status("UNINITIALIZED") {}
bool MockTurbiditySensor::initialize() {
    _status = "OK";
    return true;
}
float MockTurbiditySensor::read() {
    return 3.5; // Mock turbidity NTU
}
bool MockTurbiditySensor::selfTest() {
    return true;
}
const char* MockTurbiditySensor::status() {
    return _status;
}
void MockTurbiditySensor::shutdown() {}

// -----------------------------------------------------------------
// Mock Dissolved Oxygen
// -----------------------------------------------------------------
MockDOSensor::MockDOSensor(int pin) : _pin(pin), _status("UNINITIALIZED") {}
bool MockDOSensor::initialize() {
    _status = "OK";
    return true;
}
float MockDOSensor::read() {
    return 8.2; // Mock DO mg/L
}
bool MockDOSensor::selfTest() {
    return true;
}
const char* MockDOSensor::status() {
    return _status;
}
void MockDOSensor::shutdown() {}

// -----------------------------------------------------------------
// Mock GPS
// -----------------------------------------------------------------
MockGPSSensor::MockGPSSensor(int rxPin, int txPin) : _rxPin(rxPin), _txPin(txPin), _status("UNINITIALIZED") {}
bool MockGPSSensor::initialize() {
    _status = "OK";
    return true;
}
void MockGPSSensor::read(double &lat, double &lon) {
    lat = 27.5;
    lon = -81.2;
}
bool MockGPSSensor::selfTest() {
    return true;
}
const char* MockGPSSensor::status() {
    return _status;
}
void MockGPSSensor::shutdown() {}

// -----------------------------------------------------------------
// Mock LED
// -----------------------------------------------------------------
MockLED::MockLED(int pin) : _pin(pin), _state("OFF"), _status("UNINITIALIZED") {}
bool MockLED::initialize() {
    _status = "OK";
    return true;
}
bool MockLED::writeState(const char* state) {
    _state = state;
    return true;
}
const char* MockLED::readState() {
    return _state;
}
bool MockLED::selfTest() {
    return true;
}
const char* MockLED::status() {
    return _status;
}
void MockLED::shutdown() {
    _state = "OFF";
}

// -----------------------------------------------------------------
// Mock Buzzer
// -----------------------------------------------------------------
MockBuzzer::MockBuzzer(int pin) : _pin(pin), _state("OFF"), _status("UNINITIALIZED") {}
bool MockBuzzer::initialize() {
    _status = "OK";
    return true;
}
bool MockBuzzer::writeState(const char* state) {
    _state = state;
    return true;
}
const char* MockBuzzer::readState() {
    return _state;
}
bool MockBuzzer::selfTest() {
    return true;
}
const char* MockBuzzer::status() {
    return _status;
}
void MockBuzzer::shutdown() {
    _state = "OFF";
}

// -----------------------------------------------------------------
// Mock Relay
// -----------------------------------------------------------------
MockRelay::MockRelay(int pin) : _pin(pin), _state("OFF"), _status("UNINITIALIZED") {}
bool MockRelay::initialize() {
    _status = "OK";
    return true;
}
bool MockRelay::writeState(const char* state) {
    _state = state;
    return true;
}
const char* MockRelay::readState() {
    return _state;
}
bool MockRelay::selfTest() {
    return true;
}
const char* MockRelay::status() {
    return _status;
}
void MockRelay::shutdown() {
    _state = "OFF";
}
