#ifndef CONFIGURATION_MANAGER_H
#define CONFIGURATION_MANAGER_H

#include "BackendSyncPolicy.h"
#include <stddef.h>

/**
 * @brief Struct holding parsed config properties.
 */
struct BackendConfig {
    char version[16];
    unsigned long telemetryIntervalMs;
    unsigned long heartbeatIntervalMs;
    unsigned long diagnosticsIntervalMs;
};

class ConfigurationManager {
private:
    BackendConfig _activeConfig;
    BackendConfig _previousConfig;
    BackendSyncPolicy* _syncPolicy;
    unsigned long _rollbackCount;

    bool validate(const BackendConfig& config) const;

public:
    ConfigurationManager(BackendSyncPolicy* policy);
    ~ConfigurationManager() {}

    /**
     * @brief Receives dynamic configuration JSON string, validates and applies it.
     * Restores previous settings if validation fails.
     */
    bool receiveConfiguration(const char* jsonPayload);

    const BackendConfig& getActiveConfig() const { return _activeConfig; }
    const BackendConfig& getPreviousConfig() const { return _previousConfig; }
    unsigned long getRollbackCount() const { return _rollbackCount; }
};

#endif // CONFIGURATION_MANAGER_H
