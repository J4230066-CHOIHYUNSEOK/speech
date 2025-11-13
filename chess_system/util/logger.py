from collections import deque
from datetime import datetime


class Logger:
    def __init__(self, history_limit: int = 200):
        self.gui = None
        self._history = deque(maxlen=history_limit)

    def attach_gui(self, gui):
        self.gui = gui

    def write(self, text: str, tag: str = "FSM"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = f"[{timestamp}] {text}"
        self._history.append(entry)
        print(entry)
        if self.gui:
            self.gui.append_history(f"[{tag}] {text}")

    def get_history(self):
        return list(self._history)
