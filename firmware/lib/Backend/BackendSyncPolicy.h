#ifndef BACKEND_SYNC_POLICY_H
#define BACKEND_SYNC_POLICY_H

/**
 * @brief Policy class holding timing intervals and retry limits for backend sync.
 */
class BackendSyncPolicy {
private:
    unsigned long _heartbeatIntervalMs;
    unsigned long _telemetryIntervalMs;
    unsigned long _diagnosticsIntervalMs;
    
    unsigned int _registrationRetryLimit;
    unsigned int _syncRetryLimit;
    unsigned int _configRetryLimit;
    
    unsigned int _maxSyncAttempts;
    unsigned long _recoveryDelayMs;

public:
    BackendSyncPolicy();
    ~BackendSyncPolicy() {}

    unsigned long getHeartbeatIntervalMs() const { return _heartbeatIntervalMs; }
    void setHeartbeatIntervalMs(unsigned long val) { _heartbeatIntervalMs = val; }

    unsigned long getTelemetryIntervalMs() const { return _telemetryIntervalMs; }
    void setTelemetryIntervalMs(unsigned long val) { _telemetryIntervalMs = val; }

    unsigned long getDiagnosticsIntervalMs() const { return _diagnosticsIntervalMs; }
    void setDiagnosticsIntervalMs(unsigned long val) { _diagnosticsIntervalMs = val; }

    unsigned int getRegistrationRetryLimit() const { return _registrationRetryLimit; }
    void setRegistrationRetryLimit(unsigned int val) { _registrationRetryLimit = val; }

    unsigned int getSyncRetryLimit() const { return _syncRetryLimit; }
    void setSyncRetryLimit(unsigned int val) { _syncRetryLimit = val; }

    unsigned int getConfigRetryLimit() const { return _configRetryLimit; }
    void setConfigRetryLimit(unsigned int val) { _configRetryLimit = val; }

    unsigned int getMaxSyncAttempts() const { return _maxSyncAttempts; }
    void setMaxSyncAttempts(unsigned int val) { _maxSyncAttempts = val; }

    unsigned long getRecoveryDelayMs() const { return _recoveryDelayMs; }
    void setRecoveryDelayMs(unsigned long val) { _recoveryDelayMs = val; }
};

#endif // BACKEND_SYNC_POLICY_H
