#ifndef MQTT_STATE_H
#define MQTT_STATE_H

/**
 * @brief Enum class specifying dynamic MQTT communication states.
 */
enum class MQTTState {
    DISCONNECTED,
    CONNECTING,
    CONNECTED,
    RECONNECTING,
    FAILED,
    DISABLED
};

#endif
