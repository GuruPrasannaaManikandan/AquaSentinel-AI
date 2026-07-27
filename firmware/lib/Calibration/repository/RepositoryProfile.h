#ifndef REPOSITORY_PROFILE_H
#define REPOSITORY_PROFILE_H

#include "CalibrationProfiles.h"
#include "CalibrationRepository.h"

/**
 * @brief Adapter class that implements the CalibrationProfile interface.
 * Routes coefficients and threshold requests dynamically from the active loaded repository.
 * Keeps CalibrationManager implementation 100% frozen.
 */
class RepositoryProfile : public CalibrationProfile {
private:
    CalibrationRepository* _repository;
public:
    RepositoryProfile(CalibrationRepository* repository);
    ~RepositoryProfile() override {}

    const char* getName() override;
    CalibrationCoefficients getCoefficients(SensorType type) override;
    ValidationThresholds getThresholds(SensorType type) override;
};

#endif
