#ifndef DRIVER_HEALTH_H
#define DRIVER_HEALTH_H

/**
 * @brief Professional enum representing detailed health status of drivers.
 */
enum class DriverHealth {
    OK,
    NOT_INITIALIZED,
    SENSOR_DISCONNECTED,
    OUT_OF_RANGE,
    ADC_FAILURE,
    CRC_FAILURE,
    TIMEOUT,
    UNKNOWN
};

#endif
