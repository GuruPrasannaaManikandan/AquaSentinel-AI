#ifndef SCHEDULER_DIAGNOSTICS_H
#define SCHEDULER_DIAGNOSTICS_H

#include "time/ITimeProvider.h"

/**
 * @brief Diagnostic tracker compiling utilization ratios and loop latency runtimes.
 */
class SchedulerDiagnostics {
private:
    ITimeProvider* _timeProvider;
    unsigned long _startTime;
    unsigned long _taskFailures;
    unsigned long _longestExecutionUs;
    unsigned long _shortestExecutionUs;
    unsigned long _totalTaskExecutionTimeUs;
    unsigned long _loopCount;
    unsigned long _lastLoopTimeUs;
    unsigned long _totalLoopLatencyUs;

public:
    SchedulerDiagnostics(ITimeProvider* timeProvider = nullptr);
    ~SchedulerDiagnostics() {}

    void setTimeProvider(ITimeProvider* provider);
    void start();
    
    void recordLoopStart();
    void recordTaskExecution(unsigned long durationUs, bool success);

    unsigned long getUptimeMs() const;
    unsigned long getTaskFailures() const { return _taskFailures; }
    unsigned long getLongestExecutionUs() const { return _longestExecutionUs; }
    unsigned long getShortestExecutionUs() const { return _shortestExecutionUs; }
    
    /**
     * @brief CPU execution time dedicated to task processing (%).
     */
    float getSchedulerUtilization() const;
    
    /**
     * @brief Average microsecond interval between scheduler loop cycles.
     */
    unsigned long getAverageLoopLatencyUs() const;
    
    void reset();
};

#endif
