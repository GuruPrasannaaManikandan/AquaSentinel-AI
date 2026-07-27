#ifndef ICALIBRATION_STORAGE_H
#define ICALIBRATION_STORAGE_H

#include "CalibrationData.h"

/**
 * @brief Abstract interface defining raw storage persistence layer methods.
 */
class ICalibrationStorage {
public:
    virtual ~ICalibrationStorage() {}

    /**
     * @brief Load data from non-volatile storage.
     * @return true on success, false on read failures or missing profiles.
     */
    virtual bool load(CalibrationData &data) = 0;

    /**
     * @brief Save data to storage.
     * @return true on success, false on write errors.
     */
    virtual bool save(const CalibrationData &data) = 0;

    /**
     * @brief Wipe data from storage block.
     * @return true if successful.
     */
    virtual bool erase() = 0;

    /**
     * @brief Check if a valid profile block exists in storage.
     */
    virtual bool exists() = 0;

    /**
     * @brief Verify checksums and coefficient counts.
     */
    virtual bool validate(const CalibrationData &data) = 0;
};

#endif
