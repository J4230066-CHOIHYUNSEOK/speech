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
        entry = f"[{timestamp}] [{tag}] {text}"
        self._history.append(entry)
        print(entry)
        if self.gui:
            self.gui.show_fsm_message(text, tag=tag)

    def write_move(self, text: str):
        """Log a move to history without cluttering the FSM message panel."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = f"[{timestamp}] [MOVE] {text}"
        self._history.append(entry)
        print(entry)
        if self.gui:
            # Rebuild history in GUI so move list stays accurate (including undo).
            self.gui.refresh_history()

    def get_history(self):
        return list(self._history)
