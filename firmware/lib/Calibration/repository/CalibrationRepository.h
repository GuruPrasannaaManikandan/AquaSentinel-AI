#ifndef CALIBRATION_REPOSITORY_H
#define CALIBRATION_REPOSITORY_H

#include "ICalibrationStorage.h"
#include "config/SensorType.h"

class CalibrationRepository {
private:
    ICalibrationStorage* _storage;
    CalibrationData _activeData;
    CalibrationData _factoryBackup;

    void loadFactoryDefaults(CalibrationData &data);

public:
    CalibrationRepository(ICalibrationStorage* storage);
    ~CalibrationRepository();

    /**
     * @brief Boot initialization.
     * Loads the active profile from storage. If it is corrupted or missing,
     * it recovers by falling back to Factory Defaults.
     */
    bool initialize();

    bool load();
    bool save(const CalibrationData &data);
    
    /**
     * @brief Restores storage to factory default coefficients.
     */
    bool reset();
    
    bool backup();
    bool restore();
    bool validate(const CalibrationData &data);

    CalibrationData getActiveData() const;
    CalibrationCoefficients getCoefficients(SensorType type) const;
    ValidationThresholds getThresholds(SensorType type) const;
};

#endif
