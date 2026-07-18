class Queue:
    """
    Simulates a FreeRTOS Queue for thread-safe/task-safe communication.
    Provides simple FIFO queue functionality.
    """
    def __init__(self, maxsize: int = 0):
        self.maxsize = maxsize
        self.queue = []

    def put(self, item) -> bool:
        if self.maxsize > 0 and len(self.queue) >= self.maxsize:
            return False
        self.queue.append(item)
        return True

    def get(self):
        if not self.queue:
            return None
        return self.queue.pop(0)

    def empty(self) -> bool:
        return len(self.queue) == 0

    def size(self) -> int:
        return len(self.queue)

    def clear(self):
        self.queue.clear()


class Event:
    """
    Simulates FreeRTOS Event Groups / Event Flags.
    Used for simple signal synchronization between tasks.
    """
    def __init__(self):
        self._flag = False

    def set(self):
        self._flag = True

    def clear(self):
        self._flag = False

    def is_set(self) -> bool:
        return self._flag


class Task:
    """
    Represents a scheduled unit of execution (FreeRTOS Task).
    """
    def __init__(self, name: str, period_ticks: int, callback, priority: int = 1):
        self.name = name
        self.period = period_ticks
        self.callback = callback
        self.priority = priority
        self.last_run = 0

    def should_run(self, current_tick: int) -> bool:
        # Check if period has elapsed since last run
        return (current_tick - self.last_run) >= self.period

    def run(self, current_tick: int):
        self.last_run = current_tick
        self.callback()


class SimpleScheduler:
    """
    A lightweight, tick-based cooperative scheduler simulating an RTOS kernel.
    """
    def __init__(self):
        self.tasks = []
        self.current_tick = 0

    def register_task(self, task: Task):
        # Insert task keeping them sorted by priority (higher first), then name
        self.tasks.append(task)
        self.tasks.sort(key=lambda t: (-t.priority, t.name))

    def step(self):
        """Advances scheduler by one tick and runs all ready tasks."""
        self.current_tick += 1
        for task in self.tasks:
            if task.should_run(self.current_tick):
                task.run(self.current_tick)

    def reset(self):
        self.current_tick = 0
        for task in self.tasks:
            task.last_run = 0
