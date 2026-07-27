#include "CalibrationProfiles.h"
#include "config/ValidationState.h"

#ifndef CALIBRATION_MANAGER_H
#define CALIBRATION_MANAGER_H

class CalibrationManager {
private:
    CalibrationProfile* _profile;
public:
    CalibrationManager(CalibrationProfile* profile = nullptr);
    ~CalibrationManager();

    void setProfile(CalibrationProfile* profile);
    CalibrationProfile* getProfile() const;

    /**
     * @brief Converts raw volts or Celsius to engineering values.
     * @return Calibrated value, or -999.0 on fault/out-of-bounds inputs.
     */
    float calibrate(SensorType type, float rawValue);

    /**
     * @brief Performs threshold validations.
     * @return ValidationState band (VALID, WARNING, CRITICAL, FAULT).
     */
    ValidationState validate(SensorType type, float calibratedValue);
};

#endif
