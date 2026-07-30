#ifndef DIAGNOSTICS_OBSERVER_MANAGER_H
#define DIAGNOSTICS_OBSERVER_MANAGER_H

#include "IDiagnosticsObserver.h"

#define MAX_DIAGNOSTICS_OBSERVERS 5

/**
 * @brief Class managing subscriptions and notifications dispatch to diagnostics observers.
 */
class DiagnosticsObserverManager {
private:
    IDiagnosticsObserver* _observers[MAX_DIAGNOSTICS_OBSERVERS];
    int _count;

public:
    DiagnosticsObserverManager();
    ~DiagnosticsObserverManager() {}

    /**
     * @brief Subscribes an observer. Returns true if successful.
     */
    bool subscribe(IDiagnosticsObserver* observer);

    /**
     * @brief Unsubscribes an observer. Returns true if successful.
     */
    bool unsubscribe(IDiagnosticsObserver* observer);

    void notifyHealthStatus(const SubsystemHealth& health);
    void notifyFaultState(int faultId, FaultSeverity severity, bool active, const char* description);
    void notifyRecovery(int faultId, const char* status);
};

#endif // DIAGNOSTICS_OBSERVER_MANAGER_H
