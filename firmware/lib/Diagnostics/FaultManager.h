#ifndef FAULT_MANAGER_H
#define FAULT_MANAGER_H

#include "FaultRegistry.h"

/**
 * @brief Class managing registering, tracking, clearing, and statistics of faults.
 */
class FaultManager {
private:
    FaultRegistry* _registry;
    unsigned int _faultOccurrences[50]; // Tracks occurrences of up to 50 unique fault IDs

public:
    FaultManager(FaultRegistry* registry);
    ~FaultManager() {}

    /**
     * @brief Registers a fault, incrementing its occurrence counter and writing to registry.
     */
    void registerFault(int faultId, const char* subsystem, FaultSeverity severity, const char* description);

    /**
     * @brief Resolves a fault, marking it inactive.
     */
    void clearFault(int faultId);

    /**
     * @brief Queries if a fault ID is currently active.
     */
    bool isFaultActive(int faultId) const;

    /**
     * @brief Gets the total occurrence count of a fault ID.
     */
    unsigned int getFaultOccurrences(int faultId) const;

    /**
     * @brief Finds the highest severity of all currently active faults.
     */
    bool getHighestActiveSeverity(FaultSeverity& severityOut) const;
};

#endif // FAULT_MANAGER_H
