from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Callable

import lwake
import sounddevice as sd
from vosk import KaldiRecognizer, Model

from voice_recog.grammar import load_grammar_for
from voice_recog.parser import extract_command


# Directory to store the recorded wake sample for lWake
BASE_DIR = Path(__file__).parent
WAKE_REF_DIR = BASE_DIR / "ref"
WAKE_SAMPLE = WAKE_REF_DIR / "sample.wav"


#############################################
# Wake word recording & detection (lWake)
#############################################


def _wait_for_m(prompt: str):
    """Block until the user types 'm' + Enter."""
    print(prompt)
    while True:
        user_input = input("Press m and Enter to continue: ").strip().lower()
        if user_input == "m":
            return


def record_wake_sample(force: bool = False):
    """Prompt the user and record a short wake-word sample."""
    WAKE_REF_DIR.mkdir(exist_ok=True)
    if WAKE_SAMPLE.exists() and not force:
        print(f"[WAKE] Using existing sample at {WAKE_SAMPLE}")
        return
    _wait_for_m("Press 'm' then say the wake word 'hey chess' to record a 1s sample…")
    lwake.record(str(WAKE_SAMPLE), duration=2, trim_silence=False)
    print(f"[WAKE] Sample saved to {WAKE_SAMPLE}")


def wait_for_wake_word(stop_event: threading.Event | None = None):
    """
    Block until lWake detects the wake word using the recorded sample.wav.
    Runs lWake in a thread so we can return to the main loop after detection.
    """
    detected = threading.Event()

    def handle_detection(detection, stream):
        print(f"[WAKE] Detected '{detection['wakeword']}' at {detection['timestamp']}")
        detected.set()
        # Stop the listen loop by raising, caught in the worker thread.
        raise SystemExit

    print("Listening for wake word with lWake (say 'hey chess')…")

    def worker():
        try:
            lwake.listen(
                str(WAKE_REF_DIR),
                threshold=0.05,
                method="embedding",
                callback=handle_detection,
            )
        except SystemExit:
            pass
        except Exception as e:
            if not (stop_event and stop_event.is_set()):
                print(f"[WAKE] listener error: {e}")

    t = threading.Thread(target=worker, daemon=True)
    t.start()
    while not detected.is_set():
        if stop_event and stop_event.is_set():
            break
        detected.wait(timeout=0.1)
    t.join(timeout=2.0)


#############################################
# Speech recognizer wrapper
#############################################


class SpeechRecognizer:
    """
    Background speech listener that emits normalized commands via callback.
    - Uses lWake for wake word detection.
    - Uses Vosk grammar per FSM state (ROOT / PLAY / IMAGINE).
    """

    def __init__(
        self,
        on_command: Callable[[str], None],
        state_provider: Callable[[], str | None] | None = None,
        on_wake: Callable[[], None] | None = None,
    ):
        self._on_command = on_command
        self._state_provider = state_provider or (lambda: "ROOT")
        self._on_wake = on_wake or (lambda: None)

        self.recognizers: dict[str, KaldiRecognizer] = {}
        self._active_rec: KaldiRecognizer | None = None
        self.current_state = "WAIT_WAKE"
        self._last_state_change = time.time()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

        self._load_recognizers()

    def _load_recognizers(self):
        for st in ["ROOT", "IMAGINE"]:
            print(f"[LOAD] Loading recognizer for state: {st}")
            model = Model("vosk-model-small-en-us-0.15")
            grammar = load_grammar_for(st)
            self.recognizers[st] = KaldiRecognizer(model, 16000, json.dumps(grammar))

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        _wait_for_m("Press 'm' and Enter to start the speech listener.")
        record_wake_sample(force=False)
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=1.0)
            self._thread = None

    # =============================================
    # Internal loops
    # =============================================
    def _loop(self):
        while not self._stop.is_set():
            self._change_state("WAIT_WAKE")
            wait_for_wake_word(stop_event=self._stop)
            if self._stop.is_set():
                break
            self._on_wake()
            # align with app state right after wake
            target_state = self._state_from_app(default="ROOT")
            if target_state == "WAIT_WAKE":
                target_state = "ROOT"
            self._change_state(target_state)
            self._listen_until_app_wait_wake()

    def _listen_until_app_wait_wake(self):
        print("Listening…  (Ctrl+C to stop)")
        waiting_for_app_root = True
        with sd.RawInputStream(
            samplerate=16000,
            blocksize=4000,
            dtype="int16",
            channels=1,
            callback=self._audio_callback,
        ):
            while not self._stop.is_set():
                app_state = self._state_from_app()
                if app_state:
                    # Wait until the app actually enters ROOT once before re-arming wake
                    if waiting_for_app_root:
                        if app_state != "WAIT_WAKE":
                            waiting_for_app_root = False
                            self._change_state(app_state)
                    else:
                        if app_state != self.current_state:
                            self._change_state(app_state)
                        if self.current_state == "WAIT_WAKE":
                            break
                time.sleep(0.1)

    # =============================================
    # Helpers
    # =============================================
    def _audio_callback(self, indata, frames, time_info, status):
        if self._active_rec is None:
            return

        data = bytes(indata)
        if self._active_rec.AcceptWaveform(data):
            res = json.loads(self._active_rec.Result())
            text = res.get("text", "").strip()

            if not text:
                return

            cmd = extract_command(text, self.current_state)
            if cmd:
                print(f"[RECOG:{self.current_state}] {text} → {cmd}")
                self._on_command(cmd)
            self._last_state_change = time.time()
        else:
            # Partial (debug 用)
            pres = json.loads(self._active_rec.PartialResult())
            if pres.get("partial"):
                print(f"[PARTIAL:{self.current_state}] {pres['partial']}")

    def _sync_with_app_state(self):
        target = self._state_from_app()
        if target and target != self.current_state:
            self._change_state(target)

    def _state_from_app(self, default: str | None = None) -> str | None:
        try:
            state = self._state_provider()
        except Exception:
            state = None
        if state is None:
            return default
        # Allow Enum State values to flow through
        if hasattr(state, "name"):
            return state.name  # type: ignore[attr-defined]
        return str(state)

    def _change_state(self, new_state: str):
        if new_state == self.current_state:
            return
        self.current_state = new_state
        self._last_state_change = time.time()
        if new_state in self.recognizers:
            self._active_rec = self.recognizers[new_state]
            self._active_rec.Reset()
        else:
            self._active_rec = None
        # keep quiet; main FSM handles user-facing state logs


#############################################
# Standalone entry point (debug)
#############################################


def _print_command(cmd: str):
    print(f"CMD: {cmd}")


def main():
    listener = SpeechRecognizer(on_command=_print_command)
    listener.start()
    print("Speech recognizer running. Press Ctrl+C to exit.")
    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("Stopping listener…")
        listener.stop()


if __name__ == "__main__":
    main()
