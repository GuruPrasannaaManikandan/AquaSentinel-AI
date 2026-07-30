#include "OfflineTelemetryBuffer.h"
#include <string.h>

OfflineTelemetryBuffer::OfflineTelemetryBuffer() {
    clear();
}

void OfflineTelemetryBuffer::clear() {
    _head = 0;
    _tail = 0;
    _count = 0;
    _droppedCount = 0;
    memset(_buffer, 0, sizeof(_buffer));
}

bool OfflineTelemetryBuffer::push(const TelemetryData& data) {
    bool overflow = false;
    
    if (isFull()) {
        // Discard the oldest cached value (circular buffer overwrite)
        _head = (_head + 1) % OFFLINE_BUFFER_CAPACITY;
        _count--;
        _droppedCount++;
        overflow = true;
    }
    
    _buffer[_tail] = data;
    _tail = (_tail + 1) % OFFLINE_BUFFER_CAPACITY;
    _count++;
    
    return overflow;
}

bool OfflineTelemetryBuffer::pop(TelemetryData& dataOut) {
    if (isEmpty()) {
        return false;
    }
    
    dataOut = _buffer[_head];
    _head = (_head + 1) % OFFLINE_BUFFER_CAPACITY;
    _count--;
    
    return true;
}
