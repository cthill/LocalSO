import time
from threading import Timer

class EventScheduler:
    def __init__(self):
        pass

    def schedule_event(self, event_func, delay):
        return Timer(delay, event_func, ()).start()

    def schedule_event_recurring(self, event_func, delay):
        def _m_recurring_event():
            event_func()
            self.schedule_event(_m_recurring_event, delay)

        self.schedule_event(_m_recurring_event, delay)
