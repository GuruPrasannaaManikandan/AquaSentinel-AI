#ifndef WIFI_STATE_H
#define WIFI_STATE_H

/**
 * @brief Enum class specifying internal Wi-Fi connection states.
 */
enum class WiFiState {
    DISCONNECTED,
    CONNECTING,
    AUTHENTICATING,
    DHCP,
    CONNECTED,
    RECONNECTING,
    FAILED,
    DISABLED
};

#endif
