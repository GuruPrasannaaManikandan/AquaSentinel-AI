#include "CalibrationRepository.h"
#include <string.h>
#include <Arduino.h>

CalibrationRepository::CalibrationRepository(ICalibrationStorage* storage) : _storage(storage) {
    loadFactoryDefaults(_factoryBackup);
}

CalibrationRepository::~CalibrationRepository() {
    delete _storage;
}

void CalibrationRepository::loadFactoryDefaults(CalibrationData &data) {
    strcpy(data.metadata.profileId, "PR_FACTORY_01");
    strcpy(data.metadata.name, "Factory Freshwater");
    strcpy(data.metadata.version, "1.0");
    strcpy(data.metadata.author, "System Architect");
    data.metadata.creationTimestamp = 1799999000;
    data.metadata.lastModifiedTimestamp = 1799999000;
    data.metadata.checksum = 0; // Handled by storage checkers
    data.metadata.isFactoryDefault = true;
    data.metadata.isValid = true;

    // Default Coefficients (Freshwater defaults)
    data.tempCoeffs = {1.0f, 0.0f, -5.0f, 50.0f};
    data.phCoeffs = {3.5f, 0.0f, 0.1f, 3.2f};
    data.salinityCoeffs = {0.5f, 0.0f, 0.1f, 3.2f};
    data.turbidityCoeffs = {-1120.4f, 5742.3f, 0.1f, 3.2f};
    data.doCoeffs = {4.0f, 0.0f, 0.1f, 3.2f};

    // Validation Thresholds
    data.tempThresholds = {10.0f, 30.0f, 5.0f, 35.0f, 0.0f, 40.0f};
    data.phThresholds = {6.5f, 8.5f, 6.0f, 9.0f, 4.0f, 10.0f};
    data.salinityThresholds = {0.0f, 0.5f, 0.0f, 1.0f, 0.0f, 5.0f};
    data.turbidityThresholds = {0.0f, 25.0f, 0.0f, 50.0f, 0.0f, 150.0f};
    data.doThresholds = {6.0f, 12.0f, 5.0f, 14.0f, 3.0f, 18.0f};
}

bool CalibrationRepository::initialize() {
    Serial.println("[REPOSITORY] Reading non-volatile calibration parameters...");
    
    bool loadOk = _storage->load(_activeData);
    bool validOk = loadOk && _storage->validate(_activeData);
    
    if (!validOk) {
        Serial.println("[WARNING] Calibration storage data CORRUPTED or MISSING!");
        Serial.println("[REPOSITORY] Triggering safety recovery: Loading Factory Defaults...");
        
        _activeData = _factoryBackup;
        bool saveOk = _storage->save(_activeData);
        if (!saveOk) {
            Serial.println("[ERROR] Failed to write Factory default backup block to storage!");
        }
        return false;
    }
    
    Serial.print("[REPOSITORY] Loaded Calibration Profile: ");
    Serial.print(_activeData.metadata.name);
    Serial.print(" (v");
    Serial.print(_activeData.metadata.version);
    Serial.println(")");
    return true;
}

bool CalibrationRepository::load() {
    return _storage->load(_activeData);
}

bool CalibrationRepository::save(const CalibrationData &data) {
    if (!_storage->validate(data)) return false;
    
    bool ok = _storage->save(data);
    if (ok) {
        _activeData = data;
    }
    return ok;
}

bool CalibrationRepository::reset() {
    _storage->erase();
    _activeData = _factoryBackup;
    return _storage->save(_activeData);
}

bool CalibrationRepository::backup() {
    // Write copy to persistent storage backup sector
    return _storage->save(_activeData);
}

bool CalibrationRepository::restore() {
    _activeData = _factoryBackup;
    return _storage->save(_activeData);
}

bool CalibrationRepository::validate(const CalibrationData &data) {
    return _storage->validate(data);
}

CalibrationData CalibrationRepository::getActiveData() const {
    return _activeData;
}

CalibrationCoefficients CalibrationRepository::getCoefficients(SensorType type) const {
    switch (type) {
        case SensorType::TEMPERATURE:       return _activeData.tempCoeffs;
        case SensorType::PH:                return _activeData.phCoeffs;
        case SensorType::SALINITY:          return _activeData.salinityCoeffs;
        case SensorType::TURBIDITY:         return _activeData.turbidityCoeffs;
        case SensorType::DISSOLVED_OXYGEN:  return _activeData.doCoeffs;
    }
    return {1.0f, 0.0f, 0.0f, 3.3f};
}

ValidationThresholds CalibrationRepository::getThresholds(SensorType type) const {
    switch (type) {
        case SensorType::TEMPERATURE:       return _activeData.tempThresholds;
        case SensorType::PH:                return _activeData.phThresholds;
        case SensorType::SALINITY:          return _activeData.salinityThresholds;
        case SensorType::TURBIDITY:         return _activeData.turbidityThresholds;
        case SensorType::DISSOLVED_OXYGEN:  return _activeData.doThresholds;
    }
    return {0.0f, 100.0f, 0.0f, 100.0f, 0.0f, 100.0f};
}
