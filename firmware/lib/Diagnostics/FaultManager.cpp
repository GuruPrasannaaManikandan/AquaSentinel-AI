#include "FaultManager.h"
#include <Arduino.h>

FaultManager::FaultManager(FaultRegistry* registry) : _registry(registry) {
    memset(_faultOccurrences, 0, sizeof(_faultOccurrences));
}

void FaultManager::registerFault(int faultId, const char* subsystem, FaultSeverity severity, const char* description) {
    if (!_registry) return;

    if (faultId >= 0 && faultId < 50) {
        _faultOccurrences[faultId]++;
    }

    FaultRecord record;
    record.faultId = faultId;
    strncpy(record.subsystem, subsystem ? subsystem : "UNKNOWN", sizeof(record.subsystem) - 1);
    record.subsystem[sizeof(record.subsystem) - 1] = '\0';
    record.timestamp = millis();
    record.severity = severity;
    strncpy(record.description, description ? description : "", sizeof(record.description) - 1);
    record.description[sizeof(record.description) - 1] = '\0';
    strncpy(record.recoveryStatus, "PENDING", sizeof(record.recoveryStatus) - 1);
    record.recoveryStatus[sizeof(record.recoveryStatus) - 1] = '\0';
    record.active = true;

    _registry->addFault(record);

    Serial.print("[FAULT-MANAGER] Registered Fault ID: ");
    Serial.print(faultId);
    Serial.print(" | Subsystem: ");
    Serial.print(record.subsystem);
    Serial.print(" | Severity: ");
    Serial.print(getFaultSeverityName(severity));
    Serial.print(" | Desc: ");
    Serial.println(record.description);
}

void FaultManager::clearFault(int faultId) {
    if (!_registry) return;

    bool cleared = _registry->clearFault(faultId, millis());
    if (cleared) {
        Serial.print("[FAULT-MANAGER] Cleared Fault ID: ");
        Serial.println(faultId);
    }
}

bool FaultManager::isFaultActive(int faultId) const {
    if (!_registry) return false;

    int count = _registry->getCount();
    FaultRecord record;
    for (int i = 0; i < count; i++) {
        if (_registry->getRecord(i, record)) {
            if (record.faultId == faultId && record.active) {
                return true;
            }
        }
    }
    return false;
}

unsigned int FaultManager::getFaultOccurrences(int faultId) const {
    if (faultId >= 0 && faultId < 50) {
        return _faultOccurrences[faultId];
    }
    return 0;
}

bool FaultManager::getHighestActiveSeverity(FaultSeverity& severityOut) const {
    if (!_registry) return false;

    int count = _registry->getCount();
    FaultRecord record;
    bool anyActive = false;
    FaultSeverity highest = FaultSeverity::INFO;

    for (int i = 0; i < count; i++) {
        if (_registry->getRecord(i, record)) {
            if (record.active) {
                anyActive = true;
                if (static_cast<int>(record.severity) > static_cast<int>(highest)) {
                    highest = record.severity;
                }
            }
        }
    }

    if (anyActive) {
        severityOut = highest;
        return true;
    }
    return false;
}
