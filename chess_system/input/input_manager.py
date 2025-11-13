"""
Keyboard-based input manager used as a stand-in for a speech recognizer.
It runs a background thread that keeps reading from stdin and exposes
the lines through a simple FIFO queue.
"""

from __future__ import annotations

import queue
import threading
from dataclasses import dataclass


@dataclass
class InputEvent:
    raw_text: str

    @property
    def text(self) -> str:
        return self.raw_text.strip()


class InputManager:
    def __init__(self, prompt: str = "> "):
        self.prompt = prompt
        self._queue: queue.Queue[InputEvent] = queue.Queue()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self):
        if self._thread and self._thread.is_alive():
            return

        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        if not self._thread:
            return
        self._stop.set()
        self._thread.join(timeout=0.1)
        self._thread = None

    def _loop(self):
        while not self._stop.is_set():
            try:
                text = input(self.prompt)
            except EOFError:
                break
            self._queue.put(InputEvent(raw_text=text))

    def get(self, timeout: float | None = None) -> InputEvent | None:
        try:
            return self._queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def inject(self, text: str):
        """Used by tests to simulate an incoming utterance."""
        self._queue.put(InputEvent(raw_text=text))
