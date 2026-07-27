#ifndef IWIFI_SERVICE_H
#define IWIFI_SERVICE_H

#include "WiFiState.h"

/**
 * @brief Abstract interface representing standard Wi-Fi network services.
 * Decouples logic from physical Espressif Wi-Fi stack.
 */
class IWiFiService {
public:
    virtual ~IWiFiService() {}

    /**
     * @brief Configure and initiate physical connections.
     */
    virtual bool begin(const char* ssid, const char* password, const char* hostname) = 0;
    
    /**
     * @brief Closes connection link.
     */
    virtual void disconnect() = 0;
    
    virtual WiFiState getStatus() = 0;
    virtual int getRSSI() = 0;
    virtual const char* getIPAddress() = 0;
    virtual const char* getMACAddress() = 0;
    
    /**
     * @brief Periodic update called inside WiFiManager scans.
     */
    virtual void update() = 0;
};

#endif
