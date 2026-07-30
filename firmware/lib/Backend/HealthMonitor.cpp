#include "HealthMonitor.h"
#include <Arduino.h>

HealthMonitor::HealthMonitor(Scheduler* scheduler, WiFiManager* wifiManager, MQTTManager* mqttManager, HAL* hal)
    : _scheduler(scheduler), _wifiManager(wifiManager), _mqttManager(mqttManager), _hal(hal) {
    _startTimeMs = millis();
}

HealthMetrics HealthMonitor::getMetrics() const {
    HealthMetrics m;
    
    // CPU Load & Task Execution Time
    if (_scheduler) {
        m.cpuLoad = _scheduler->getDiagnostics().getSchedulerUtilization();
        m.longestTaskExecutionUs = _scheduler->getDiagnostics().getLongestExecutionUs();
    } else {
        m.cpuLoad = 0.0f;
        m.longestTaskExecutionUs = 0;
    }
    
    // Heap Usage
    #if defined(ESP32) || defined(ARDUINO_ARCH_ESP32)
    m.freeHeap = ESP.getFreeHeap();
    m.totalHeap = ESP.getHeapSize();
    #else
    m.freeHeap = 245000;
    m.totalHeap = 320000;
    #endif

    // Wi-Fi and MQTT Status
    m.wifiStatus = _wifiManager ? static_cast<int>(_wifiManager->getState()) : 0;
    m.mqttStatus = _mqttManager ? static_cast<int>(_mqttManager->getState()) : 0;

    // Sensor Status defaults to OK (BackendGateway will update it from latest readings)
    m.sensorStatus = "OK";
    
    // Uptime in seconds
    m.uptimeSeconds = millis() / 1000;
    
    return m;
}
