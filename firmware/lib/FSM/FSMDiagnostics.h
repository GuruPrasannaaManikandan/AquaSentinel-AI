#ifndef FSM_DIAGNOSTICS_H
#define FSM_DIAGNOSTICS_H

/**
 * @brief Dynamic metrics monitoring execution speeds and queue overflows.
 */
struct FSMDiagnostics {
    unsigned long transitionCount;
    unsigned long invalidEventsCount;
    unsigned long invalidTransitionsCount;
    unsigned long timeoutsCount;
    unsigned long guardFailuresCount;
    unsigned long queueDepth;
    unsigned long droppedEvents;
    unsigned long observerNotifications;
    unsigned long averageTransitionTimeUs;
    unsigned long maxTransitionTimeUs;
};

#endif
