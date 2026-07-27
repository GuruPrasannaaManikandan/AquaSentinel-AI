#include "MockStorage.h"
#include <string.h>

MockStorage::MockStorage() : _hasData(true), _corruptedForTesting(false) {
    loadFactoryDefaults(_inMemoryStore);
    _inMemoryStore.metadata.checksum = calculateChecksum(_inMemoryStore);
}

void MockStorage::loadFactoryDefaults(CalibrationData &data) {
    // 1. Populate metadata
    strcpy(data.metadata.profileId, "PR_FACTORY_01");
    strcpy(data.metadata.name, "Factory Freshwater");
    strcpy(data.metadata.version, "1.0");
    strcpy(data.metadata.author, "System Architect");
    data.metadata.creationTimestamp = 1799999000;
    data.metadata.lastModifiedTimestamp = 1799999000;
    data.metadata.isFactoryDefault = true;
    data.metadata.isValid = true;

    // 2. Coefficients
    data.tempCoeffs = {1.0f, 0.0f, -5.0f, 50.0f};
    data.phCoeffs = {3.5f, 0.0f, 0.1f, 3.2f};
    data.salinityCoeffs = {0.5f, 0.0f, 0.1f, 3.2f};
    data.turbidityCoeffs = {-1120.4f, 5742.3f, 0.1f, 3.2f};
    data.doCoeffs = {4.0f, 0.0f, 0.1f, 3.2f};

    // 3. Validation Thresholds
    data.tempThresholds = {10.0f, 30.0f, 5.0f, 35.0f, 0.0f, 40.0f};
    data.phThresholds = {6.5f, 8.5f, 6.0f, 9.0f, 4.0f, 10.0f};
    data.salinityThresholds = {0.0f, 0.5f, 0.0f, 1.0f, 0.0f, 5.0f};
    data.turbidityThresholds = {0.0f, 25.0f, 0.0f, 50.0f, 0.0f, 150.0f};
    data.doThresholds = {6.0f, 12.0f, 5.0f, 14.0f, 3.0f, 18.0f};
}

uint16_t MockStorage::calculateChecksum(const CalibrationData &data) {
    uint32_t sum = 0;
    // Simple additive check over sensor slopes and intercepts
    sum += (uint32_t)(data.phCoeffs.slope * 100);
    sum += (uint32_t)(data.phCoeffs.intercept * 100);
    sum += (uint32_t)(data.salinityCoeffs.slope * 100);
    sum += (uint32_t)(data.salinityCoeffs.intercept * 100);
    sum += (uint32_t)(data.turbidityCoeffs.slope * 100);
    sum += (uint32_t)(data.turbidityCoeffs.intercept * 100);
    sum += (uint32_t)(data.doCoeffs.slope * 100);
    sum += (uint32_t)(data.doCoeffs.intercept * 100);
    return (uint16_t)(sum & 0xFFFF);
}

bool MockStorage::load(CalibrationData &data) {
    if (!_hasData) return false;
    if (_corruptedForTesting) return false;
    
    data = _inMemoryStore;
    return true;
}

bool MockStorage::save(const CalibrationData &data) {
    if (_corruptedForTesting) return false;
    
    _inMemoryStore = data;
    _inMemoryStore.metadata.checksum = calculateChecksum(_inMemoryStore);
    _hasData = true;
    return true;
}

bool MockStorage::erase() {
    _hasData = false;
    memset(&_inMemoryStore, 0, sizeof(CalibrationData));
    return true;
}

bool MockStorage::exists() {
    return _hasData && !_corruptedForTesting;
}

bool MockStorage::validate(const CalibrationData &data) {
    if (_corruptedForTesting) return false;
    
    // Check validation checks: checksum matches
    uint16_t sum = calculateChecksum(data);
    if (data.metadata.checksum != sum) {
        return false;
    }
    
    // Verify coefficients within basic boundaries
    if (data.phCoeffs.slope < 0.1f || data.phCoeffs.slope > 10.0f) return false;
    if (data.doCoeffs.slope < 0.1f || data.doCoeffs.slope > 15.0f) return false;
    
    return true;
}

void MockStorage::setCorrupted(bool corrupted) {
    _corruptedForTesting = corrupted;
}
