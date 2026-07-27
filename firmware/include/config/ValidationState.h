#ifndef VALIDATION_STATE_H
#define VALIDATION_STATE_H

/**
 * @brief Enum class representing validation bands for calibrated readings.
 */
enum class ValidationState {
    VALID,
    WARNING,
    CRITICAL,
    FAULT
};

#endif
