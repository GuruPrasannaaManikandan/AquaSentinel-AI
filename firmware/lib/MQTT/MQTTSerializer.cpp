#include "MQTTSerializer.h"
#include <stdio.h>
#include <string.h>

bool MQTTSerializer::serializeTelemetry(const TelemetryData& data, char* buffer, size_t bufferSize) {
    if (!buffer || bufferSize == 0) return false;
    
    int written = snprintf(buffer, bufferSize,
        "{\"temp\":%.2f,\"pH\":%.2f,\"salinity\":%.2f,\"turbidity\":%.2f,\"do\":%.2f,\"status\":\"%s\"}",
        data.temperature_c, data.ph, data.salinity_ppt, data.turbidity_ntu, data.dissolved_oxygen_mg_l, data.sensor_status);
        
    return (written > 0 && (size_t)written < bufferSize);
}

bool MQTTSerializer::serializeDiagnostics(const MQTTDiagnostics& diag, char* buffer, size_t bufferSize) {
    if (!buffer || bufferSize == 0) return false;

    // Written using V2 diagnostics parameter maps
    int written = snprintf(buffer, bufferSize,
        "{\"sessions\":%lu,\"publishes\":%lu,\"reconnects\":%lu,\"drops\":%lu,\"avg_latency\":%lu,\"queue_depth\":%lu}",
        diag.connectionCount, diag.publishCount, diag.reconnectCount, diag.droppedMessages,
        diag.averagePublishTimeMs, diag.queueDepth);

    return (written > 0 && (size_t)written < bufferSize);
}

bool MQTTSerializer::parseCommand(const char* payload, char* commandOut, size_t cmdSize) {
    if (!payload || !commandOut || cmdSize == 0) return false;

    // Simple parser checking plain command terms
    if (strstr(payload, "SHUTDOWN") != nullptr) {
        strncpy(commandOut, "SHUTDOWN", cmdSize - 1);
        commandOut[cmdSize - 1] = '\0';
        return true;
    }
    else if (strstr(payload, "RECOVER") != nullptr) {
        strncpy(commandOut, "RECOVER", cmdSize - 1);
        commandOut[cmdSize - 1] = '\0';
        return true;
    }
    else if (strstr(payload, "POLL") != nullptr) {
        strncpy(commandOut, "POLL", cmdSize - 1);
        commandOut[cmdSize - 1] = '\0';
        return true;
    }

    strncpy(commandOut, payload, cmdSize - 1);
    commandOut[cmdSize - 1] = '\0';
    return true;
}
