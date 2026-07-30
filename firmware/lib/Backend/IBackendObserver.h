#ifndef IBACKEND_OBSERVER_H
#define IBACKEND_OBSERVER_H

#include "BackendSyncState.h"
#include "config/TelemetryData.h"

/**
 * @brief Observer callback interface tracking Backend Gateway state changes.
 * Ensures observers remain read-only listeners without gateway modification rights.
 */
class IBackendObserver {
public:
    virtual ~IBackendObserver() {}

    /**
     * @brief Triggered when the synchronization state machine transitions to a new state.
     */
    virtual void onSyncStateTransition(BackendSyncState fromState, BackendSyncState toState) = 0;

    /**
     * @brief Triggered when a new configuration version is applied successfully.
     */
    virtual void onConfigUpdated(const char* version, unsigned long telemetryIntervalMs) = 0;

    /**
     * @brief Triggered when telemetry is pushed to the offline buffer.
     */
    virtual void onTelemetryBuffered(const TelemetryData& data, int currentCount) = 0;

    /**
     * @brief Triggered when telemetry is dropped from the buffer due to overflow.
     */
    virtual void onTelemetryDropped(const TelemetryData& droppedData) = 0;

    /**
     * @brief Triggered when diagnostics are sent or updated.
     */
    virtual void onDiagnosticsSynced() = 0;
};

#endif // IBACKEND_OBSERVER_H
