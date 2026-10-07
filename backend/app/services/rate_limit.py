"""A per-origin sliding-window counter, in process memory. Simple on purpose.

Each process counts on its own (several gunicorn workers each allow the limit) and a restart forgets
everything. Enough to stop a loop from filling an inbox; not a distributed limiter.
"""

import threading
import time
from collections import defaultdict, deque
from collections.abc import Callable


class SlidingWindowLimiter:
    def __init__(self, limit: int, window_seconds: float, clock: Callable[[], float] = time.monotonic):
        self.limit = limit
        self.window_seconds = window_seconds
        self._clock = clock
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, key: str) -> bool:
        """Count one hit for `key` if it is under the limit. Returns False, counting nothing, if not."""
        now = self._clock()
        with self._lock:
            self._forget_before(now - self.window_seconds)
            hits = self._hits[key]
            if len(hits) >= self.limit:
                return False
            hits.append(now)
            return True

    def _forget_before(self, cutoff: float) -> None:
        for key in list(self._hits):
            hits = self._hits[key]
            while hits and hits[0] <= cutoff:
                hits.popleft()
            if not hits:
                del self._hits[key]
