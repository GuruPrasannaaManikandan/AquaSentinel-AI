#ifndef HEALTH_MONITOR_H
#define HEALTH_MONITOR_H

#include "Scheduler.h"
#include "WiFiManager.h"
#include "MQTTManager.h"
#include "hal/HAL.h"
#include <stdint.h>

/**
 * @brief HealthMetrics structure aggregating CPU, memory, task, network, and sensor status.
 */
struct HealthMetrics {
    float cpuLoad;
    uint32_t freeHeap;
    uint32_t totalHeap;
    uint32_t longestTaskExecutionUs;
    int wifiStatus;
    int mqttStatus;
    const char* sensorStatus;
    unsigned long uptimeSeconds;
};

class HealthMonitor {
private:
    Scheduler* _scheduler;
    WiFiManager* _wifiManager;
    MQTTManager* _mqttManager;
    HAL* _hal;
    unsigned long _startTimeMs;

public:
    HealthMonitor(Scheduler* scheduler, WiFiManager* wifiManager, MQTTManager* mqttManager, HAL* hal);
    ~HealthMonitor() {}

    HealthMetrics getMetrics() const;
};

#endif // HEALTH_MONITOR_H
