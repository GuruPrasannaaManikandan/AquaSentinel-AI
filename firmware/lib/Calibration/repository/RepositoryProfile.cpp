#include "RepositoryProfile.h"

RepositoryProfile::RepositoryProfile(CalibrationRepository* repository) : _repository(repository) {}

const char* RepositoryProfile::getName() {
    // Dynamic naming based on active loaded profile metadata
    return _repository->getActiveData().metadata.name;
}

CalibrationCoefficients RepositoryProfile::getCoefficients(SensorType type) {
    return _repository->getCoefficients(type);
}

ValidationThresholds RepositoryProfile::getThresholds(SensorType type) {
    return _repository->getThresholds(type);
}
