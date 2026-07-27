#ifndef MOCK_STORAGE_H
#define MOCK_STORAGE_H

#include "ICalibrationStorage.h"

class MockStorage : public ICalibrationStorage {
private:
    CalibrationData _inMemoryStore;
    bool _hasData;
    bool _corruptedForTesting;

    void loadFactoryDefaults(CalibrationData &data);
    uint16_t calculateChecksum(const CalibrationData &data);

public:
    MockStorage();
    ~MockStorage() override {}

    bool load(CalibrationData &data) override;
    bool save(const CalibrationData &data) override;
    bool erase() override;
    bool exists() override;
    bool validate(const CalibrationData &data) override;

    // Test helper to trigger recovery states
    void setCorrupted(bool corrupted);
};

#endif
