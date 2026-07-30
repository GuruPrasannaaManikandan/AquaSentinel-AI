#ifndef TASK_ID_H
#define TASK_ID_H

/**
 * @brief Enum class representing unique task identifiers.
 */
enum class TaskId {
    SENSOR_POLLING,
    CALIBRATION,
    HEALTH_CHECK,
    LED_UPDATE,
    BUZZER_UPDATE,
    HEARTBEAT,
    FSM_UPDATE,
    WIFI_UPDATE,
    MQTT_UPDATE,
    BACKEND_UPDATE,
    DIAGNOSTICS_UPDATE
};

#endif
