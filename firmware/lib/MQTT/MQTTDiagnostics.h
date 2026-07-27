#ifndef MQTT_DIAGNOSTICS_H
#define MQTT_DIAGNOSTICS_H

#include "MQTTState.h"

/**
 * @brief Diagnostic parameters logging MQTT session stats (Version 2).
 */
struct MQTTDiagnostics {
    MQTTState currentState;
    unsigned long connectionCount;
    unsigned long reconnectCount;
    unsigned long publishCount;
    unsigned long subscribeCount;
    unsigned long droppedMessages;
    
    // Session Statistics
    unsigned long brokerSessions;
    unsigned long longestSessionMs;
    unsigned long shortestSessionMs;
    unsigned long averageSessionMs;
    
    // Traffic Statistics
    unsigned long totalBytesSent;
    unsigned long totalBytesReceived;
    unsigned long averagePublishLatencyMs;
    unsigned long averageReceiveLatencyMs;
    float publishSuccessRate;
    unsigned long messageRetryCount;

    // Compatibility parameters
    unsigned long averagePublishTimeMs;
    unsigned long queueDepth;
    unsigned long brokerDisconnects;
    char lastError[32];
};

#endif
