#ifndef EVENT_SOURCE_H
#define EVENT_SOURCE_H

/**
 * @brief Enum class specifying the origin of FSM events.
 */
enum class EventSource {
    SYSTEM,
    SCHEDULER,
    SENSOR,
    CALIBRATION,
    DIAGNOSTICS,
    FSM,
    NETWORK,
    MQTT,
    USER,
    UNKNOWN
};

#endif
