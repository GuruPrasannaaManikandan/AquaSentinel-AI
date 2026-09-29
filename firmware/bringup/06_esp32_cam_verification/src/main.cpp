/**
 * @file main.cpp
 * @brief Phase 5: ESP32-CAM Isolated Boot & System Diagnostics
 * 
 * Target: AI-Thinker ESP32-CAM via ESP32-CAM-MB Programmer
 * Objective: Verify boot, CPU execution, serial communications, PSRAM, and heap.
 * Note: Camera sensor is NOT yet initialized in Phase 5 per protocol.
 */

#include <Arduino.h>
#include "esp_system.h"
#include "esp_spi_flash.h"
#include "esp_heap_caps.h"

// Flash LED pin on AI-Thinker ESP32-CAM is GPIO 4
#define FLASH_LED_PIN 4

const char* getResetReasonString(esp_reset_reason_t reason) {
    switch (reason) {
        case ESP_RST_POWERON:   return "Vbat Power-on Reset (ESP_RST_POWERON)";
        case ESP_RST_EXT:       return "External Reset Pin (ESP_RST_EXT)";
        case ESP_RST_SW:        return "Software Reset (ESP_RST_SW)";
        case ESP_RST_PANIC:     return "Exception / Panic Reset (ESP_RST_PANIC)";
        case ESP_RST_INT_WDT:   return "Interrupt Watchdog Reset (ESP_RST_INT_WDT)";
        case ESP_RST_TASK_WDT:  return "Task Watchdog Reset (ESP_RST_TASK_WDT)";
        case ESP_RST_WDT:       return "Other Watchdog Reset (ESP_RST_WDT)";
        case ESP_RST_DEEPSLEEP: return "Deep-sleep Wakeup (ESP_RST_DEEPSLEEP)";
        case ESP_RST_BROWNOUT:  return "Brownout Reset (ESP_RST_BROWNOUT)";
        case ESP_RST_SDIO:      return "SDIO Reset (ESP_RST_SDIO)";
        default:                return "Unknown Reset Reason";
    }
}

void printSystemDiagnostics() {
    Serial.println();
    Serial.println("==================================================================");
    Serial.println("   AquaSentinel-AI: ESP32-CAM Isolated Bring-Up Diagnostic");
    Serial.println("   PHASE 5 — FIRST FLASH / BOOT & SYSTEM VERIFICATION");
    Serial.println("==================================================================");
    
    Serial.println("[SYSTEM STATUS]");
    Serial.println("  Status                : Firmware Started Successfully");
    Serial.println("  Board Detected        : AI-Thinker ESP32-CAM");
    Serial.printf("  Reset Reason          : %s\n", getResetReasonString(esp_reset_reason()));
    
    esp_chip_info_t chip_info;
    esp_chip_info(&chip_info);
    Serial.println("------------------------------------------------------------------");
    Serial.println("[CHIP INFORMATION]");
    Serial.printf("  Model                 : ESP32 (rev %d)\n", chip_info.revision);
    Serial.printf("  CPU Cores             : %d @ %u MHz\n", chip_info.cores, getCpuFrequencyMhz());
    Serial.printf("  Silicon Features      : %s%s%s\n",
                  (chip_info.features & CHIP_FEATURE_WIFI_BGN) ? "802.11bgn Wi-Fi " : "",
                  (chip_info.features & CHIP_FEATURE_BT) ? "Bluetooth " : "",
                  (chip_info.features & CHIP_FEATURE_BLE) ? "BLE " : "");
    Serial.printf("  Internal Flash Size   : %u MB (%s mode)\n",
                  spi_flash_get_chip_size() / (1024 * 1024),
                  "DIO");

    Serial.println("------------------------------------------------------------------");
    Serial.println("[MEMORY & PSRAM STATUS]");
    bool hasPsram = psramFound();
    Serial.printf("  PSRAM Physically Found: %s\n", hasPsram ? "YES (DETECTED 🟢)" : "NO (NOT FOUND 🔴)");
    if (hasPsram) {
        Serial.printf("  Total PSRAM Size      : %u bytes (%u KB / %.2f MB)\n", 
                      ESP.getPsramSize(), ESP.getPsramSize() / 1024, ESP.getPsramSize() / (1024.0 * 1024.0));
        Serial.printf("  Free PSRAM            : %u bytes (%u KB)\n", 
                      ESP.getFreePsram(), ESP.getFreePsram() / 1024);
    } else {
        Serial.println("  WARNING: External PSRAM not recognized by ESP-IDF heap allocator!");
    }
    
    Serial.printf("  Internal Free Heap    : %u bytes (%u KB)\n", 
                  ESP.getFreeHeap(), ESP.getFreeHeap() / 1024);
    Serial.printf("  Minimum Free Heap     : %u bytes (%u KB)\n", 
                  ESP.getMinFreeHeap(), ESP.getMinFreeHeap() / 1024);
    Serial.printf("  Heap Caps 8-bit Alloc : %u bytes\n", 
                  heap_caps_get_free_size(MALLOC_CAP_8BIT));
    Serial.printf("  Heap Caps SPIRAM Alloc: %u bytes\n", 
                  heap_caps_get_free_size(MALLOC_CAP_SPIRAM));
    
    Serial.println("==================================================================");
    Serial.println("[HEARTBEAT] Beginning diagnostic loop (1 tick / sec)...");
    Serial.println("------------------------------------------------------------------");
}

void setup() {
    // Initialize UART0 at 115200 baud
    Serial.begin(115200);
    delay(1000); // Allow UART and power rails to stabilize

    // Keep onboard flash LED (GPIO 4) strictly LOW so it does not blind or heat up
    pinMode(FLASH_LED_PIN, OUTPUT);
    digitalWrite(FLASH_LED_PIN, LOW);

    printSystemDiagnostics();
}

unsigned long tickCount = 0;

void loop() {
    tickCount++;
    Serial.printf("  [TICK #%03lu] Uptime: %03lu s | Free Heap: %6u B | Free PSRAM: %7u B | STATUS: ALIVE 🟢\n",
                  tickCount, millis() / 1000, ESP.getFreeHeap(), ESP.getFreePsram());
    delay(1000);
}
