from contextlib import contextmanager
import math
import signal
import threading

def bytes_to_str(data):
    return " ".join("{:02x}".format(ord(c)) for c in data)

def buff_to_str(buff):
    return " ".join("{:02x}".format(b) for b in buff)

def ceildiv(a, b):
    return int(-(-a // b))

def dist(x1, y1, x2, y2):
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

class LockDict(dict):
    def __init__(self, *args, **kw):
        super(LockDict, self).__init__(*args, **kw)
        self.lock = threading.Lock()

    def __enter__(self):
        self.lock.acquire()
        return self

    def __exit__(self, type, value, traceback):
        self.lock.release()

    def acquire(self):
        self.lock.acquire()

    def release(self):
        self.lock.release()

class LockSet(set):
    def __init__(self, *args, **kw):
        super(LockSet, self).__init__(*args, **kw)
        self.lock = threading.Lock()

    def __enter__(self):
        self.lock.acquire()
        return self

    def __exit__(self, type, value, traceback):
        self.lock.release()

    def acquire(self):
        self.lock.acquire()

    def release(self):
        self.lock.release()

class LockList(list):
    def __init__(self, *args, **kw):
        super(LockList, self).__init__(*args, **kw)
        self.lock = threading.Lock()

    def __enter__(self):
        self.lock.acquire()
        return self

    def __exit__(self, type, value, traceback):
        self.lock.release()

    def acquire(self):
        self.lock.acquire()

    def release(self):
        self.lock.release()

class SigHandler:
    def __init__(self):
        self.caught_signal = False
        signal.signal(signal.SIGINT, self.handle_signal)
        signal.signal(signal.SIGTERM, self.handle_signal)

    def handle_signal(self, signum, frame):
        self.caught_signal = True

# acquire_all function taken from:
#  Python Cookbook, 3rd Edition
#  By Brian Jones, David Beazley
#  ISBN: 1449340377

# Thread-local state to stored information on locks already acquired
_local = threading.local()
@contextmanager
def acquire_all(*locks):
    # Sort locks by object identifier
    locks = sorted(locks, key=lambda x: id(x))

    # Make sure lock order of previously acquired locks is not violated
    acquired = getattr(_local,'acquired',[])
    if acquired and max(id(lock) for lock in acquired) >= id(locks[0]):
        raise RuntimeError('Lock Order Violation')

    # Acquire all of the locks
    acquired.extend(locks)
    _local.acquired = acquired
    try:
        for lock in locks:
            lock.acquire()
        yield
    finally:
        # Release locks in reverse order of acquisition
        for lock in reversed(locks):
            lock.release()
        del acquired[-len(locks):]
