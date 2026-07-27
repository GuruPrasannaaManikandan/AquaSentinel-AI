#ifndef CALIBRATED_SENSOR_H
#define CALIBRATED_SENSOR_H

#include "interfaces/ISensor.h"
#include "config/SensorType.h"
#include "CalibrationManager.h"

/**
 * @brief Decorator class wrapping raw hardware sensors.
 * Intercepts read calls to perform calibration and validation on-the-fly.
 * Satisfies Open-Closed and Single Responsibility principles.
 */
class CalibratedSensor : public ISensor {
private:
    ISensor* _rawSensor;
    SensorType _type;
    CalibrationManager* _manager;
    ValidationState _lastValidation;
    float _lastValue;
public:
    CalibratedSensor(ISensor* rawSensor, SensorType type, CalibrationManager* manager);
    ~CalibratedSensor() override;

    bool initialize() override;
    
    /**
     * @brief Reads raw voltage, applies profile calibrations, and returns converted values.
     */
    float read() override;
    
    bool selfTest() override;
    
    /**
     * @brief Translates internal validation state to frozen status C-string.
     */
    const char* status() override;
    
    void shutdown() override;
};

#endif
