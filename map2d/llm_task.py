"""Run an LLM call in a background thread without freezing pygame."""
from __future__ import annotations

import threading
import time


class LLMTask:
    TIMEOUT = 90.0

    def __init__(self):
        self._thread = None
        self._running = False
        self._timed_out = False
        self._started_at = 0.0
        self.result = None
        self.error = None

    # ---- Public read-only views ----
    @property
    def timed_out(self) -> bool:
        return self._timed_out

    def start(self, fn, *args, **kwargs):
        if self._running:
            return
        self._running = True
        self._timed_out = False
        self._started_at = time.time()
        self.result = None
        self.error = None

        def _worker():
            try:
                r = fn(*args, **kwargs)
                if not self._timed_out:
                    self.result = r
            except Exception as e:
                if not self._timed_out:
                    self.error = e
            finally:
                self._running = False

        self._thread = threading.Thread(target=_worker, daemon=True)
        self._thread.start()

    def update(self):
        """Call every frame. Marks as timed out if it runs too long."""
        if self._running and time.time() - self._started_at > self.TIMEOUT:
            self._timed_out = True
            self._running = False

    def is_done(self) -> bool:
        return not self._running

    def elapsed(self) -> float:
        return time.time() - self._started_at