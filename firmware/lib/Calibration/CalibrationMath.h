#ifndef CALIBRATION_MATH_H
#define CALIBRATION_MATH_H

/**
 * @brief Utility class performing mathematical conversion operations and numeric sanitization.
 */
class CalibrationMath {
public:
    static float applyLinear(float raw, float slope, float intercept);
    
    /**
     * @brief Applies standard Gravity turbidity quadratic conversion:
     * NTU = a * V^2 + b * V + c
     */
    static float applyTurbidity(float rawVolts, float a, float b, float c = -4352.9f);
    
    /**
     * @brief Checks if a float is NaN or Infinite.
     */
    static bool isValidFloat(float value);
    
    /**
     * @brief Detects sensor drift (if difference exceeds dynamic delta).
     */
    static bool checkDrift(float currentValue, float previousValue, float maxDelta);
};

#endif
