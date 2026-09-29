#include "CalibrationProfiles.h"

// -----------------------------------------------------------------
// Freshwater Profile
// -----------------------------------------------------------------
CalibrationCoefficients FreshwaterProfile::getCoefficients(SensorType type) {
    switch (type) {
        case SensorType::TEMPERATURE:       return {1.0f, 0.0f, -5.0f, 50.0f}; // Digital, direct C
        case SensorType::PH:                return {3.5f, 0.0f, 0.0f, 10.0f};  // pH = 3.5 * V (reconstructed 0.0-8.25V range)
        case SensorType::SALINITY:          return {0.5f, 0.0f, 0.1f, 3.2f};   // Salinity ppt
        case SensorType::TURBIDITY:         return {-1120.4f, 5742.3f, 0.0f, 10.0f}; // Quadratic coefficients (reconstructed 0.0-8.25V range)
        case SensorType::DISSOLVED_OXYGEN:  return {4.0f, 0.0f, 0.1f, 3.2f};   // DO = 4.0 * V
    }
    return {1.0f, 0.0f, 0.0f, 5.0f};
}

ValidationThresholds FreshwaterProfile::getThresholds(SensorType type) {
    switch (type) {
        case SensorType::TEMPERATURE:       return {10.0f, 30.0f, 5.0f, 35.0f, 0.0f, 40.0f};
        case SensorType::PH:                return {6.5f, 8.5f, 6.0f, 9.0f, 0.0f, 14.0f};
        case SensorType::SALINITY:          return {0.0f, 0.5f, 0.0f, 1.0f, 0.0f, 5.0f}; // Low salt
        case SensorType::TURBIDITY:         return {0.0f, 25.0f, 0.0f, 50.0f, 0.0f, 150.0f};
        case SensorType::DISSOLVED_OXYGEN:  return {6.0f, 12.0f, 5.0f, 14.0f, 3.0f, 18.0f};
    }
    return {0.0f, 100.0f, 0.0f, 100.0f, 0.0f, 100.0f};
}


// -----------------------------------------------------------------
// Marine Profile
// -----------------------------------------------------------------
CalibrationCoefficients MarineProfile::getCoefficients(SensorType type) {
    switch (type) {
        case SensorType::TEMPERATURE:       return {1.0f, 0.0f, -5.0f, 50.0f};
        case SensorType::PH:                return {3.5f, 0.0f, 0.1f, 5.0f};
        case SensorType::SALINITY:          return {15.0f, 0.0f, 0.1f, 3.2f};  // High salt ppt
        case SensorType::TURBIDITY:         return {-1120.4f, 5742.3f, 0.1f, 5.0f};
        case SensorType::DISSOLVED_OXYGEN:  return {4.0f, 0.0f, 0.1f, 3.2f};
    }
    return {1.0f, 0.0f, 0.0f, 5.0f};
}

ValidationThresholds MarineProfile::getThresholds(SensorType type) {
    switch (type) {
        case SensorType::TEMPERATURE:       return {15.0f, 28.0f, 10.0f, 32.0f, 5.0f, 38.0f};
        case SensorType::PH:                return {7.8f, 8.4f, 7.5f, 8.7f, 6.5f, 9.5f}; // Alkaline saltwater
        case SensorType::SALINITY:          return {30.0f, 36.0f, 25.0f, 38.0f, 15.0f, 45.0f}; // high salinity
        case SensorType::TURBIDITY:         return {0.0f, 15.0f, 0.0f, 35.0f, 0.0f, 100.0f};
        case SensorType::DISSOLVED_OXYGEN:  return {5.0f, 9.0f, 4.0f, 11.0f, 2.0f, 15.0f};
    }
    return {0.0f, 100.0f, 0.0f, 100.0f, 0.0f, 100.0f};
}


// -----------------------------------------------------------------
// Laboratory Profile (1:1 Reference)
// -----------------------------------------------------------------
CalibrationCoefficients LaboratoryProfile::getCoefficients(SensorType type) {
    // 1:1 voltage tracking for calibration analysis
    return {1.0f, 0.0f, 0.0f, 5.0f};
}

ValidationThresholds LaboratoryProfile::getThresholds(SensorType type) {
    // Generous laboratory bounds to prevent warnings during testing
    return {0.0f, 50.0f, -10.0f, 100.0f, -50.0f, 500.0f};
}
