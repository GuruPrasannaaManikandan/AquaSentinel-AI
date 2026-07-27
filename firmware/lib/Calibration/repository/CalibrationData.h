#ifndef CALIBRATION_DATA_H
#define CALIBRATION_DATA_H

#include "CalibrationProfiles.h"
#include <stdint.h>

/**
 * @brief Calibration metadata block containing profile details and version info.
 */
struct CalibrationMetadata {
    char profileId[16];
    char name[32];
    char version[8];
    char author[32];
    uint32_t creationTimestamp;
    uint32_t lastModifiedTimestamp;
    uint16_t checksum;
    bool isFactoryDefault;
    bool isValid;
};

/**
 * @brief Unified resource struct aggregating all calibration parameters.
 */
struct CalibrationData {
    CalibrationMetadata metadata;

    // Coefficients
    CalibrationCoefficients tempCoeffs;
    CalibrationCoefficients phCoeffs;
    CalibrationCoefficients salinityCoeffs;
    CalibrationCoefficients turbidityCoeffs;
    CalibrationCoefficients doCoeffs;

    // Validation Thresholds
    ValidationThresholds tempThresholds;
    ValidationThresholds phThresholds;
    ValidationThresholds salinityThresholds;
    ValidationThresholds turbidityThresholds;
    ValidationThresholds doThresholds;
};

#endif
