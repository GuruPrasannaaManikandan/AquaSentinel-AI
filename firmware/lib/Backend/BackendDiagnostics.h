#ifndef BACKEND_DIAGNOSTICS_H
#define BACKEND_DIAGNOSTICS_H

/**
 * @brief Expanded diagnostic tracker for the Backend Integration Layer.
 * Compiles stats on published telemetry/alerts, received commands, state sync, latency, config updates, buffer usage, and durations.
 */
class BackendDiagnostics {
private:
    unsigned long _messagesPublished;
    unsigned long _messagesReceived;
    unsigned long _syncSuccess;
    unsigned long _syncFailure;
    unsigned long _reconnectCount;
    unsigned long _totalSyncTimeMs;
    unsigned long _lastSyncTimestamp;

    // Expanded diagnostics variables
    unsigned long _configUpdates;
    unsigned long _rollbackCount;
    unsigned long _offlineBufferUsage;
    unsigned long _droppedTelemetry;
    unsigned long _sessionDurationMs;
    unsigned long _sessionStartMs;

public:
    BackendDiagnostics();
    ~BackendDiagnostics() {}

    void recordPublish();
    void recordReceive();
    void recordSyncSuccess(unsigned long durationMs);
    void recordSyncFailure();
    void recordReconnect();

    // Expanded recording methods
    void recordConfigUpdate();
    void recordRollback();
    void updateOfflineBufferUsage(unsigned long usage);
    void recordDroppedTelemetry();
    void startSession();
    void endSession();

    unsigned long getMessagesPublished() const { return _messagesPublished; }
    unsigned long getMessagesReceived() const { return _messagesReceived; }
    unsigned long getSyncSuccess() const { return _syncSuccess; }
    unsigned long getSyncFailure() const { return _syncFailure; }
    unsigned long getReconnectCount() const { return _reconnectCount; }
    unsigned long getAverageSyncTimeMs() const;
    unsigned long getLastSyncTimestamp() const { return _lastSyncTimestamp; }

    // Expanded getter methods
    unsigned long getConfigUpdates() const { return _configUpdates; }
    unsigned long getRollbackCount() const { return _rollbackCount; }
    unsigned long getOfflineBufferUsage() const { return _offlineBufferUsage; }
    unsigned long getDroppedTelemetry() const { return _droppedTelemetry; }
    float getSyncSuccessRate() const;
    float getSyncFailureRate() const;
    unsigned long getSessionDurationSeconds() const;

    void reset();
};

#endif // BACKEND_DIAGNOSTICS_H
