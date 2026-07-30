#include "TelemetryPublisher.h"
#include <ArduinoJson.h>
#include <stdio.h>
#include <string.h>

TelemetryPublisher::TelemetryPublisher(MQTTManager* mqttManager, const char* deviceId, const char* datasetRoute)
    : _mqttManager(mqttManager), _sequenceNumber(0) {
    strncpy(_deviceId, deviceId ? deviceId : "UNKNOWN", sizeof(_deviceId) - 1);
    _deviceId[sizeof(_deviceId) - 1] = '\0';

    strncpy(_datasetRoute, datasetRoute ? datasetRoute : "caml", sizeof(_datasetRoute) - 1);
    _datasetRoute[sizeof(_datasetRoute) - 1] = '\0';
}

bool TelemetryPublisher::publishTelemetry(const TelemetryData& data, float battery, int rssi, const char* isoTimestamp) {
    if (!_mqttManager) return false;

    StaticJsonDocument<512> doc;
    doc["schema_version"] = "1.0";
    doc["device_id"] = _deviceId;
    doc["timestamp"] = isoTimestamp;
    doc["sequence_number"] = _sequenceNumber++;
    doc["dataset_route"] = _datasetRoute;
    
    JsonObject loc = doc.createNestedObject("location");
    loc["latitude"] = data.latitude;
    loc["longitude"] = data.longitude;

    JsonObject sensors = doc.createNestedObject("sensors");
    sensors["temperature_c"] = data.temperature_c;
    sensors["salinity_ppt"] = data.salinity_ppt;
    sensors["ph"] = data.ph;
    sensors["turbidity_ntu"] = data.turbidity_ntu;
    sensors["dissolved_oxygen_mg_l"] = data.dissolved_oxygen_mg_l;
    sensors["battery"] = battery;
    sensors["rssi"] = rssi;
    sensors["distance_to_water_m"] = (strcmp(_datasetRoute, "caml") == 0) ? 120.0 : 0.0;
    sensors["sample_depth"] = (strcmp(_datasetRoute, "habsos") == 0) ? 1.0 : 0.0;

    JsonObject health = doc.createNestedObject("device_health");
    health["wifi_connected"] = true;
    health["mqtt_connected"] = _mqttManager->isConnected();
    health["sensor_status"] = data.sensor_status ? data.sensor_status : "OK";

    char buffer[512];
    size_t len = serializeJson(doc, buffer, sizeof(buffer));

    char topic[64];
    snprintf(topic, sizeof(topic), "aquatic/%s/telemetry", _deviceId);

    if (len > 0 && len < sizeof(buffer)) {
        return _mqttManager->publish(topic, buffer, 0, false);
    }
    return false;
}
