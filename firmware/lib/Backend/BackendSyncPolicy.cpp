#include "BackendSyncPolicy.h"

BackendSyncPolicy::BackendSyncPolicy() {
    // Default production-grade interval timings
    _heartbeatIntervalMs = 10000;    // 10s heartbeat
    _telemetryIntervalMs = 5000;     // 5s telemetry polling
    _diagnosticsIntervalMs = 30000;  // 30s diagnostics sync
    
    // Default retries
    _registrationRetryLimit = 3;
    _syncRetryLimit = 3;
    _configRetryLimit = 3;
    
    // Limits
    _maxSyncAttempts = 5;
    _recoveryDelayMs = 5000;         // 5s recovery delay before retry
}
