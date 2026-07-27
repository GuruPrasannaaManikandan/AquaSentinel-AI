#ifndef TURBIDITY_DRIVER_H
#define TURBIDITY_DRIVER_H

#include "interfaces/ISensor.h"
#include "config/DriverHealth.h"
#include <Arduino.h>

class TurbidityDriver : public ISensor {
private:
    int _pin;
    DriverHealth _health;
    bool _initialized;
public:
    TurbidityDriver(int pin);
    bool initialize() override;
    float read() override; // Returns raw measured voltage (V)
    bool selfTest() override;
    const char* status() override;
    void shutdown() override;
};

#endif
