#ifndef TELEMETRY_PUBLISHER_H
#define TELEMETRY_PUBLISHER_H

#include "config/TelemetryData.h"
#include "MQTTManager.h"

class TelemetryPublisher {
private:
    MQTTManager* _mqttManager;
    char _deviceId[32];
    char _datasetRoute[16];
    unsigned long _sequenceNumber;

public:
    TelemetryPublisher(MQTTManager* mqttManager, const char* deviceId, const char* datasetRoute);
    ~TelemetryPublisher() {}

    /**
     * @brief Formats and publishes telemetry JSON payload via MQTTManager.
     */
    bool publishTelemetry(const TelemetryData& data, float battery, int rssi, const char* isoTimestamp);

    unsigned long getSequenceNumber() const { return _sequenceNumber; }
    void resetSequenceNumber() { _sequenceNumber = 0; }
};

#endif // TELEMETRY_PUBLISHER_H
