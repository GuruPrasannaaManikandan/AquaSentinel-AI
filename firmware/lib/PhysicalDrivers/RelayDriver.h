#ifndef RELAY_DRIVER_H
#define RELAY_DRIVER_H

#include "interfaces/IActuator.h"
#include "config/DriverHealth.h"
#include <Arduino.h>

class RelayDriver : public IActuator {
private:
    int _pin;
    const char* _state;
    DriverHealth _health;
    bool _initialized;
public:
    RelayDriver(int pin);
    bool initialize() override;
    bool writeState(const char* state) override;
    const char* readState() override;
    bool selfTest() override;
    const char* status() override;
    void shutdown() override;
};

#endif
