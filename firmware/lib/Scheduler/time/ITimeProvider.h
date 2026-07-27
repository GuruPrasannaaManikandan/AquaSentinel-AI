#ifndef ITIME_PROVIDER_H
#define ITIME_PROVIDER_H

/**
 * @brief Abstract interface representing a millisecond time source.
 * Decouples scheduler logic from hardware millis() loops.
 */
class ITimeProvider {
public:
    virtual ~ITimeProvider() {}

    /**
     * @brief Retrieve current tick value in milliseconds.
     */
    virtual unsigned long now() = 0;
};

#endif
