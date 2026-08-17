import threading
from collections import deque
import time

class RateLimiter:
    def __init__(self, max_calls=10, period=60):
        self.max_calls = max_calls
        self.period = period
        self.calls = deque()
        self.lock = threading.Lock()

    def acquire(self):
        with self.lock:
            now = time.time()
            
            while self.calls and now - self.calls[0] >= self.period:
                self.calls.popleft()
            
            if len(self.calls) >= self.max_calls:
                sleep_time = self.period - (now - self.calls[0])
                time.sleep(sleep_time + 0.1)
                return self.acquire()
            
            self.calls.append(time.time())

dm_rate_limiter = RateLimiter(max_calls=9, period=60)
