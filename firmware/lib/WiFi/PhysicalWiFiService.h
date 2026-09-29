#ifndef PHYSICAL_WIFI_SERVICE_H
#define PHYSICAL_WIFI_SERVICE_H

#include "IWiFiService.h"
#include <WiFi.h>

class PhysicalWiFiService : public IWiFiService {
private:
    char _ip[16];
    char _mac[18];
public:
    PhysicalWiFiService();
    bool begin(const char* ssid, const char* password, const char* hostname) override;
    void disconnect() override;
    WiFiState getStatus() override;
    int getRSSI() override;
    const char* getIPAddress() override;
    const char* getMACAddress() override;
    void update() override;
};

#endif
