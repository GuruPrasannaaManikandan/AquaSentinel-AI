#ifndef CALIBRATION_PROFILES_H
#define CALIBRATION_PROFILES_H

#include "config/SensorType.h"

/**
 * @brief Struct holding parameters for linear voltage-to-unit conversions (y = m*x + c).
 */
struct CalibrationCoefficients {
    float slope;
    float intercept;
    float minRawVolts;
    float maxRawVolts;
};

/**
 * @brief Struct holding validation safety bands for calibrated engineering values.
 */
struct ValidationThresholds {
    float minValid;
    float maxValid;
    float minWarning;
    float maxWarning;
    float minCritical;
    float maxCritical;
};

/**
 * @brief Abstract Base Class for calibration profiles.
 */
class CalibrationProfile {
public:
    virtual ~CalibrationProfile() {}
    virtual const char* getName() = 0;
    virtual CalibrationCoefficients getCoefficients(SensorType type) = 0;
    virtual ValidationThresholds getThresholds(SensorType type) = 0;
};

/**
 * @brief Profile configured for Freshwater rivers, lakes, and reservoirs.
 */
class FreshwaterProfile : public CalibrationProfile {
public:
    const char* getName() override { return "Freshwater"; }
    CalibrationCoefficients getCoefficients(SensorType type) override;
    ValidationThresholds getThresholds(SensorType type) override;
};

/**
 * @brief Profile configured for Marine/Estuarine salt waters.
 */
class MarineProfile : public CalibrationProfile {
public:
    const char* getName() override { return "Marine"; }
    CalibrationCoefficients getCoefficients(SensorType type) override;
    ValidationThresholds getThresholds(SensorType type) override;
};

/**
 * @brief Profile configured for laboratory reference and sensor testing.
 */
class LaboratoryProfile : public CalibrationProfile {
public:
    const char* getName() override { return "Laboratory"; }
    CalibrationCoefficients getCoefficients(SensorType type) override;
    ValidationThresholds getThresholds(SensorType type) override;
};

#endif
