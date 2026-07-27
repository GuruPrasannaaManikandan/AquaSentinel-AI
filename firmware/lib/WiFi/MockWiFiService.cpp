#include "MockWiFiService.h"
#include <string.h>
#include <Arduino.h>

MockWiFiService::MockWiFiService() : _status(WiFiState::DISCONNECTED), _connectingTimeStart(0), _rssi(0) {
    strcpy(_ip, "0.0.0.0");
    strcpy(_mac, "AA:BB:CC:11:22:33");
}

bool MockWiFiService::begin(const char* ssid, const char* password, const char* hostname) {
    if (_status == WiFiState::CONNECTED) return true;

    Serial.print("[MOCK-WIFI] Scanning and connecting to SSID: ");
    Serial.println(ssid);
    _status = WiFiState::CONNECTING;
    _connectingTimeStart = millis();
    return true;
}

void MockWiFiService::disconnect() {
    Serial.println("[MOCK-WIFI] Disconnecting link...");
    _status = WiFiState::DISCONNECTED;
    strcpy(_ip, "0.0.0.0");
    _rssi = 0;
}

void MockWiFiService::update() {
    unsigned long nowMs = millis();

    if (_status == WiFiState::CONNECTING) {
        // After 1 second, transition to authenticating
        if (nowMs - _connectingTimeStart >= 1000) {
            _status = WiFiState::AUTHENTICATING;
            Serial.println("[MOCK-WIFI] SSID found. Authenticating (WPA2)...");
        }
    } else if (_status == WiFiState::AUTHENTICATING) {
        // After another 1 second, transition to DHCP
        if (nowMs - _connectingTimeStart >= 2000) {
            _status = WiFiState::DHCP;
            Serial.println("[MOCK-WIFI] Authenticated. Acquiring IP via DHCP...");
        }
    } else if (_status == WiFiState::DHCP) {
        // After another 1 second, transition to connected
        if (nowMs - _connectingTimeStart >= 3000) {
            _status = WiFiState::CONNECTED;
            strcpy(_ip, "192.168.4.150");
            _rssi = -62;
            Serial.println("[MOCK-WIFI] DHCP success. Assigned IP: 192.168.4.150");
        }
    } else if (_status == WiFiState::CONNECTED) {
        int delta = random(-3, 3);
        _rssi = -62 + delta;
    }
}
