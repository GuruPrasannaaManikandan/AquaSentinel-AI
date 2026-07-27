#ifndef SALINITY_DRIVER_H
#define SALINITY_DRIVER_H

#include "interfaces/ISensor.h"
#include "config/DriverHealth.h"
#include <Arduino.h>

class SalinityDriver : public ISensor {
private:
    int _pin;
    DriverHealth _health;
    bool _initialized;
public:
    SalinityDriver(int pin);
    bool initialize() override;
    float read() override; // Returns raw measured voltage (V)
    bool selfTest() override;
    const char* status() override;
    void shutdown() override;
};

#endif
