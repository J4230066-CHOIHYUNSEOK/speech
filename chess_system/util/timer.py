import threading
import time


class Timer:
    """
    Simple countdown timer that can be driven manually (via tick)
    or by the built-in auto tick thread. A single timeout callback
    can be registered; it fires once per arm/reset cycle.
    """

    def __init__(self, max_time: float = 5.0):
        self.max_time = max_time
        self._remaining = max_time
        self._running = False
        self._timeout_fired = False
        self._timeout_cb = None

        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._auto_thread = None

    # ------------------------------------------------------------------
    # Basic controls
    # ------------------------------------------------------------------
    def arm(self, duration: float | None = None, start: bool = True):
        """Configure (optionally change duration) and start the countdown."""
        with self._lock:
            if duration is not None:
                self.max_time = duration
            self._remaining = self.max_time
            self._running = start
            self._timeout_fired = False

    def reset(self, restart: bool | None = None):
        """Reset remaining time without changing duration."""
        with self._lock:
            self._remaining = self.max_time
            self._timeout_fired = False
            if restart is not None:
                self._running = restart

    def pause(self):
        with self._lock:
            self._running = False

    def resume(self):
        with self._lock:
            if self._remaining <= 0:
                self._remaining = self.max_time
            self._running = True
            self._timeout_fired = False

    def on_timeout(self, callback):
        self._timeout_cb = callback

    # ------------------------------------------------------------------
    # Ticking
    # ------------------------------------------------------------------
    def tick(self, dt: float):
        callback = None
        with self._lock:
            if not self._running or self._remaining <= 0:
                return

            self._remaining = max(0.0, self._remaining - dt)
            if self._remaining == 0 and not self._timeout_fired:
                self._timeout_fired = True
                self._running = False
                callback = self._timeout_cb
        if callback:
            callback()

    def start_auto_tick(self, interval: float = 0.1):
        """Start background ticking. No-op if already running."""
        if self._auto_thread and self._auto_thread.is_alive():
            return

        self._stop_event.clear()
        self._auto_thread = threading.Thread(
            target=self._auto_loop, args=(interval,), daemon=True
        )
        self._auto_thread.start()

    def stop_auto_tick(self):
        if not self._auto_thread:
            return
        self._stop_event.set()
        self._auto_thread.join(timeout=1.0)
        self._auto_thread = None

    def _auto_loop(self, interval):
        while not self._stop_event.is_set():
            time.sleep(interval)
            self.tick(interval)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------
    @property
    def remaining(self) -> float:
        with self._lock:
            return self._remaining

    @property
    def running(self) -> bool:
        with self._lock:
            return self._running

    def __del__(self):
        self.stop_auto_tick()
