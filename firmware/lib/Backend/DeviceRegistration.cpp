#include "DeviceRegistration.h"
#include <ArduinoJson.h>
#include <string.h>

DeviceRegistration::DeviceRegistration(const char* deviceId, const char* fwVer, const char* hwRev) {
    strncpy(_deviceId, deviceId ? deviceId : "UNKNOWN", sizeof(_deviceId) - 1);
    _deviceId[sizeof(_deviceId) - 1] = '\0';

    strncpy(_firmwareVersion, fwVer ? fwVer : "3.9.0", sizeof(_firmwareVersion) - 1);
    _firmwareVersion[sizeof(_firmwareVersion) - 1] = '\0';

    strncpy(_hardwareRevision, hwRev ? hwRev : "ESP32-WROOM-32E", sizeof(_hardwareRevision) - 1);
    _hardwareRevision[sizeof(_hardwareRevision) - 1] = '\0';

    strcpy(_capabilities, "gps,rtc,temperature,salinity,ph,turbidity,dissolved_oxygen");
    _latitude = 0.0;
    _longitude = 0.0;
    _hasLocation = false;
    _status = RegistrationStatus::UNREGISTERED;
}

void DeviceRegistration::setCapabilities(const char* cap) {
    if (cap) {
        strncpy(_capabilities, cap, sizeof(_capabilities) - 1);
        _capabilities[sizeof(_capabilities) - 1] = '\0';
    }
}

void DeviceRegistration::setLocation(double lat, double lon) {
    _latitude = lat;
    _longitude = lon;
    _hasLocation = true;
}

bool DeviceRegistration::serialize(char* buffer, size_t size) const {
    StaticJsonDocument<256> doc;
    doc["device_id"] = _deviceId;
    doc["firmware_version"] = _firmwareVersion;
    doc["hardware_revision"] = _hardwareRevision;
    
    // Split capabilities into array
    JsonArray caps = doc.createNestedArray("capabilities");
    char tempCaps[128];
    strncpy(tempCaps, _capabilities, sizeof(tempCaps) - 1);
    tempCaps[sizeof(tempCaps) - 1] = '\0';
    
    char* token = strtok(tempCaps, ",");
    while (token != nullptr) {
        caps.add(token);
        token = strtok(nullptr, ",");
    }

    if (_hasLocation) {
        JsonObject loc = doc.createNestedObject("location");
        loc["latitude"] = _latitude;
        loc["longitude"] = _longitude;
    }

    const char* statusStr = "UNREGISTERED";
    if (_status == RegistrationStatus::REGISTERED) statusStr = "REGISTERED";
    else if (_status == RegistrationStatus::REGISTERING) statusStr = "REGISTERING";
    else if (_status == RegistrationStatus::FAILED) statusStr = "FAILED";
    doc["registration_status"] = statusStr;

    size_t written = serializeJson(doc, buffer, size);
    return (written > 0 && written < size);
}
