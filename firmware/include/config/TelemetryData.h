#ifndef TELEMETRY_DATA_H
#define TELEMETRY_DATA_H

/**
 * @brief Canonical data structure aggregating sensor readings for MQTT dispatch.
 */
struct TelemetryData {
    float temperature_c;
    float salinity_ppt;
    float ph;
    float turbidity_ntu;
    float dissolved_oxygen_mg_l;
    double latitude;
    double longitude;
    const char* sensor_status; // "OK", "WARNING", "FAULT"
};

#endif
