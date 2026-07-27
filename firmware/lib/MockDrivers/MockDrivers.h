#ifndef MOCK_DRIVERS_H
#define MOCK_DRIVERS_H

#include "interfaces/ISensor.h"
#include "interfaces/IActuator.h"
#include "interfaces/IGPSSensor.h"

// -----------------------------------------------------------------
// MOCK SENSORS
// -----------------------------------------------------------------

class MockTemperatureSensor : public ISensor {
private:
    int _pin;
    const char* _status;
public:
    MockTemperatureSensor(int pin);
    bool initialize() override;
    float read() override;
    bool selfTest() override;
    const char* status() override;
    void shutdown() override;
};

class MockSalinitySensor : public ISensor {
private:
    int _pin;
    const char* _status;
public:
    MockSalinitySensor(int pin);
    bool initialize() override;
    float read() override;
    bool selfTest() override;
    const char* status() override;
    void shutdown() override;
};

class MockPHSensor : public ISensor {
private:
    int _pin;
    const char* _status;
public:
    MockPHSensor(int pin);
    bool initialize() override;
    float read() override;
    bool selfTest() override;
    const char* status() override;
    void shutdown() override;
};

class MockTurbiditySensor : public ISensor {
private:
    int _pin;
    const char* _status;
public:
    MockTurbiditySensor(int pin);
    bool initialize() override;
    float read() override;
    bool selfTest() override;
    const char* status() override;
    void shutdown() override;
};

class MockDOSensor : public ISensor {
private:
    int _pin;
    const char* _status;
public:
    MockDOSensor(int pin);
    bool initialize() override;
    float read() override;
    bool selfTest() override;
    const char* status() override;
    void shutdown() override;
};

class MockGPSSensor : public IGPSSensor {
private:
    int _rxPin;
    int _txPin;
    const char* _status;
public:
    MockGPSSensor(int rxPin, int txPin);
    bool initialize() override;
    void read(double &lat, double &lon) override;
    bool selfTest() override;
    const char* status() override;
    void shutdown() override;
};

// -----------------------------------------------------------------
// MOCK ACTUATORS
// -----------------------------------------------------------------

class MockLED : public IActuator {
private:
    int _pin;
    const char* _state;
    const char* _status;
public:
    MockLED(int pin);
    bool initialize() override;
    bool writeState(const char* state) override;
    const char* readState() override;
    bool selfTest() override;
    const char* status() override;
    void shutdown() override;
};

class MockBuzzer : public IActuator {
private:
    int _pin;
    const char* _state;
    const char* _status;
public:
    MockBuzzer(int pin);
    bool initialize() override;
    bool writeState(const char* state) override;
    const char* readState() override;
    bool selfTest() override;
    const char* status() override;
    void shutdown() override;
};

class MockRelay : public IActuator {
private:
    int _pin;
    const char* _state;
    const char* _status;
public:
    MockRelay(int pin);
    bool initialize() override;
    bool writeState(const char* state) override;
    const char* readState() override;
    bool selfTest() override;
    const char* status() override;
    void shutdown() override;
};

#endif
