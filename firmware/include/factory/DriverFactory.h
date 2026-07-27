#ifndef DRIVER_FACTORY_H
#define DRIVER_FACTORY_H

#include "interfaces/ISensor.h"
#include "interfaces/IActuator.h"
#include "interfaces/IGPSSensor.h"
#include "config/PinConfig.h"
#include "config/DriverMode.h"

/**
 * @brief Factory class responsible for instantiating sensor and actuator drivers.
 * Supports toggling execution mode using the DriverMode enum.
 */
class DriverFactory {
public:
    static ISensor* createTemperatureSensor(const PinConfig& config, DriverMode mode);
    static ISensor* createSalinitySensor(const PinConfig& config, DriverMode mode);
    static ISensor* createPHSensor(const PinConfig& config, DriverMode mode);
    static ISensor* createTurbiditySensor(const PinConfig& config, DriverMode mode);
    static ISensor* createDOSensor(const PinConfig& config, DriverMode mode);
    static IGPSSensor* createGPSSensor(const PinConfig& config, DriverMode mode);

    static IActuator* createLED(int pin, DriverMode mode);
    static IActuator* createBuzzer(int pin, DriverMode mode);
    static IActuator* createRelay(int pin, DriverMode mode);
};

#endif
