#ifndef DS18B20_DRIVER_H
#define DS18B20_DRIVER_H

#include "interfaces/ISensor.h"
#include "config/DriverHealth.h"
#include <Arduino.h>
#include <OneWire.h>
#include <DallasTemperature.h>

class DS18B20Driver : public ISensor {
private:
    int _pin;
    OneWire* _oneWire;
    DallasTemperature* _sensors;
    DriverHealth _health;
    bool _initialized;
public:
    DS18B20Driver(int pin);
    ~DS18B20Driver() override;
    bool initialize() override;
    float read() override;
    bool selfTest() override;
    const char* status() override;
    void shutdown() override;
};

#endif
