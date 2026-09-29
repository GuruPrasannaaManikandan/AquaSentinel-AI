#include "PhysicalWiFiService.h"
#include <string.h>

PhysicalWiFiService::PhysicalWiFiService() {
    strcpy(_ip, "0.0.0.0");
    strcpy(_mac, "00:00:00:00:00:00");
}

bool PhysicalWiFiService::begin(const char* ssid, const char* password, const char* hostname) {
    if (WiFi.status() == WL_CONNECTED) return true;
    
    Serial.print("[PHYSICAL-WIFI] Connecting to SSID: ");
    Serial.println(ssid);
    WiFi.mode(WIFI_STA);
    if (hostname && strlen(hostname) > 0) {
        WiFi.setHostname(hostname);
    }
    WiFi.begin(ssid, password);
    return true;
}

void PhysicalWiFiService::disconnect() {
    Serial.println("[PHYSICAL-WIFI] Disconnecting Wi-Fi...");
    WiFi.disconnect();
    strcpy(_ip, "0.0.0.0");
}

WiFiState PhysicalWiFiService::getStatus() {
    wl_status_t status = WiFi.status();
    if (status == WL_CONNECTED) {
        static bool logged = false;
        strncpy(_ip, WiFi.localIP().toString().c_str(), sizeof(_ip) - 1);
        _ip[sizeof(_ip) - 1] = '\0';
        strncpy(_mac, WiFi.macAddress().c_str(), sizeof(_mac) - 1);
        _mac[sizeof(_mac) - 1] = '\0';
        if (!logged) {
            Serial.print("[PHYSICAL-WIFI] Wi-Fi Connected! IP: ");
            Serial.println(_ip);
            logged = true;
        }
        return WiFiState::CONNECTED;
    } else if (status == WL_DISCONNECTED || status == WL_IDLE_STATUS) {
        return WiFiState::DISCONNECTED;
    } else if (status == WL_CONNECT_FAILED || status == WL_CONNECTION_LOST) {
        return WiFiState::DISCONNECTED;
    }
    return WiFiState::CONNECTING;
}

int PhysicalWiFiService::getRSSI() {
    return WiFi.RSSI();
}

const char* PhysicalWiFiService::getIPAddress() {
    return _ip;
}

const char* PhysicalWiFiService::getMACAddress() {
    return _mac;
}

void PhysicalWiFiService::update() {
    // Espressif FreeRTOS Wi-Fi task processes asynchronous link events
}
