#include "TaskManager.h"
#include <Arduino.h>

TaskManager::TaskManager() : _taskCount(0) {
    for (int i = 0; i < MAX_TASKS; i++) {
        _tasks[i] = nullptr;
    }
}

TaskManager::~TaskManager() {
    for (int i = 0; i < _taskCount; i++) {
        delete _tasks[i];
    }
}

bool TaskManager::registerTask(Task* task) {
    if (!task) return false;
    if (_taskCount >= MAX_TASKS) return false;

    // Check duplicate ID and Duplicate Names
    for (int i = 0; i < _taskCount; i++) {
        if (_tasks[i]->getId() == task->getId()) {
            return false;
        }
        if (strcmp(_tasks[i]->getName(), task->getName()) == 0) {
            return false;
        }
    }

    _tasks[_taskCount++] = task;
    return true;
}

bool TaskManager::removeTask(TaskId id) {
    int targetIndex = -1;
    for (int i = 0; i < _taskCount; i++) {
        if (_tasks[i]->getId() == id) {
            targetIndex = i;
            break;
        }
    }

    if (targetIndex == -1) return false;

    delete _tasks[targetIndex];

    for (int i = targetIndex; i < _taskCount - 1; i++) {
        _tasks[i] = _tasks[i + 1];
    }
    _tasks[--_taskCount] = nullptr;
    return true;
}

bool TaskManager::enableTask(TaskId id) {
    Task* t = getTask(id);
    if (!t) return false;
    t->setEnabled(true);
    return true;
}

bool TaskManager::disableTask(TaskId id) {
    Task* t = getTask(id);
    if (!t) return false;
    t->setEnabled(false);
    return true;
}

bool TaskManager::pauseTask(TaskId id) {
    Task* t = getTask(id);
    if (!t) return false;
    t->setState(TaskState::WAITING);
    return true;
}

bool TaskManager::resumeTask(TaskId id) {
    Task* t = getTask(id);
    if (!t) return false;
    t->setState(TaskState::READY);
    return true;
}

Task* TaskManager::getTask(TaskId id) const {
    for (int i = 0; i < _taskCount; i++) {
        if (_tasks[i]->getId() == id) {
            return _tasks[i];
        }
    }
    return nullptr;
}

Task* TaskManager::getTaskByIndex(int index) const {
    if (index < 0 || index >= _taskCount) return nullptr;
    return _tasks[index];
}

void TaskManager::resetAllStatistics() {
    for (int i = 0; i < _taskCount; i++) {
        _tasks[i]->resetStats();
    }
}
