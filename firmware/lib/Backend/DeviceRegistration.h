#ifndef DEVICE_REGISTRATION_H
#define DEVICE_REGISTRATION_H

#include <stddef.h>

/**
 * @brief RegistrationStatus enum representing the current registration state.
 */
enum class RegistrationStatus {
    UNREGISTERED,
    REGISTERING,
    REGISTERED,
    FAILED
};

class DeviceRegistration {
private:
    char _deviceId[32];
    char _firmwareVersion[16];
    char _hardwareRevision[16];
    char _capabilities[128];
    double _latitude;
    double _longitude;
    bool _hasLocation;
    RegistrationStatus _status;

public:
    DeviceRegistration(const char* deviceId, const char* fwVer = "3.9.0", const char* hwRev = "ESP32-WROOM-32E");
    ~DeviceRegistration() {}

    void setCapabilities(const char* cap);
    void setLocation(double lat, double lon);
    void setStatus(RegistrationStatus status) { _status = status; }

    const char* getDeviceId() const { return _deviceId; }
    const char* getFirmwareVersion() const { return _firmwareVersion; }
    const char* getHardwareRevision() const { return _hardwareRevision; }
    const char* getCapabilities() const { return _capabilities; }
    bool getHasLocation() const { return _hasLocation; }
    double getLatitude() const { return _latitude; }
    double getLongitude() const { return _longitude; }
    RegistrationStatus getStatus() const { return _status; }

    /**
     * @brief Serialize the registration payload to JSON.
     */
    bool serialize(char* buffer, size_t size) const;
};

#endif // DEVICE_REGISTRATION_H
