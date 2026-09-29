#ifndef UNAVAILABLE_SENSOR_H
#define UNAVAILABLE_SENSOR_H

#include "interfaces/ISensor.h"
#include "interfaces/IGPSSensor.h"

/**
 * @brief Representation of an uninstalled or deferred sensor channel.
 * Reports -999.0f reading and "UNAVAILABLE" status without failing boot/self-tests.
 */
class UnavailableSensor : public ISensor {
private:
    const char* _sensorName;
public:
    UnavailableSensor(const char* name = "SENSOR") : _sensorName(name) {}
    bool initialize() override { return true; }
    float read() override { return -999.0f; }
    bool selfTest() override { return true; }
    const char* status() override { return "UNAVAILABLE"; }
    void shutdown() override {}
};

/**
 * @brief Representation of an uninstalled or deferred GPS module.
 */
class UnavailableGPSSensor : public IGPSSensor {
public:
    UnavailableGPSSensor() {}
    bool initialize() override { return true; }
    void read(double &lat, double &lon) override {
        lat = -999.0;
        lon = -999.0;
    }
    bool selfTest() override { return true; }
    const char* status() override { return "UNAVAILABLE"; }
    void shutdown() override {}
};

#endif
