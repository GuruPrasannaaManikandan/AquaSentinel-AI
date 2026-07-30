#include "ConfigurationManager.h"
#include <ArduinoJson.h>
#include <string.h>
#include <Arduino.h>

ConfigurationManager::ConfigurationManager(BackendSyncPolicy* policy) : _syncPolicy(policy), _rollbackCount(0) {
    strcpy(_activeConfig.version, "1.0");
    _activeConfig.telemetryIntervalMs = 5000;
    _activeConfig.heartbeatIntervalMs = 10000;
    _activeConfig.diagnosticsIntervalMs = 30000;

    _previousConfig = _activeConfig;
}

bool ConfigurationManager::validate(const BackendConfig& config) const {
    if (config.telemetryIntervalMs < 1000 || config.telemetryIntervalMs > 60000) {
        return false;
    }
    if (config.heartbeatIntervalMs < 1000 || config.heartbeatIntervalMs > 60000) {
        return false;
    }
    if (config.diagnosticsIntervalMs < 5000 || config.diagnosticsIntervalMs > 120000) {
        return false;
    }
    if (strlen(config.version) == 0) {
        return false;
    }
    return true;
}

bool ConfigurationManager::receiveConfiguration(const char* jsonPayload) {
    if (!jsonPayload || !_syncPolicy) {
        return false;
    }

    StaticJsonDocument<256> doc;
    DeserializationError error = deserializeJson(doc, jsonPayload);
    if (error) {
        Serial.println("[CONFIG-MANAGER] ERROR: JSON deserialization failed.");
        return false;
    }

    BackendConfig incoming;
    memset(&incoming, 0, sizeof(BackendConfig));

    const char* versionStr = doc["version"];
    strncpy(incoming.version, versionStr ? versionStr : "", sizeof(incoming.version) - 1);
    
    incoming.telemetryIntervalMs = doc["telemetry_interval"] | _activeConfig.telemetryIntervalMs;
    incoming.heartbeatIntervalMs = doc["heartbeat_interval"] | _activeConfig.heartbeatIntervalMs;
    incoming.diagnosticsIntervalMs = doc["diagnostics_interval"] | _activeConfig.diagnosticsIntervalMs;

    if (validate(incoming)) {
        _previousConfig = _activeConfig;
        _activeConfig = incoming;

        _syncPolicy->setTelemetryIntervalMs(_activeConfig.telemetryIntervalMs);
        _syncPolicy->setHeartbeatIntervalMs(_activeConfig.heartbeatIntervalMs);
        _syncPolicy->setDiagnosticsIntervalMs(_activeConfig.diagnosticsIntervalMs);

        Serial.print("[CONFIG-MANAGER] Successfully applied new configuration version: ");
        Serial.println(_activeConfig.version);
        return true;
    } else {
        Serial.println("[CONFIG-MANAGER] WARNING: Validation failed! Rolling back/ignoring changes...");
        _rollbackCount++;
        
        _syncPolicy->setTelemetryIntervalMs(_activeConfig.telemetryIntervalMs);
        _syncPolicy->setHeartbeatIntervalMs(_activeConfig.heartbeatIntervalMs);
        _syncPolicy->setDiagnosticsIntervalMs(_activeConfig.diagnosticsIntervalMs);
        return false;
    }
}
