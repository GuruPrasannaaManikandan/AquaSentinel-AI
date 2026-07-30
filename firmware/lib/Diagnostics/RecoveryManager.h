#ifndef RECOVERY_MANAGER_H
#define RECOVERY_MANAGER_H

#include "EventDispatcher.h"
#include "FaultRegistry.h"

/**
 * @brief Enum specifying active recovery escalation stages.
 */
enum class RecoveryEscalationLevel {
    RETRY,
    RESTART,
    SHUTDOWN
};

/**
 * @brief Class executing and tracking recovery actions for registered faults.
 */
class RecoveryManager {
private:
    EventDispatcher* _dispatcher;
    RecoveryEscalationLevel _escalationLevel;
    unsigned int _retryCount;
    unsigned int _maxRetries;
    char _status[24];

public:
    RecoveryManager(EventDispatcher* dispatcher);
    ~RecoveryManager() {}

    /**
     * @brief Evaluates an active fault and initiates recovery escalation if necessary.
     */
    void handleFault(int faultId, FaultSeverity severity);

    /**
     * @brief Resets retry counters and escalation stages when faults are cleared.
     */
    void resetRecovery();

    const char* getRecoveryStatus() const { return _status; }
    unsigned int getRetryCount() const { return _retryCount; }
};

#endif // RECOVERY_MANAGER_H
