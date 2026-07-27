#include "CalibrationMath.h"
#include <cmath>

float CalibrationMath::applyLinear(float raw, float slope, float intercept) {
    if (!isValidFloat(raw) || raw == -999.0f) return -999.0f;
    return (raw * slope) + intercept;
}

float CalibrationMath::applyTurbidity(float rawVolts, float a, float b, float c) {
    if (!isValidFloat(rawVolts) || rawVolts == -999.0f) return -999.0f;
    
    // Quadratic mapping: a * V^2 + b * V + c
    float ntu = a * (rawVolts * rawVolts) + b * rawVolts + c;
    
    if (ntu < 0.0f) ntu = 0.0f;
    if (ntu > 500.0f) ntu = 500.0f;
    return ntu;
}

bool CalibrationMath::isValidFloat(float value) {
    return !std::isnan(value) && !std::isinf(value);
}

bool CalibrationMath::checkDrift(float currentValue, float previousValue, float maxDelta) {
    if (!isValidFloat(currentValue) || !isValidFloat(previousValue)) return false;
    return std::fabs(currentValue - previousValue) > maxDelta;
}
