#include "CalibrationManager.h"
#include "CalibrationMath.h"

CalibrationManager::CalibrationManager(CalibrationProfile* profile) : _profile(profile) {}

CalibrationManager::~CalibrationManager() {
    // The profile lifecycles are owned by caller setup contexts.
}

void CalibrationManager::setProfile(CalibrationProfile* profile) {
    _profile = profile;
}

CalibrationProfile* CalibrationManager::getProfile() const {
    return _profile;
}

float CalibrationManager::calibrate(SensorType type, float rawValue) {
    if (rawValue == -999.0f || !CalibrationMath::isValidFloat(rawValue)) {
        return -999.0f;
    }

    if (!_profile) {
        return rawValue; // Lab pass-through mode
    }

    CalibrationCoefficients coeffs = _profile->getCoefficients(type);

    // Validate raw voltage limits to detect sensor disconnects or shorts
    if (rawValue < coeffs.minRawVolts || rawValue > coeffs.maxRawVolts) {
        return -999.0f; // raw input out of safe ranges
    }

    if (type == SensorType::TURBIDITY) {
        // Turbidity uses standard quadratic equation: a * V^2 + b * V + c
        // coeffs.slope = a (-1120.4), coeffs.intercept = b (5742.3)
        // c is default -4352.9
        return CalibrationMath::applyTurbidity(rawValue, coeffs.slope, coeffs.intercept);
    }

    // Linear sensors
    return CalibrationMath::applyLinear(rawValue, coeffs.slope, coeffs.intercept);
}

ValidationState CalibrationManager::validate(SensorType type, float calibratedValue) {
    if (calibratedValue == -999.0f || !CalibrationMath::isValidFloat(calibratedValue)) {
        return ValidationState::FAULT;
    }

    if (!_profile) {
        return ValidationState::VALID; // Lab default
    }

    ValidationThresholds thresholds = _profile->getThresholds(type);

    // 1. Critical check (outside critical boundary)
    if (calibratedValue < thresholds.minCritical || calibratedValue > thresholds.maxCritical) {
        return ValidationState::CRITICAL;
    }

    // 2. Warning check (outside warning boundary)
    if (calibratedValue < thresholds.minWarning || calibratedValue > thresholds.maxWarning) {
        return ValidationState::WARNING;
    }

    // 3. Valid check (inside nominal boundary)
    if (calibratedValue >= thresholds.minValid && calibratedValue <= thresholds.maxValid) {
        return ValidationState::VALID;
    }

    return ValidationState::FAULT;
}
