#ifndef IDIAGNOSTICS_OBSERVER_H
#define IDIAGNOSTICS_OBSERVER_H

#include "HealthAggregator.h"
#include "FaultRegistry.h"

/**
 * @brief Interface for read-only observers of the Diagnostics Subsystem.
 * Observers (Logger, Backend, Dashboard, etc.) receive read-only status reports.
 */
class IDiagnosticsObserver {
public:
    virtual ~IDiagnosticsObserver() {}

    /**
     * @brief Triggered when the diagnostics subsystem compiles a new health status.
     */
    virtual void onHealthStatusAggregated(const SubsystemHealth& health) = 0;

    /**
     * @brief Triggered when a fault transitions (registered or cleared).
     */
    virtual void onFaultStateChanged(int faultId, FaultSeverity severity, bool active, const char* description) = 0;

    /**
     * @brief Triggered when a recovery action is executed.
     */
    virtual void onRecoveryExecuted(int faultId, const char* status) = 0;
};

#endif // IDIAGNOSTICS_OBSERVER_H
