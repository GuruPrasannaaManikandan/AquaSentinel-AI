#include "factory/DriverFactory.h"
#include "../lib/MockDrivers/MockDrivers.h"
#include "../lib/PhysicalDrivers/DS18B20Driver.h"
#include "../lib/PhysicalDrivers/PHDriver.h"
#include "../lib/PhysicalDrivers/SalinityDriver.h"
#include "../lib/PhysicalDrivers/TurbidityDriver.h"
#include "../lib/PhysicalDrivers/DODriver.h"
#include "../lib/PhysicalDrivers/LEDDriver.h"
#include "../lib/PhysicalDrivers/BuzzerDriver.h"
#include "../lib/PhysicalDrivers/RelayDriver.h"

ISensor* DriverFactory::createTemperatureSensor(const PinConfig& config, DriverMode mode) {
    if (mode == DriverMode::PHYSICAL) {
        return new DS18B20Driver(config.tempPin);
    }
    return new MockTemperatureSensor(config.tempPin);
}

ISensor* DriverFactory::createSalinitySensor(const PinConfig& config, DriverMode mode) {
    if (mode == DriverMode::PHYSICAL) {
        return new SalinityDriver(config.salinityPin);
    }
    return new MockSalinitySensor(config.salinityPin);
}

ISensor* DriverFactory::createPHSensor(const PinConfig& config, DriverMode mode) {
    if (mode == DriverMode::PHYSICAL) {
        return new PHDriver(config.phPin);
    }
    return new MockPHSensor(config.phPin);
}

ISensor* DriverFactory::createTurbiditySensor(const PinConfig& config, DriverMode mode) {
    if (mode == DriverMode::PHYSICAL) {
        return new TurbidityDriver(config.turbidityPin);
    }
    return new MockTurbiditySensor(config.turbidityPin);
}

ISensor* DriverFactory::createDOSensor(const PinConfig& config, DriverMode mode) {
    if (mode == DriverMode::PHYSICAL) {
        return new DODriver(config.doPin);
    }
    return new MockDOSensor(config.doPin);
}

IGPSSensor* DriverFactory::createGPSSensor(const PinConfig& config, DriverMode mode) {
    // Under Version 3.3.1 objectives, GPS remains Mock only
    return new MockGPSSensor(config.gpsRxPin, config.gpsTxPin);
}

IActuator* DriverFactory::createLED(int pin, DriverMode mode) {
    if (mode == DriverMode::PHYSICAL) {
        return new LEDDriver(pin);
    }
    return new MockLED(pin);
}

IActuator* DriverFactory::createBuzzer(int pin, DriverMode mode) {
    if (mode == DriverMode::PHYSICAL) {
        return new BuzzerDriver(pin);
    }
    return new MockBuzzer(pin);
}

IActuator* DriverFactory::createRelay(int pin, DriverMode mode) {
    if (mode == DriverMode::PHYSICAL) {
        return new RelayDriver(pin);
    }
    return new MockRelay(pin);
}
