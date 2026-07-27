#ifndef MOCK_WIFI_SERVICE_H
#define MOCK_WIFI_SERVICE_H

#include "IWiFiService.h"

class MockWiFiService : public IWiFiService {
private:
    WiFiState _status;
    unsigned long _connectingTimeStart;
    char _ip[16];
    char _mac[18];
    int _rssi;

public:
    MockWiFiService();
    ~MockWiFiService() override {}

    bool begin(const char* ssid, const char* password, const char* hostname) override;
    void disconnect() override;
    WiFiState getStatus() override { return _status; }
    int getRSSI() override { return _rssi; }
    const char* getIPAddress() override { return _ip; }
    const char* getMACAddress() override { return _mac; }
    void update() override;

    // Helper to simulate connection drops
    void setStatus(WiFiState state) { _status = state; }
};

#endif
