#include "hal/HAL.h"
#include <Arduino.h>
#include <string.h>

HAL::HAL(const PinConfig& config,
         ISensor* tempSensor,
         ISensor* salinitySensor,
         ISensor* phSensor,
         ISensor* turbiditySensor,
         ISensor* doSensor,
         IGPSSensor* gpsSensor,
         IActuator* greenLed,
         IActuator* yellowLed,
         IActuator* redLed,
         IActuator* buzzer,
         IActuator* pumpRelay) 
    : _config(config),
      _tempSensor(tempSensor),
      _salinitySensor(salinitySensor),
      _phSensor(phSensor),
      _turbiditySensor(turbiditySensor),
      _doSensor(doSensor),
      _gpsSensor(gpsSensor),
      _greenLed(greenLed),
      _yellowLed(yellowLed),
      _redLed(redLed),
      _buzzer(buzzer),
      _pumpRelay(pumpRelay),
      _sensorStatus("UNINITIALIZED") {
}

HAL::~HAL() {
    // Under Dependency Injection design, the HAL does NOT own the pointers
    // and must not delete them. The creator context is responsible for deletion.
}

bool HAL::initialize() {
    bool success = true;

    if (!_tempSensor->initialize()) success = false;
    if (!_salinitySensor->initialize()) success = false;
    if (!_phSensor->initialize()) success = false;
    if (!_turbiditySensor->initialize()) success = false;
    if (!_doSensor->initialize()) success = false;
    if (!_gpsSensor->initialize()) success = false;

    if (!_greenLed->initialize()) success = false;
    if (!_yellowLed->initialize()) success = false;
    if (!_redLed->initialize()) success = false;
    if (!_buzzer->initialize()) success = false;
    if (!_pumpRelay->initialize()) success = false;

    _sensorStatus = success ? "OK" : "FAULT";
    return success;
}

TelemetryData HAL::readAllSensors() {
    TelemetryData data;
    
    data.temperature_c = _tempSensor->read();
    data.salinity_ppt = _salinitySensor->read();
    data.ph = _phSensor->read();
    data.turbidity_ntu = _turbiditySensor->read();
    data.dissolved_oxygen_mg_l = _doSensor->read();
    
    double lat = 0.0, lon = 0.0;
    _gpsSensor->read(lat, lon);
    data.latitude = lat;
    data.longitude = lon;
    
    // Overall HAL status:
    // Active physical channels: pH and Turbidity.
    // As long as raw readings are valid numbers (not -999.0f), hardware is OK.
    if (data.ph != -999.0f && data.turbidity_ntu != -999.0f) {
        _sensorStatus = "OK";
    } else {
        _sensorStatus = "FAULT";
    }
    data.sensor_status = _sensorStatus;
    Serial.print("[HAL-ALL] ph="); Serial.print(data.ph);
    Serial.print(" turb="); Serial.print(data.turbidity_ntu);
    Serial.print(" status="); Serial.println(_sensorStatus);
    
    return data;
}

bool HAL::writeActuator(const char* name, const char* state) {
    if (strcmp(name, "green_led") == 0) {
        return _greenLed->writeState(state);
    } else if (strcmp(name, "yellow_led") == 0) {
        return _yellowLed->writeState(state);
    } else if (strcmp(name, "red_led") == 0) {
        return _redLed->writeState(state);
    } else if (strcmp(name, "buzzer") == 0) {
        return _buzzer->writeState(state);
    } else if (strcmp(name, "pump_relay") == 0) {
        return _pumpRelay->writeState(state);
    }
    return false;
}

const char* HAL::readActuator(const char* name) {
    if (strcmp(name, "green_led") == 0) {
        return _greenLed->readState();
    } else if (strcmp(name, "yellow_led") == 0) {
        return _yellowLed->readState();
    } else if (strcmp(name, "red_led") == 0) {
        return _redLed->readState();
    } else if (strcmp(name, "buzzer") == 0) {
        return _buzzer->readState();
    } else if (strcmp(name, "pump_relay") == 0) {
        return _pumpRelay->readState();
    }
    return "OFF";
}

bool HAL::runSelfTest() {
    bool healthy = true;
    
    if (!_tempSensor->selfTest()) { Serial.println("[HAL-TEST] tempSensor failed"); healthy = false; }
    if (!_salinitySensor->selfTest()) { Serial.println("[HAL-TEST] salinitySensor failed"); healthy = false; }
    if (!_phSensor->selfTest()) { Serial.println("[HAL-TEST] phSensor failed"); healthy = false; }
    if (!_turbiditySensor->selfTest()) { Serial.println("[HAL-TEST] turbiditySensor failed"); healthy = false; }
    if (!_doSensor->selfTest()) { Serial.println("[HAL-TEST] doSensor failed"); healthy = false; }
    if (!_gpsSensor->selfTest()) { Serial.println("[HAL-TEST] gpsSensor failed"); healthy = false; }
    
    if (!_greenLed->selfTest()) { Serial.println("[HAL-TEST] greenLed failed"); healthy = false; }
    if (!_yellowLed->selfTest()) { Serial.println("[HAL-TEST] yellowLed failed"); healthy = false; }
    if (!_redLed->selfTest()) { Serial.println("[HAL-TEST] redLed failed"); healthy = false; }
    if (!_buzzer->selfTest()) { Serial.println("[HAL-TEST] buzzer failed"); healthy = false; }
    if (!_pumpRelay->selfTest()) { Serial.println("[HAL-TEST] pumpRelay failed"); healthy = false; }

    _sensorStatus = healthy ? "OK" : "FAULT";
    return healthy;
}

void HAL::shutdown() {
    _tempSensor->shutdown();
    _salinitySensor->shutdown();
    _phSensor->shutdown();
    _turbiditySensor->shutdown();
    _doSensor->shutdown();
    _gpsSensor->shutdown();

    _greenLed->shutdown();
    _yellowLed->shutdown();
    _redLed->shutdown();
    _buzzer->shutdown();
    _pumpRelay->shutdown();
    
    _sensorStatus = "UNINITIALIZED";
}
