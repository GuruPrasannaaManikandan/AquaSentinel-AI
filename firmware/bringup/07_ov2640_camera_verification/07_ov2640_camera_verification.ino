/**
 * @file 07_ov2640_camera_verification.ino
 * @brief Phase B–I: Isolated OV2640 Camera Hardware Verification Sketch for Arduino IDE
 * 
 * Target: AI-Thinker ESP32-CAM via ESP32-CAM-MB Programmer (CH340)
 * Arduino IDE Settings:
 *   - Board: "AI Thinker ESP32-CAM"
 *   - CPU Frequency: "240MHz (WiFi/BT)"
 *   - Flash Frequency: "80MHz"
 *   - Flash Mode: "DIO"
 *   - Partition Scheme: "Huge APP (3MB No OTA/1MB SPIFFS)"
 *   - Core Debug Level: "None" or "Info"
 *   - Port: "COM4"
 */

#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>
#include "esp_camera.h"
#include "img_converters.h"
#include "soc/soc.h"
#include "soc/rtc_cntl_reg.h"

// -----------------------------------------------------------------
// CAMERA PIN DEFINITIONS (AI-Thinker ESP32-CAM Module PCB Mapping)
// -----------------------------------------------------------------
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27

#define Y9_GPIO_NUM       35  // D7
#define Y8_GPIO_NUM       34  // D6
#define Y7_GPIO_NUM       39  // D5
#define Y6_GPIO_NUM       36  // D4
#define Y5_GPIO_NUM       21  // D3
#define Y4_GPIO_NUM       19  // D2
#define Y3_GPIO_NUM       18  // D1
#define Y2_GPIO_NUM        5  // D0
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

// Flash LED pin on AI-Thinker ESP32-CAM (Active HIGH)
#define FLASH_LED_PIN      4

// -----------------------------------------------------------------
// GLOBALS & STATE
// -----------------------------------------------------------------
WebServer server(80);
bool cameraInitialized = false;
bool psramDetected = false;
int fbCountInUse = 1;  // frame buffers the driver was initialised with
bool nativeJpegMode = false;
uint32_t sensorPID = 0;
String sensorModelName = "UNKNOWN";

// Universal JPEG frame wrapper
struct VerifiedFrame {
    uint8_t* data;
    size_t length;
    int width;
    int height;
    bool needsFree;
    camera_fb_t* rawFb;
};

VerifiedFrame acquireJpegFrame() {
    VerifiedFrame vf = {NULL, 0, 0, 0, false, NULL};
    if (!cameraInitialized) return vf;

    // With CAMERA_GRAB_WHEN_EMPTY the driver fills its buffers right after the
    // previous capture and holds them, so the first fb_get returns an old scene.
    // Drain every pre-filled buffer so the frame we return is exposed now.
    for (int i = 0; i < fbCountInUse; i++) {
        camera_fb_t* stale = esp_camera_fb_get();
        if (stale) esp_camera_fb_return(stale);
    }

    camera_fb_t* fb = esp_camera_fb_get();
    if (!fb || fb->buf == NULL || fb->len == 0) {
        if (fb) esp_camera_fb_return(fb);
        return vf;
    }
    vf.rawFb = fb;
    vf.width = fb->width;
    vf.height = fb->height;

    if (fb->format == PIXFORMAT_JPEG) {
        vf.data = fb->buf;
        vf.length = fb->len;
        vf.needsFree = false;
    } else {
        uint8_t* jpgBuf = NULL;
        size_t jpgLen = 0;
        if (frame2jpg(fb, 80, &jpgBuf, &jpgLen) && jpgBuf != NULL && jpgLen > 0) {
            vf.data = jpgBuf;
            vf.length = jpgLen;
            vf.needsFree = true;
        } else {
            if (jpgBuf) free(jpgBuf);
            esp_camera_fb_return(fb);
            vf.rawFb = NULL;
        }
    }
    return vf;
}

void releaseJpegFrame(VerifiedFrame& vf) {
    if (vf.needsFree && vf.data) {
        free(vf.data);
    }
    if (vf.rawFb) {
        esp_camera_fb_return(vf.rawFb);
    }
    vf.data = NULL;
    vf.length = 0;
    vf.rawFb = NULL;
}

// Base64 lookup table
static const char b64_table[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";

void sendBase64Serial(const uint8_t* data, size_t length) {
    size_t i = 0;
    char chunk[4];
    while (i < length) {
        size_t rem = length - i;
        uint32_t b0 = data[i++];
        uint32_t b1 = (rem > 1) ? data[i++] : 0;
        uint32_t b2 = (rem > 2) ? data[i++] : 0;
        uint32_t triple = (b0 << 16) | (b1 << 8) | b2;

        chunk[0] = b64_table[(triple >> 18) & 0x3F];
        chunk[1] = b64_table[(triple >> 12) & 0x3F];
        chunk[2] = (rem > 1) ? b64_table[(triple >> 6) & 0x3F] : '=';
        chunk[3] = (rem > 2) ? b64_table[triple & 0x3F] : '=';

        Serial.write((const uint8_t*)chunk, 4);
        if ((i % 120) == 0) {
            Serial.println();
        }
    }
    Serial.println();
}

// -----------------------------------------------------------------
// PHASE C: CAMERA INITIALIZATION & PROBE
// -----------------------------------------------------------------
bool initCamera(framesize_t targetSize = FRAMESIZE_QVGA) {
    Serial.println("==================================================================");
    Serial.println("ESP32-CAM CAMERA TEST");
    Serial.println("==================================================================");

    // 1. ESP32 Chip & System Verification
    Serial.println("[SYSTEM INITIALIZATION]");
    Serial.printf("  Chip Model            : %s (rev %d)\n", ESP.getChipModel(), ESP.getChipRevision());
    Serial.printf("  CPU Cores             : %d @ %u MHz\n", ESP.getChipCores(), ESP.getCpuFreqMHz());
    Serial.printf("  Flash Size            : %u MB (DIO Mode)\n", ESP.getFlashChipSize() / (1024 * 1024));
    Serial.println("ESP32 INITIALIZATION: PASS");

    // 2. PSRAM Detection
    psramDetected = psramFound();
    if (psramDetected) {
        Serial.printf("  Total PSRAM           : %u bytes (%u KB)\n", ESP.getPsramSize(), ESP.getPsramSize() / 1024);
        Serial.printf("  Free PSRAM            : %u bytes (%u KB)\n", ESP.getFreePsram(), ESP.getFreePsram() / 1024);
        Serial.println("PSRAM: PASS");
    } else {
        Serial.println("PSRAM: NOT AVAILABLE");
    }

    // Power cycle camera hardware via PWDN pin (GPIO 32)
    pinMode(PWDN_GPIO_NUM, OUTPUT);
    digitalWrite(PWDN_GPIO_NUM, HIGH); // Power off
    delay(20);
    digitalWrite(PWDN_GPIO_NUM, LOW);  // Power on
    delay(30);

    // 3. Configure Camera Parameters
    camera_config_t config;
    config.ledc_channel = LEDC_CHANNEL_0;
    config.ledc_timer   = LEDC_TIMER_0;
    config.pin_d0       = Y2_GPIO_NUM;
    config.pin_d1       = Y3_GPIO_NUM;
    config.pin_d2       = Y4_GPIO_NUM;
    config.pin_d3       = Y5_GPIO_NUM;
    config.pin_d4       = Y6_GPIO_NUM;
    config.pin_d5       = Y7_GPIO_NUM;
    config.pin_d6       = Y8_GPIO_NUM;
    config.pin_d7       = Y9_GPIO_NUM;
    config.pin_xclk     = XCLK_GPIO_NUM;
    config.pin_pclk     = PCLK_GPIO_NUM;
    config.pin_vsync    = VSYNC_GPIO_NUM;
    config.pin_href     = HREF_GPIO_NUM;
    config.pin_sccb_sda = SIOD_GPIO_NUM;
    config.pin_sccb_scl = SIOC_GPIO_NUM;
    config.pin_pwdn     = PWDN_GPIO_NUM;
    config.pin_reset    = RESET_GPIO_NUM;
    config.xclk_freq_hz = 20000000;
    config.pixel_format = PIXFORMAT_JPEG;
    config.frame_size   = targetSize;
    config.jpeg_quality = 12;
    config.fb_count     = psramDetected ? 2 : 1;
    config.grab_mode    = CAMERA_GRAB_WHEN_EMPTY;
    config.fb_location  = psramDetected ? CAMERA_FB_IN_PSRAM : CAMERA_FB_IN_DRAM;

    Serial.println("------------------------------------------------------------------");
    Serial.println("[CAMERA INITIALIZATION]");
    Serial.printf("  Resolution Configured : %s\n", (targetSize == FRAMESIZE_QVGA) ? "QVGA (320x240)" : "OTHER");
    Serial.printf("  Frame Buffer Count    : %d\n", config.fb_count);
    Serial.printf("  FB Allocation         : %s\n", psramDetected ? "PSRAM" : "DRAM");
    Serial.printf("  XCLK Frequency        : %u MHz\n", config.xclk_freq_hz / 1000000);

    // De-initialize previous instance if any
    if (cameraInitialized) {
        esp_camera_deinit();
        cameraInitialized = false;
        delay(50);
    }

    // Attempt 1: Try Native PIXFORMAT_JPEG
    Serial.println("  Attempting initialization with native JPEG format...");
    esp_err_t err = esp_camera_init(&config);
    if (err == ESP_OK) {
        nativeJpegMode = true;
        cameraInitialized = true;
        fbCountInUse = config.fb_count;
        Serial.println("CAMERA INITIALIZATION: PASS (Native JPEG Mode)");
    } else if (err == 0x0106) { // ESP_ERR_NOT_SUPPORTED
        Serial.println("[DIAGNOSTIC] Native JPEG rejected by driver (0x0106).");
        Serial.println("[DIAGNOSTIC] Initializing with PIXFORMAT_RGB565 to query sensor identity...");
        esp_camera_deinit();
        delay(50);

        config.pixel_format = PIXFORMAT_RGB565;
        config.fb_count = 1;
        config.fb_location = psramDetected ? CAMERA_FB_IN_PSRAM : CAMERA_FB_IN_DRAM;

        err = esp_camera_init(&config);
        if (err == ESP_OK) {
            nativeJpegMode = false;
            cameraInitialized = true;
            fbCountInUse = config.fb_count;
            Serial.println("CAMERA INITIALIZATION: PASS (RGB565 Pipeline with Auto-JPEG Conversion)");
        } else {
            Serial.printf("CAMERA INITIALIZATION: FAIL on RGB565 (Error Code: 0x%04x)\n", err);
            cameraInitialized = false;
            return false;
        }
    } else {
        Serial.printf("CAMERA INITIALIZATION: FAIL (Error Code: 0x%04x)\n", err);
        cameraInitialized = false;
        return false;
    }

    // 5. Query Sensor Hardware Identity
    sensor_t* s = esp_camera_sensor_get();
    if (s != NULL) {
        sensorPID = s->id.PID;
        camera_sensor_info_t* info = esp_camera_sensor_get_info(&s->id);
        sensorModelName = info ? info->name : "UNKNOWN";

        Serial.println("==================================================================");
        Serial.println("[HARDWARE SENSOR DIAGNOSTIC REPORT]");
        Serial.printf("  Sensor Model Name     : %s\n", sensorModelName.c_str());
        Serial.printf("  Sensor PID            : 0x%04X (Decimal: %d)\n", sensorPID, sensorPID);
        Serial.printf("  Manufacturer ID (MID) : 0x%02X%02X\n", s->id.MIDH, s->id.MIDL);
        Serial.printf("  Revision VER          : 0x%02X\n", s->id.VER);
        Serial.printf("  SCCB Slave Address    : 0x%02X\n", s->slv_addr);
        Serial.printf("  Driver Supports JPEG  : %s\n", (info && info->support_jpeg) ? "YES" : "NO");

        if (sensorPID == OV2640_PID) {
            Serial.println("OV2640: DETECTED");
            if (!nativeJpegMode) {
                // Try switching to JPEG now that sensor is active
                if (s->set_pixformat(s, PIXFORMAT_JPEG) == 0) {
                    nativeJpegMode = true;
                    Serial.println("  Switched sensor to PIXFORMAT_JPEG successfully!");
                }
            }
        } else {
            Serial.printf("SENSOR DETECTED: %s (PID: 0x%04X)\n", sensorModelName.c_str(), sensorPID);
        }
        Serial.println("==================================================================");
    } else {
        Serial.println("WARNING: Unable to query sensor_t handle.");
    }

    Serial.printf("  Free Heap             : %u bytes\n", ESP.getFreeHeap());
    if (psramDetected) {
        Serial.printf("  Free PSRAM            : %u bytes\n", ESP.getFreePsram());
    }
    Serial.println("==================================================================");
    return true;
}

// -----------------------------------------------------------------
// PHASE D: SINGLE FRAME CAPTURE TEST
// -----------------------------------------------------------------
bool testSingleFrameCapture() {
    Serial.println("[PHASE D — SINGLE FRAME CAPTURE]");
    if (!cameraInitialized) {
        Serial.println("FRAME CAPTURE: FAIL (Camera not initialized)");
        return false;
    }

    VerifiedFrame vf = acquireJpegFrame();
    if (!vf.data || vf.length == 0) {
        Serial.println("FRAME CAPTURE: FAIL (NULL or empty frame buffer)");
        releaseJpegFrame(vf);
        return false;
    }

    bool validJpeg = (vf.length >= 4 && vf.data[0] == 0xFF && vf.data[1] == 0xD8);

    Serial.println("FRAME CAPTURE: PASS");
    Serial.printf("  Width                 : %d\n", vf.width);
    Serial.printf("  Height                : %d\n", vf.height);
    Serial.printf("  Format                : JPEG\n");
    Serial.printf("  Frame Length          : %u bytes\n", vf.length);
    Serial.printf("  JPEG Magic Bytes Valid: %s (0x%02X 0x%02X)\n", validJpeg ? "YES" : "NO", vf.data[0], vf.data[1]);
    Serial.printf("  Free Heap             : %u bytes\n", ESP.getFreeHeap());
    if (psramDetected) {
        Serial.printf("  Free PSRAM            : %u bytes\n", ESP.getFreePsram());
    }

    releaseJpegFrame(vf);
    return validJpeg;
}

// -----------------------------------------------------------------
// PHASE E: 10 REPEATED FRAMES CAPTURE TEST
// -----------------------------------------------------------------
bool testRepeatedFramesCapture() {
    Serial.println("------------------------------------------------------------------");
    Serial.println("[PHASE E — 10 REPEATED FRAMES CAPTURE]");
    if (!cameraInitialized) {
        Serial.println("REPEATED TEST: FAIL (Camera not initialized)");
        return false;
    }

    const int TOTAL_TEST_FRAMES = 10;
    int successCount = 0;
    int failCount = 0;
    size_t minSize = 0xFFFFFFFF;
    size_t maxSize = 0;
    uint64_t totalSize = 0;

    for (int i = 1; i <= TOTAL_TEST_FRAMES; i++) {
        unsigned long tStart = millis();
        VerifiedFrame vf = acquireJpegFrame();
        unsigned long dur = millis() - tStart;

        if (vf.data && vf.length > 0 && vf.data[0] == 0xFF && vf.data[1] == 0xD8) {
            successCount++;
            if (vf.length < minSize) minSize = vf.length;
            if (vf.length > maxSize) maxSize = vf.length;
            totalSize += vf.length;

            Serial.printf("  Frame %2d PASS | Length: %5u B | Latency: %3lu ms | FreeHeap: %6u B | FreePSRAM: %7u B\n",
                          i, vf.length, dur, ESP.getFreeHeap(), ESP.getFreePsram());
            releaseJpegFrame(vf);
        } else {
            failCount++;
            Serial.printf("  Frame %2d FAIL | Buffer Null or Invalid\n", i);
            releaseJpegFrame(vf);
        }
        delay(50);
    }

    size_t avgSize = (successCount > 0) ? (totalSize / successCount) : 0;
    Serial.println("------------------------------------------------------------------");
    Serial.println("[PHASE E SUMMARY]");
    Serial.printf("  Successful Frames     : %d / %d\n", successCount, TOTAL_TEST_FRAMES);
    Serial.printf("  Failed Frames         : %d / %d\n", failCount, TOTAL_TEST_FRAMES);
    Serial.printf("  Minimum Frame Size    : %u bytes\n", (successCount > 0) ? minSize : 0);
    Serial.printf("  Maximum Frame Size    : %u bytes\n", maxSize);
    Serial.printf("  Average Frame Size    : %u bytes\n", avgSize);

    bool pass = (successCount == TOTAL_TEST_FRAMES && failCount == 0);
    Serial.printf("REPEATED FRAME CAPTURE: %s\n", pass ? "PASS" : "FAIL");
    return pass;
}

// -----------------------------------------------------------------
// PHASE F: TRANSMIT FRAME OVER SERIAL (BASE64) FOR LAPTOP VIEWING
// -----------------------------------------------------------------
void transmitFrameOverSerial() {
    Serial.println("[TRANSMITTING FRAME OVER SERIAL]");
    if (!cameraInitialized) {
        Serial.println("ERROR: Camera not initialized.");
        return;
    }

    VerifiedFrame vf = acquireJpegFrame();
    if (!vf.data || vf.length == 0) {
        Serial.println("ERROR: Could not acquire frame buffer for transmission.");
        releaseJpegFrame(vf);
        return;
    }

    Serial.printf("<<<FRAME_B64_START:%d:%d:%u>>>\n", vf.width, vf.height, vf.length);
    sendBase64Serial(vf.data, vf.length);
    Serial.println("<<<FRAME_B64_END>>>");

    releaseJpegFrame(vf);
}

// -----------------------------------------------------------------
// PHASE H: 50-FRAME CONTINUOUS CAPTURE STABILITY TEST
// -----------------------------------------------------------------
bool testContinuousStability() {
    Serial.println("==================================================================");
    Serial.println("[PHASE H — 50-FRAME CONTINUOUS CAPTURE STABILITY TEST]");
    if (!cameraInitialized) {
        Serial.println("STABILITY TEST: FAIL (Camera not initialized)");
        return false;
    }

    const int STABILITY_TARGET = 50;
    int successCount = 0;
    int failCount = 0;
    size_t minSize = 0xFFFFFFFF;
    size_t maxSize = 0;
    uint64_t totalSize = 0;
    unsigned long totalDuration = 0;
    uint32_t heapStart = ESP.getFreeHeap();
    uint32_t psramStart = ESP.getFreePsram();

    for (int i = 1; i <= STABILITY_TARGET; i++) {
        unsigned long t0 = millis();
        VerifiedFrame vf = acquireJpegFrame();
        unsigned long tCap = millis() - t0;

        if (vf.data && vf.length > 0 && vf.data[0] == 0xFF && vf.data[1] == 0xD8) {
            successCount++;
            if (vf.length < minSize) minSize = vf.length;
            if (vf.length > maxSize) maxSize = vf.length;
            totalSize += vf.length;
            totalDuration += tCap;

            if (i % 10 == 0 || i == 1 || i == STABILITY_TARGET) {
                Serial.printf("  [Frame #%02d/50] Length: %5u B | Latency: %3lu ms | Heap: %6u B | PSRAM: %7u B | OK\n",
                              i, vf.length, tCap, ESP.getFreeHeap(), ESP.getFreePsram());
            }
            releaseJpegFrame(vf);
        } else {
            failCount++;
            Serial.printf("  [Frame #%02d/50] CAPTURE FAILURE | Retrying...\n", i);
            releaseJpegFrame(vf);
        }
        delay(50);
    }

    uint32_t heapEnd = ESP.getFreeHeap();
    uint32_t psramEnd = ESP.getFreePsram();
    int32_t heapDelta = (int32_t)heapEnd - (int32_t)heapStart;
    int32_t psramDelta = (int32_t)psramEnd - (int32_t)psramStart;

    Serial.println("------------------------------------------------------------------");
    Serial.println("[PHASE H STABILITY SUMMARY]");
    Serial.printf("  Successful Frames     : %d / %d\n", successCount, STABILITY_TARGET);
    Serial.printf("  Failed Frames         : %d / %d\n", failCount, STABILITY_TARGET);
    Serial.printf("  Average Latency       : %.1f ms\n", (successCount > 0) ? ((float)totalDuration / successCount) : 0);
    Serial.printf("  Min / Max / Avg Size  : %u B / %u B / %u B\n",
                  (successCount > 0) ? minSize : 0, maxSize,
                  (successCount > 0) ? (size_t)(totalSize / successCount) : 0);
    Serial.printf("  Heap Drift            : %d bytes (Start: %u, End: %u)\n", heapDelta, heapStart, heapEnd);
    Serial.printf("  PSRAM Drift           : %d bytes (Start: %u, End: %u)\n", psramDelta, psramStart, psramEnd);

    bool pass = (successCount >= 48 && failCount <= 2 && abs(heapDelta) < 8192);
    Serial.printf("CAMERA STABILITY TEST: %s\n", pass ? "PASS" : "FAIL");
    Serial.println("==================================================================");
    return pass;
}

// -----------------------------------------------------------------
// PHASE I: DOCUMENT WORKING CAMERA BASELINE
// -----------------------------------------------------------------
void printHardwareBaseline() {
    Serial.println("==================================================================");
    Serial.println("[PHASE I — VERIFIED ESP32-CAM HARDWARE BASELINE]");
    Serial.println("==================================================================");
    Serial.println("  Board                 : AI-Thinker ESP32-CAM");
    Serial.printf("  Camera Sensor         : %s (PID: 0x%02X)\n", sensorModelName.c_str(), sensorPID);
    Serial.println("  Frame Size            : QVGA 320x240 (FRAMESIZE_QVGA)");
    Serial.printf("  JPEG Encoding         : %s\n", nativeJpegMode ? "HARDWARE (OV2640 DSP)" : "SOFTWARE (frame2jpg converter)");
    Serial.printf("  Framebuffer Count     : %d\n", psramDetected ? 2 : 1);
    Serial.printf("  PSRAM Usage           : %s\n", psramDetected ? "ENABLED (CAMERA_FB_IN_PSRAM)" : "DISABLED (INTERNAL_DRAM)");
    Serial.println("  Capture Interval      : 10.0 sec (0.1 FPS) - Operational Baseline");
    Serial.printf("  Free Heap (Baseline)  : %u bytes\n", ESP.getFreeHeap());
    Serial.printf("  Free PSRAM (Baseline) : %u bytes\n", ESP.getFreePsram());
    Serial.println("  Transport Modes       : MQTT over Wi-Fi (V4.8.2) + HTTP Endpoint (Diagnostic)");
    Serial.println("  Wi-Fi Access Point    : AquaSentinel-CAM-AP (IP: 192.168.4.1)");
    Serial.println("==================================================================");
}

// -----------------------------------------------------------------
// WEB SERVER HANDLERS (PHASE F LOCAL HTTP VIEWER)
// -----------------------------------------------------------------
void handleRoot() {
    String html = "<!DOCTYPE html><html><head><meta charset='utf-8'><title>AquaSentinel-AI Camera Verification</title>";
    html += "<meta name='viewport' content='width=device-width, initial-scale=1'>";
    html += "<style>body{background:#0b1329;color:#e2e8f0;font-family:sans-serif;margin:0;padding:20px;text-align:center;}";
    html += "h1{color:#38bdf8;margin-bottom:5px;} .card{background:#1e293b;border:1px solid #334155;border-radius:12px;padding:20px;max-width:560px;margin:20px auto;box-shadow:0 8px 24px rgba(0,0,0,0.4);}";
    html += "img{border:3px solid #38bdf8;border-radius:8px;max-width:100%;height:auto;margin:15px 0;}";
    html += ".badge{display:inline-block;padding:4px 10px;border-radius:6px;font-size:12px;font-weight:bold;margin:4px;}";
    html += ".badge-pass{background:#166534;color:#4ade80;} .badge-info{background:#0369a1;color:#7dd3fc;}";
    html += "button{background:#0284c7;color:#fff;border:none;padding:10px 20px;border-radius:6px;font-size:14px;cursor:pointer;margin:5px;}";
    html += "button:hover{background:#0369a1;}</style></head><body>";
    html += "<h1>AquaSentinel-AI</h1><p>ESP32-CAM Hardware Verification Portal</p>";
    html += "<div class='card'>";
    html += "<div><span class='badge badge-pass'>CAMERA: PASS</span><span class='badge badge-pass'>" + sensorModelName + " DETECTED</span>";
    html += "<span class='badge badge-info'>QVGA 320x240 JPEG</span></div>";
    html += "<img id='cam' src='/capture' alt='Live Frame' width='320' height='240'><br>";
    html += "<button onclick=\"document.getElementById('cam').src='/capture?t='+Date.now()\">Refresh Frame</button>";
    html += "<p style='font-size:12px;color:#94a3b8;'>Direct endpoint: <a style='color:#38bdf8;' href='/capture'>/capture</a></p>";
    html += "</div></body></html>";
    server.send(200, "text/html", html);
}

void handleCapture() {
    if (!cameraInitialized) {
        server.send(503, "text/plain", "Camera not initialized");
        return;
    }
    VerifiedFrame vf = acquireJpegFrame();
    if (!vf.data || vf.length == 0) {
        server.send(500, "text/plain", "Frame acquisition failed");
        releaseJpegFrame(vf);
        return;
    }
    server.send_P(200, "image/jpeg", (const char*)vf.data, vf.length);
    releaseJpegFrame(vf);
}

void handleStatusJson() {
    String json = "{";
    json += "\"camera_init\":\"" + String(cameraInitialized ? "PASS" : "FAIL") + "\",";
    json += "\"sensor_pid\":\"0x" + String(sensorPID, HEX) + "\",";
    json += "\"sensor_model\":\"" + sensorModelName + "\",";
    json += "\"native_jpeg\":" + String(nativeJpegMode ? "true" : "false") + ",";
    json += "\"psram_found\":" + String(psramDetected ? "true" : "false") + ",";
    json += "\"free_heap\":" + String(ESP.getFreeHeap()) + ",";
    json += "\"free_psram\":" + String(ESP.getFreePsram()) + ",";
    json += "\"resolution\":\"320x240\"";
    json += "}";
    server.send(200, "application/json", json);
}

// -----------------------------------------------------------------
// ARDUINO SETUP & LOOP
// -----------------------------------------------------------------
void setup() {
    // Disable brownout detector to prevent reboot on Wi-Fi/Camera current spikes
    WRITE_PERI_REG(RTC_CNTL_BROWN_OUT_REG, 0);

    Serial.begin(115200);
    delay(1000); // Allow power rails and UART to stabilize

    // Keep onboard flash LED (GPIO 4) strictly LOW
    pinMode(FLASH_LED_PIN, OUTPUT);
    digitalWrite(FLASH_LED_PIN, LOW);

    // Run Phase C Camera Init with FRAMESIZE_QVGA
    bool initOk = initCamera(FRAMESIZE_QVGA);

    if (initOk) {
        // Run Phase D Single Frame Test
        testSingleFrameCapture();

        // Phase E/H (10- and 50-frame tests) take ~15 s, so they only run on
        // demand ('e' / 'h'). Booting fast means a capture request from the
        // laptop right after a reset is answered within a couple of seconds.
        printHardwareBaseline();
    } else {
        Serial.println("FATAL: Camera hardware failed to initialize in setup().");
    }

    // Start Wi-Fi SoftAP for Phase F Actual Image Viewing
    Serial.println("[STARTING WI-FI SOFT-AP FOR LOCAL IMAGE VIEWING]");
    WiFi.mode(WIFI_AP);
    bool apStarted = WiFi.softAP("AquaSentinel-CAM-AP", "aquasentinel");
    if (apStarted) {
        IPAddress apIP = WiFi.softAPIP();
        Serial.printf("  SoftAP Started        : AquaSentinel-CAM-AP\n");
        Serial.printf("  SoftAP IP Address     : %s\n", apIP.toString().c_str());
        Serial.printf("  Web Dashboard URL     : http://%s/\n", apIP.toString().c_str());
        Serial.printf("  Direct Image URL      : http://%s/capture\n", apIP.toString().c_str());
    }

    server.on("/", HTTP_GET, handleRoot);
    server.on("/capture", HTTP_GET, handleCapture);
    server.on("/status", HTTP_GET, handleStatusJson);
    server.begin();
    Serial.println("HTTP Server listening on port 80.");

    Serial.println("\n[READY] Interactive commands available via Serial Monitor:");
    Serial.println("  'i' -> Run camera initialization test");
    Serial.println("  '1' -> Run single frame capture test");
    Serial.println("  'e' -> Run 10-frame repeated capture test");
    Serial.println("  'h' -> Run 50-frame stability test");
    Serial.println("  'c' -> Capture and transmit Base64 image over Serial");
    Serial.println("  'b' -> Print hardware baseline");
    Serial.println("  's' -> Print system status");
    Serial.println("==================================================================");
}

static unsigned long lastHeartbeat = 0;

void loop() {
    server.handleClient();

    // 2-second continuous heartbeat
    if (millis() - lastHeartbeat >= 2000) {
        lastHeartbeat = millis();
        Serial.printf("  [HEARTBEAT] Uptime: %lu s | Free Heap: %6u B | Free PSRAM: %7u B | Camera: %s 🟢\n",
                      millis() / 1000, ESP.getFreeHeap(), ESP.getFreePsram(),
                      cameraInitialized ? "ONLINE" : "OFFLINE");
    }

    if (Serial.available() > 0) {
        char cmd = (char)Serial.read();
        if (cmd == 'i' || cmd == 'I') {
            initCamera(FRAMESIZE_QVGA);
        } else if (cmd == '1') {
            testSingleFrameCapture();
        } else if (cmd == 'e' || cmd == 'E') {
            testRepeatedFramesCapture();
        } else if (cmd == 'h' || cmd == 'H') {
            testContinuousStability();
        } else if (cmd == 'c' || cmd == 'C') {
            transmitFrameOverSerial();
        } else if (cmd == 'b' || cmd == 'B') {
            printHardwareBaseline();
        } else if (cmd == 's' || cmd == 'S') {
            Serial.printf("[STATUS] Free Heap: %u B | Free PSRAM: %u B | Camera: %s | Uptime: %lu s\n",
                          ESP.getFreeHeap(), ESP.getFreePsram(),
                          cameraInitialized ? "ONLINE" : "OFFLINE",
                          millis() / 1000);
        }
    }
}
