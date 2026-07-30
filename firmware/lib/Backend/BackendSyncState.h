#ifndef BACKEND_SYNC_STATE_H
#define BACKEND_SYNC_STATE_H

/**
 * @brief Enum class defining the states of the device-cloud synchronization FSM.
 */
enum class BackendSyncState {
    UNREGISTERED,
    REGISTERING,
    REGISTERED,
    SYNCING,
    SYNCHRONIZED,
    RECOVERING,
    FAILED
};

/**
 * @brief Helper utility returning a readable string name for the sync state.
 */
inline const char* getBackendSyncStateName(BackendSyncState state) {
    switch (state) {
        case BackendSyncState::UNREGISTERED: return "UNREGISTERED";
        case BackendSyncState::REGISTERING:  return "REGISTERING";
        case BackendSyncState::REGISTERED:   return "REGISTERED";
        case BackendSyncState::SYNCING:      return "SYNCING";
        case BackendSyncState::SYNCHRONIZED: return "SYNCHRONIZED";
        case BackendSyncState::RECOVERING:   return "RECOVERING";
        case BackendSyncState::FAILED:       return "FAILED";
        default:                             return "UNKNOWN";
    }
}

#endif // BACKEND_SYNC_STATE_H
