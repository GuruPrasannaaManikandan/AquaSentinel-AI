#ifndef DEVICE_SHADOW_H
#define DEVICE_SHADOW_H

#include "config/TelemetryData.h"

/**
 * @brief ShadowState struct maintaining local state cache.
 */
struct ShadowState {
    int currentState;
    char sensorStatus[16];
    char networkStatus[32];
    char firmwareVersion[16];
    char configurationVersion[16];
    
    // Last Telemetry cached values
    float lastTemperature;
    float lastPH;
    float lastDO;
    float lastTurbidity;
    float lastSalinity;
    
    // Last Alert cached value
    char lastAlert[64];
};

class DeviceShadow {
private:
    ShadowState _shadow;

public:
    DeviceShadow();
    ~DeviceShadow() {}

    void updateFSMState(int state);
    void updateSensorStatus(const char* status);
    void updateNetworkStatus(const char* status);
    void updateVersions(const char* fw, const char* cfg);
    void updateTelemetry(const TelemetryData& data);
    void updateLastAlert(const char* alert);

    const ShadowState& getShadow() const { return _shadow; }
};

#endif // DEVICE_SHADOW_H
