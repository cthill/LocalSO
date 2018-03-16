from threading import Timer

def schedule_event(event_func, delay):
    return Timer(delay, event_func, ()).start()

def schedule_event_recurring(event_func, delay):
    def _m_recurring_event():
        event_func()
        schedule_event(_m_recurring_event, delay)

    schedule_event(_m_recurring_event, delay)
