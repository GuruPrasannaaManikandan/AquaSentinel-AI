#ifndef BACKEND_OBSERVER_MANAGER_H
#define BACKEND_OBSERVER_MANAGER_H

#include "IBackendObserver.h"

#define MAX_BACKEND_OBSERVERS 5

/**
 * @brief Manager coordinates registration and notifications dispatch to registered observers.
 */
class BackendObserverManager {
private:
    IBackendObserver* _observers[MAX_BACKEND_OBSERVERS];
    int _count;

public:
    BackendObserverManager();
    ~BackendObserverManager() {}

    /**
     * @brief Subscribes an observer. Returns true if successful.
     */
    bool subscribe(IBackendObserver* observer);

    /**
     * @brief Unsubscribes an observer. Returns true if successful.
     */
    bool unsubscribe(IBackendObserver* observer);

    void notifySyncStateTransition(BackendSyncState fromState, BackendSyncState toState);
    void notifyConfigUpdated(const char* version, unsigned long telemetryIntervalMs);
    void notifyTelemetryBuffered(const TelemetryData& data, int currentCount);
    void notifyTelemetryDropped(const TelemetryData& droppedData);
    void notifyDiagnosticsSynced();
};

#endif // BACKEND_OBSERVER_MANAGER_H
