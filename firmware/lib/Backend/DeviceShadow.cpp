#include "DeviceShadow.h"
#include <string.h>

DeviceShadow::DeviceShadow() {
    memset(&_shadow, 0, sizeof(ShadowState));
    strcpy(_shadow.sensorStatus, "UNKNOWN");
    strcpy(_shadow.networkStatus, "DISCONNECTED");
    strcpy(_shadow.firmwareVersion, "3.9.0");
    strcpy(_shadow.configurationVersion, "1.0");
    strcpy(_shadow.lastAlert, "NONE");
    _shadow.currentState = 0; // State::BOOT
}

void DeviceShadow::updateFSMState(int state) {
    _shadow.currentState = state;
}

void DeviceShadow::updateSensorStatus(const char* status) {
    if (status) {
        strncpy(_shadow.sensorStatus, status, sizeof(_shadow.sensorStatus) - 1);
        _shadow.sensorStatus[sizeof(_shadow.sensorStatus) - 1] = '\0';
    }
}

void DeviceShadow::updateNetworkStatus(const char* status) {
    if (status) {
        strncpy(_shadow.networkStatus, status, sizeof(_shadow.networkStatus) - 1);
        _shadow.networkStatus[sizeof(_shadow.networkStatus) - 1] = '\0';
    }
}

void DeviceShadow::updateVersions(const char* fw, const char* cfg) {
    if (fw) {
        strncpy(_shadow.firmwareVersion, fw, sizeof(_shadow.firmwareVersion) - 1);
        _shadow.firmwareVersion[sizeof(_shadow.firmwareVersion) - 1] = '\0';
    }
    if (cfg) {
        strncpy(_shadow.configurationVersion, cfg, sizeof(_shadow.configurationVersion) - 1);
        _shadow.configurationVersion[sizeof(_shadow.configurationVersion) - 1] = '\0';
    }
}

void DeviceShadow::updateTelemetry(const TelemetryData& data) {
    _shadow.lastTemperature = data.temperature_c;
    _shadow.lastPH = data.ph;
    _shadow.lastDO = data.dissolved_oxygen_mg_l;
    _shadow.lastTurbidity = data.turbidity_ntu;
    _shadow.lastSalinity = data.salinity_ppt;
    updateSensorStatus(data.sensor_status);
}

void DeviceShadow::updateLastAlert(const char* alert) {
    if (alert) {
        strncpy(_shadow.lastAlert, alert, sizeof(_shadow.lastAlert) - 1);
        _shadow.lastAlert[sizeof(_shadow.lastAlert) - 1] = '\0';
    }
}
