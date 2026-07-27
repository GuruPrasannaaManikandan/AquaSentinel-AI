#ifndef WIFI_DIAGNOSTICS_H
#define WIFI_DIAGNOSTICS_H

#include "WiFiState.h"

/**
 * @brief Diagnostic parameters logging wireless stats (Version 2).
 */
struct WiFiDiagnostics {
    WiFiState currentState;
    unsigned long connectionCount;
    unsigned long reconnectCount;
    unsigned long failureCount;
    unsigned long authenticationFailures;
    unsigned long dhcpFailures;
    
    // Duration Trackers (ms)
    unsigned long longestConnectionMs;
    unsigned long shortestConnectionMs;
    unsigned long averageConnectionDurationMs;
    unsigned long averageReconnectIntervalMs;
    float connectionSuccessPercentage;

    // Signal Metrics
    int rssi;
    int maxRSSI;
    int minRSSI;

    // IP/MAC Cache
    char currentIp[16];
    char currentMac[18];
    char lastDisconnectReason[32];
};

#endif
