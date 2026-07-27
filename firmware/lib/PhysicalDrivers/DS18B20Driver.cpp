#include "DS18B20Driver.h"

DS18B20Driver::DS18B20Driver(int pin) 
    : _pin(pin), 
      _oneWire(nullptr), 
      _sensors(nullptr), 
      _health(DriverHealth::NOT_INITIALIZED), 
      _initialized(false) {
}

DS18B20Driver::~DS18B20Driver() {
    delete _sensors;
    delete _oneWire;
}

bool DS18B20Driver::initialize() {
    _oneWire = new OneWire(_pin);
    _sensors = new DallasTemperature(_oneWire);
    _sensors->begin();
    
    if (_sensors->getDeviceCount() == 0) {
        _health = DriverHealth::SENSOR_DISCONNECTED;
        _initialized = false;
        return false;
    }
    
    _sensors->setResolution(12);
    _health = DriverHealth::OK;
    _initialized = true;
    return true;
}

float DS18B20Driver::read() {
    if (!_initialized) {
        _health = DriverHealth::NOT_INITIALIZED;
        return -999.0;
    }
    
    _sensors->requestTemperatures();
    float tempC = _sensors->getTempCByIndex(0);
    
    if (tempC == DEVICE_DISCONNECTED_C) {
        _health = DriverHealth::SENSOR_DISCONNECTED;
        return -999.0;
    } else if (tempC == -85.0) {
        _health = DriverHealth::CRC_FAILURE;
        return -999.0;
    }
    
    _health = DriverHealth::OK;
    return tempC;
}

bool DS18B20Driver::selfTest() {
    if (!_initialized) {
        _health = DriverHealth::NOT_INITIALIZED;
        return false;
    }
    _sensors->requestTemperatures();
    float tempC = _sensors->getTempCByIndex(0);
    if (tempC == DEVICE_DISCONNECTED_C) {
        _health = DriverHealth::SENSOR_DISCONNECTED;
        return false;
    } else if (tempC == -85.0) {
        _health = DriverHealth::CRC_FAILURE;
        return false;
    }
    _health = DriverHealth::OK;
    return true;
}

const char* DS18B20Driver::status() {
    switch (_health) {
        case DriverHealth::OK: return "OK";
        case DriverHealth::NOT_INITIALIZED: return "NOT_INITIALIZED";
        case DriverHealth::SENSOR_DISCONNECTED: return "SENSOR_DISCONNECTED";
        case DriverHealth::CRC_FAILURE: return "CRC_FAILURE";
        default: return "UNKNOWN";
    }
}

void DS18B20Driver::shutdown() {
    _health = DriverHealth::NOT_INITIALIZED;
}
