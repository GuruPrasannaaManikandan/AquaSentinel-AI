#ifndef WIFI_CONFIG_H
#define WIFI_CONFIG_H

/**
 * @brief Dynamic configuration parameters block.
 */
struct WiFiConfig {
    char ssid[32];
    char password[64];
    char hostname[32];
    unsigned long reconnectIntervalMs;
    int maxRetryCount;
    unsigned long connectionTimeoutMs;
    bool dhcpEnabled;
};

#endif
