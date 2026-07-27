#ifndef MQTT_SERIALIZER_H
#define MQTT_SERIALIZER_H

#include "config/TelemetryData.h"
#include "MQTTDiagnostics.h"
#include <stddef.h>

/**
 * @brief Helper class to handle all JSON formatting and command parsing.
 * Restricts manual json string formatting inside connection managers.
 */
class MQTTSerializer {
public:
    static bool serializeTelemetry(const TelemetryData& data, char* buffer, size_t bufferSize);
    static bool serializeDiagnostics(const MQTTDiagnostics& diag, char* buffer, size_t bufferSize);
    static bool parseCommand(const char* payload, char* commandOut, size_t cmdSize);
};

#endif
