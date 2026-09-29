/**
 * @file main_esp32_cam.cpp
 * @brief Isolated Physical Firmware Module for ESP32-CAM (AI-Thinker OV2640).
 * 
 * Milestone V4.8.3 Hardware-Ready SNTP Time Synchronization Specification.
 * Responsibilities: CAPTURE optical frame -> JPEG ENCODE -> ATTACH SNTP TIMESTAMP & SYNC METADATA -> TRANSMIT over MQTT.
 * 
 * Hardware Boundary Rule: Contains ZERO sensor ML, ZERO AIS anomaly scanning,
 * ZERO PyTorch inference, and ZERO actuator control logic.
 */

#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include "esp_camera.h"
#include <time.h>

// -----------------------------------------------------------------
// CAMERA PIN DEFINITIONS (AI-Thinker ESP32-CAM Module Defaults)
// -----------------------------------------------------------------
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27

#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

// -----------------------------------------------------------------
// CONFIGURATION & CONSTANTS
// -----------------------------------------------------------------
const char* WIFI_SSID = "AquaNet_Freshwater_AP";
const char* WIFI_PASS = "aquasentinel_secure";
const char* MQTT_BROKER = "192.168.1.100";
const int   MQTT_PORT = 1883;

const char* NTP_SERVER1 = "pool.ntp.org";
const char* NTP_SERVER2 = "time.nist.gov";

const char* DEVICE_ID = "AQUA_FRESH_001";
const char* CAMERA_TOPIC = "aquatic/AQUA_FRESH_001/camera/raw";
const unsigned long CAPTURE_INTERVAL_MS = 10000; // 0.1 FPS (1 frame / 10 sec)

WiFiClient espClient;
PubSubClient mqttClient(espClient);
unsigned long lastCaptureTime = 0;
unsigned long frameCounter = 0;

// SNTP Time Synchronization State
String timeSyncStatus = "UNSYNCED";
String clockSource = "UNSYNCED_BOOT_TICK";

// Base64 encoding helper function
static const char b64_chars[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
String base64Encode(const uint8_t* data, size_t length) {
    String result = "";
    result.reserve(((length + 2) / 3) * 4);

    for (size_t i = 0; i < length; i += 3) {
        uint32_t b = (data[i] << 16) | ((i + 1 < length ? data[i + 1] : 0) << 8) | (i + 2 < length ? data[i + 2] : 0);
        result += b64_chars[(b >> 18) & 0x3F];
        result += b64_chars[(b >> 12) & 0x3F];
        result += (i + 1 < length) ? b64_chars[(b >> 6) & 0x3F] : '=';
        result += (i + 2 < length) ? b64_chars[b & 0x3F] : '=';
    }
    return result;
}

bool initCameraHardware() {
    camera_config_t config;
    config.ledc_channel = LEDC_CHANNEL_0;
    config.ledc_timer = LEDC_TIMER_0;
    config.pin_d0 = Y2_GPIO_NUM;
    config.pin_d1 = Y3_GPIO_NUM;
    config.pin_d2 = Y4_GPIO_NUM;
    config.pin_d3 = Y5_GPIO_NUM;
    config.pin_d4 = Y6_GPIO_NUM;
    config.pin_d5 = Y7_GPIO_NUM;
    config.pin_d6 = Y8_GPIO_NUM;
    config.pin_d7 = Y9_GPIO_NUM;
    config.pin_xclk = XCLK_GPIO_NUM;
    config.pin_pclk = PCLK_GPIO_NUM;
    config.pin_vsync = VSYNC_GPIO_NUM;
    config.pin_href = HREF_GPIO_NUM;
    config.pin_sscb_sda = SIOD_GPIO_NUM;
    config.pin_sscb_scl = SIOC_GPIO_NUM;
    config.pin_pwdn = PWDN_GPIO_NUM;
    config.pin_reset = RESET_GPIO_NUM;
    config.xclk_freq_hz = 20000000;
    config.pixel_format = PIXFORMAT_JPEG;

    // Use 224x224 resolution for model native input
    config.frame_size = FRAMESIZE_224X224;
    config.jpeg_quality = 12; // Quality range [10..63]
    config.fb_count = 2;

    esp_err_t err = esp_camera_init(&config);
    if (err != ESP_OK) {
        Serial.printf("[ESP32-CAM] ERROR: Camera initialization failed with code 0x%x\n", err);
        return false;
    }
    Serial.println("[ESP32-CAM] Camera OV2640 Hardware Initialized Successfully.");
    return true;
}

void syncNTPSimeout(unsigned long timeoutMs = 5000) {
    Serial.println("[ESP32-CAM] Initializing SNTP Time Synchronization...");
    configTime(0, 0, NTP_SERVER1, NTP_SERVER2);

    struct tm timeinfo;
    unsigned long startMs = millis();
    while ((millis() - startMs) < timeoutMs) {
        if (getLocalTime(&timeinfo, 10)) {
            if (timeinfo.tm_year > (2020 - 1900)) {
                timeSyncStatus = "SYNCED";
                clockSource = "NTP";
                Serial.println("[ESP32-CAM] SNTP Time Synchronization PASSED. Clock Status: SYNCED");
                return;
            }
        }
        delay(100);
    }

    timeSyncStatus = "UNSYNCED";
    clockSource = "UNSYNCED_BOOT_TICK";
    Serial.println("[ESP32-CAM] WARNING: SNTP Synchronization Timed Out. Clock Status: UNSYNCED");
}

void connectWiFi() {
    Serial.print("[ESP32-CAM] Connecting to Wi-Fi: ");
    Serial.println(WIFI_SSID);
    WiFi.begin(WIFI_SSID, WIFI_PASS);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println("\n[ESP32-CAM] Wi-Fi Connected. IP: " + WiFi.localIP().toString());
    
    // Trigger SNTP sync attempt after Wi-Fi establishes
    syncNTPSimeout(5000);
}

void connectMQTT() {
    mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
    while (!mqttClient.connected()) {
        Serial.print("[ESP32-CAM] Connecting to MQTT Broker...");
        if (mqttClient.connect("ESP32_CAM_CLIENT")) {
            Serial.println(" Connected.");
        } else {
            Serial.printf(" Failed, rc=%d. Retrying in 5 seconds...\n", mqttClient.state());
            delay(5000);
        }
    }
}

String getCaptureIsoTimestamp() {
    struct tm timeinfo;
    if (timeSyncStatus == "SYNCED" && getLocalTime(&timeinfo, 10)) {
        char buf[32];
        strftime(buf, sizeof(buf), "%Y-%m-%dT%H:%M:%SZ", &timeinfo);
        return String(buf);
    }
    // Explicit boot-tick string for unsynchronized state
    unsigned long uptimeSec = millis() / 1000;
    return "1970-01-01T00:00:" + String(uptimeSec < 10 ? "0" : "") + String(uptimeSec) + "Z";
}

void captureAndTransmitFrame() {
    camera_fb_t* fb = esp_camera_fb_get();
    if (!fb) {
        Serial.println("[ESP32-CAM] ERROR: Camera Frame Capture Failed!");
        return;
    }

    frameCounter++;
    String frameId = "frame_cam_" + String(frameCounter);
    String captureTimestamp = getCaptureIsoTimestamp();

    // Base64 encode raw JPEG byte buffer
    String imageB64 = base64Encode(fb->buf, fb->len);

    // Build JSON Message matching V4.8.3 CameraMessageContract (Schema 1.1)
    StaticJsonDocument<2048> doc;
    doc["schema_version"] = "1.1";
    doc["device_id"] = DEVICE_ID;
    doc["frame_id"] = frameId;
    doc["timestamp"] = captureTimestamp;
    doc["capture_timestamp"] = captureTimestamp;
    doc["time_sync_status"] = timeSyncStatus;
    doc["clock_source"] = clockSource;
    doc["width"] = fb->width;
    doc["height"] = fb->height;
    doc["channels"] = 3;
    doc["format"] = "JPEG";
    doc["status"] = "OK";
    doc["quality_valid"] = true;
    doc["image_b64"] = imageB64;

    JsonObject meta = doc.createNestedObject("metadata");
    meta["hardware"] = "ESP32-CAM-OV2640";
    meta["payload_bytes"] = fb->len;
    meta["capture_interval_sec"] = 10.0;

    String jsonBuffer;
    serializeJson(doc, jsonBuffer);

    // Publish frame JSON payload over MQTT
    if (mqttClient.publish(CAMERA_TOPIC, jsonBuffer.c_str())) {
        Serial.printf("[ESP32-CAM] Published Frame #%lu (%u bytes) [%s] to topic %s\n", 
                      frameCounter, fb->len, timeSyncStatus.c_str(), CAMERA_TOPIC);
    } else {
        Serial.println("[ESP32-CAM] ERROR: MQTT Publish Failed!");
    }

    // Return frame buffer to camera driver
    esp_camera_fb_return(fb);
}

void setup() {
    Serial.begin(115200);
    Serial.println("[ESP32-CAM] Starting Physical Camera Firmware Node...");

    if (!initCameraHardware()) {
        Serial.println("[ESP32-CAM] FATAL: System halting due to camera init error.");
        while (true) { delay(1000); }
    }

    connectWiFi();
    connectMQTT();
}

void loop() {
    if (!mqttClient.connected()) {
        connectMQTT();
    }
    mqttClient.loop();

    unsigned long now = millis();
    if (now - lastCaptureTime >= CAPTURE_INTERVAL_MS) {
        lastCaptureTime = now;
        captureAndTransmitFrame();
    }
}
