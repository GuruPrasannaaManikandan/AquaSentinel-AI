#include "factory/DriverFactory.h"
#include "MockDrivers.h"
#include "DS18B20Driver.h"
#include "PHDriver.h"
#include "SalinityDriver.h"
#include "TurbidityDriver.h"
#include "DODriver.h"
#include "LEDDriver.h"
#include "BuzzerDriver.h"
#include "RelayDriver.h"
#include "interfaces/UnavailableSensor.h"

ISensor* DriverFactory::createTemperatureSensor(const PinConfig& config, DriverMode mode) {
    if (mode == DriverMode::PHYSICAL) {
        return new DS18B20Driver(config.tempPin);
    } else if (mode == DriverMode::HYBRID) {
        return new UnavailableSensor("TEMPERATURE");
    }
    return new MockTemperatureSensor(config.tempPin);
}

ISensor* DriverFactory::createSalinitySensor(const PinConfig& config, DriverMode mode) {
    if (mode == DriverMode::PHYSICAL) {
        return new SalinityDriver(config.salinityPin);
    } else if (mode == DriverMode::HYBRID) {
        return new UnavailableSensor("SALINITY");
    }
    return new MockSalinitySensor(config.salinityPin);
}

ISensor* DriverFactory::createPHSensor(const PinConfig& config, DriverMode mode) {
    if (mode == DriverMode::PHYSICAL || mode == DriverMode::HYBRID) {
        return new PHDriver(config.phPin);
    }
    return new MockPHSensor(config.phPin);
}

ISensor* DriverFactory::createTurbiditySensor(const PinConfig& config, DriverMode mode) {
    if (mode == DriverMode::PHYSICAL || mode == DriverMode::HYBRID) {
        return new TurbidityDriver(config.turbidityPin);
    }
    return new MockTurbiditySensor(config.turbidityPin);
}

ISensor* DriverFactory::createDOSensor(const PinConfig& config, DriverMode mode) {
    if (mode == DriverMode::PHYSICAL) {
        return new DODriver(config.doPin);
    } else if (mode == DriverMode::HYBRID) {
        return new UnavailableSensor("DISSOLVED_OXYGEN");
    }
    return new MockDOSensor(config.doPin);
}

IGPSSensor* DriverFactory::createGPSSensor(const PinConfig& config, DriverMode mode) {
    if (mode == DriverMode::HYBRID) {
        return new UnavailableGPSSensor();
    }
    return new MockGPSSensor(config.gpsRxPin, config.gpsTxPin);
}

IActuator* DriverFactory::createLED(int pin, DriverMode mode) {
    if (mode == DriverMode::PHYSICAL || mode == DriverMode::HYBRID) {
        return new LEDDriver(pin);
    }
    return new MockLED(pin);
}

IActuator* DriverFactory::createBuzzer(int pin, DriverMode mode) {
    if (mode == DriverMode::PHYSICAL || mode == DriverMode::HYBRID) {
        return new BuzzerDriver(pin);
    }
    return new MockBuzzer(pin);
}

IActuator* DriverFactory::createRelay(int pin, DriverMode mode) {
    if (mode == DriverMode::PHYSICAL || mode == DriverMode::HYBRID) {
        return new RelayDriver(pin);
    }
    return new MockRelay(pin);
}
