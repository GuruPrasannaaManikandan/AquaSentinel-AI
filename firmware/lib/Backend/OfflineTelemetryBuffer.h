#ifndef OFFLINE_TELEMETRY_BUFFER_H
#define OFFLINE_TELEMETRY_BUFFER_H

#include "config/TelemetryData.h"
#include <stddef.h>

#define OFFLINE_BUFFER_CAPACITY 20

/**
 * @brief Static circular FIFO buffer storing sensor telemetry when offline.
 * Prevents dynamic memory allocations to ensure stability on memory-constrained devices.
 */
class OfflineTelemetryBuffer {
private:
    TelemetryData _buffer[OFFLINE_BUFFER_CAPACITY];
    int _head;
    int _tail;
    int _count;
    unsigned long _droppedCount;

public:
    OfflineTelemetryBuffer();
    ~OfflineTelemetryBuffer() {}

    /**
     * @brief Pushes a telemetry reading. If the buffer is full, overwrites the
     * oldest reading (circular overwrite) and returns true to signal overflow.
     */
    bool push(const TelemetryData& data);

    /**
     * @brief Dequeues the oldest cached telemetry reading. Returns false if empty.
     */
    bool pop(TelemetryData& dataOut);

    bool isEmpty() const { return _count == 0; }
    bool isFull() const { return _count == OFFLINE_BUFFER_CAPACITY; }
    int getCount() const { return _count; }
    unsigned long getDroppedCount() const { return _droppedCount; }
    void clear();
};

#endif // OFFLINE_TELEMETRY_BUFFER_H
