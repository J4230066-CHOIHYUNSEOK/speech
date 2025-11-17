from __future__ import annotations

import queue

from voice_recog.swith import SpeechRecognizer


class VoiceBridge:
    """
    Connects the voice_recog SpeechRecognizer to the chess_system FSM/GUI.
    Commands recognized on the audio thread are queued and applied on the Tk
    thread to avoid cross-thread Tk calls.
    """

    def __init__(self, root, gui, fsm, logger):
        self.root = root
        self.gui = gui
        self.fsm = fsm
        self.logger = logger
        self._queue: queue.Queue[str] = queue.Queue()
        self._polling = False

        def state_provider():
            return self.fsm.get_state()

        self._recognizer = SpeechRecognizer(
            on_command=self._enqueue_text,
            state_provider=state_provider,
            on_wake=self._enqueue_wake,
        )

    # -----------------------------------------------------
    # Public API
    # -----------------------------------------------------
    def start(self):
        self._recognizer.start()
        self._start_polling()

    def stop(self):
        self._polling = False
        self._recognizer.stop()

    # -----------------------------------------------------
    # Internal
    # -----------------------------------------------------
    def _enqueue_text(self, text: str):
        self._queue.put(text)

    def _enqueue_wake(self):
        """Send wake word to FSM so it transitions into ROOT."""
        try:
            if self.fsm.get_state().name != "ROOT":
                self._queue.put("hey chess")
        except Exception:
            self._queue.put("hey chess")

    def _start_polling(self):
        if self._polling:
            return
        self._polling = True
        self._poll_queue()

    def _poll_queue(self):
        if not self._polling:
            return
        processed = False
        while True:
            try:
                text = self._queue.get_nowait()
            except queue.Empty:
                break
            self.logger.write(text, tag="VOICE")
            self.gui.process_text(text)
            processed = True

        if processed:
            self.gui.update_board()

        # Keep polling from Tk thread
        self.root.after(100, self._poll_queue)
