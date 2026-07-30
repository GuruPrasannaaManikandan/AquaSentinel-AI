#ifndef FAULT_REGISTRY_H
#define FAULT_REGISTRY_H

#include <stddef.h>
#include <string.h>

#define MAX_FAULT_RECORDS 20

/**
 * @brief Enum class specifying device fault severity levels.
 */
enum class FaultSeverity {
    INFO,
    WARNING,
    ERROR,
    CRITICAL
};

/**
 * @brief Helper utility returning a readable string for a fault severity.
 */
inline const char* getFaultSeverityName(FaultSeverity severity) {
    switch (severity) {
        case FaultSeverity::INFO: return "INFO";
        case FaultSeverity::WARNING: return "WARNING";
        case FaultSeverity::ERROR: return "ERROR";
        case FaultSeverity::CRITICAL: return "CRITICAL";
        default: return "UNKNOWN";
    }
}

/**
 * @brief Record structure storing details of registered faults.
 */
struct FaultRecord {
    int faultId;
    char subsystem[16];
    unsigned long timestamp;
    FaultSeverity severity;
    char description[64];
    char recoveryStatus[24];
    bool active;
};

/**
 * @brief Circular bounded static storage logging registered faults.
 */
class FaultRegistry {
private:
    FaultRecord _records[MAX_FAULT_RECORDS];
    int _count;
    int _currentIndex;

public:
    FaultRegistry() : _count(0), _currentIndex(0) {
        memset(_records, 0, sizeof(_records));
    }
    ~FaultRegistry() {}

    /**
     * @brief Adds or updates a fault record in static memory.
     */
    void addFault(const FaultRecord& fault) {
        for (int i = 0; i < _count; i++) {
            if (_records[i].faultId == fault.faultId && _records[i].active) {
                _records[i].timestamp = fault.timestamp;
                _records[i].severity = fault.severity;
                strncpy(_records[i].description, fault.description, sizeof(_records[i].description) - 1);
                strncpy(_records[i].recoveryStatus, fault.recoveryStatus, sizeof(_records[i].recoveryStatus) - 1);
                return;
            }
        }

        _records[_currentIndex] = fault;
        _currentIndex = (_currentIndex + 1) % MAX_FAULT_RECORDS;
        if (_count < MAX_FAULT_RECORDS) {
            _count++;
        }
    }

    /**
     * @brief Clears an active fault and flags it as resolved.
     */
    bool clearFault(int faultId, unsigned long timestamp) {
        for (int i = 0; i < _count; i++) {
            if (_records[i].faultId == faultId && _records[i].active) {
                _records[i].active = false;
                strncpy(_records[i].recoveryStatus, "RESOLVED", sizeof(_records[i].recoveryStatus) - 1);
                _records[i].timestamp = timestamp;
                return true;
            }
        }
        return false;
    }

    int getCount() const { return _count; }
    
    /**
     * @brief Gets a record by index, returning from newest to oldest.
     */
    bool getRecord(int index, FaultRecord& recordOut) const {
        if (index < 0 || index >= _count) return false;
        int idx = (_currentIndex - 1 - index + MAX_FAULT_RECORDS) % MAX_FAULT_RECORDS;
        recordOut = _records[idx];
        return true;
    }

    void clearAll() {
        _count = 0;
        _currentIndex = 0;
        memset(_records, 0, sizeof(_records));
    }
};

#endif // FAULT_REGISTRY_H
