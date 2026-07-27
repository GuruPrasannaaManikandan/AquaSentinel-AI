#ifndef HAL_H
#define HAL_H

#include "config/PinConfig.h"
#include "config/TelemetryData.h"
#include "interfaces/ISensor.h"
#include "interfaces/IActuator.h"
#include "interfaces/IGPSSensor.h"

/**
 * @brief Hardware Abstraction Layer (HAL) coordinating injected drivers.
 * Satisfies the Dependency Inversion Principle. Exposes a hardware-independent API.
 */
class HAL {
private:
    PinConfig _config;

    // Injected Sensor interfaces
    ISensor* _tempSensor;
    ISensor* _salinitySensor;
    ISensor* _phSensor;
    ISensor* _turbiditySensor;
    ISensor* _doSensor;
    IGPSSensor* _gpsSensor;

    // Injected Actuator interfaces
    IActuator* _greenLed;
    IActuator* _yellowLed;
    IActuator* _redLed;
    IActuator* _buzzer;
    IActuator* _pumpRelay;

    // Internal status state tracker
    const char* _sensorStatus;

public:
    /**
     * @brief Constructor using Dependency Injection.
     * HAL does not instantiate drivers; they are injected as pointers to base interfaces.
     */
    HAL(const PinConfig& config,
        ISensor* tempSensor,
        ISensor* salinitySensor,
        ISensor* phSensor,
        ISensor* turbiditySensor,
        ISensor* doSensor,
        IGPSSensor* gpsSensor,
        IActuator* greenLed,
        IActuator* yellowLed,
        IActuator* redLed,
        IActuator* buzzer,
        IActuator* pumpRelay);

    /**
     * @brief Destructor does NOT delete injected drivers (managed by creator).
     */
    ~HAL();

    bool initialize();
    TelemetryData readAllSensors();
    bool writeActuator(const char* name, const char* state);
    const char* readActuator(const char* name);
    bool runSelfTest();
    void shutdown();
};

#endif
