import json
import threading
import time
from pathlib import Path
import lwake
import numpy as np
import sounddevice as sd
from vosk import KaldiRecognizer, Model

from grammar import load_grammar_for
from parser import extract_command


ROOT_IDLE_TIMEOUT = 8  # seconds before falling back to WAIT_WAKE if still in ROOT

# Directory to store the recorded wake sample for lWake
BASE_DIR = Path(__file__).parent
WAKE_REF_DIR = BASE_DIR / "ref"
WAKE_SAMPLE = WAKE_REF_DIR / "sample.wav"


#############################################
# 0. Wake word recording & detection (lWake)
#############################################


def record_wake_sample():
    """Prompt the user and record a short wake-word sample."""
    WAKE_REF_DIR.mkdir(exist_ok=True)
    print("Press 'm' then say the wake word 'hey chess' to record a 1s sample…")
    while True:
        user_input = input("Press m and Enter to start recording wake sample: ").strip().lower()
        if user_input == "m":
            break
    lwake.record(str(WAKE_SAMPLE), duration=2, trim_silence=True)
    print(f"[WAKE] Sample saved to {WAKE_SAMPLE}")


def wait_for_wake_word():
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
                threshold=0.1,
                method="embedding",
                callback=handle_detection,
            )
        except SystemExit:
            pass
        except Exception as e:
            print(f"[WAKE] listener error: {e}")

    t = threading.Thread(target=worker, daemon=True)
    t.start()
    detected.wait()
    t.join(timeout=2.0)


#############################################
# 1. 全ての状態ごとに Recognizer を事前生成
#############################################

states = ["ROOT", "IMAGINE"]

recognizers = {}    # state -> KaldiRecognizer

# すべての状態の recognizer を preload（高速動作のため）
for st in states:
    print(f"Loading recognizer for state: {st}")
    model = Model("vosk-model-small-en-us-0.15")
    grammar = load_grammar_for(st)
    recognizers[st] = KaldiRecognizer(model, 16000, json.dumps(grammar))

# 現在の状態
current_state = "WAIT_WAKE"
active_rec = None
last_state_change = time.time()


#############################################
# 2. FSM の状態遷移
#############################################

def fsm_transition(state, cmd):
    """cmd に応じて状態を切り替える簡易 FSM"""
    if cmd is None:
        return state

    if state == "ROOT":
        if cmd == "imagine":
            return "IMAGINE"
        return "ROOT"

    if state == "IMAGINE":
        if cmd == "back":
            return "ROOT"
        return "IMAGINE"

    return state


def change_state(new_state):
    global current_state, active_rec, last_state_change
    current_state = new_state
    print(f"[STATE] → {new_state}")
    last_state_change = time.time()
    if new_state in recognizers:
        active_rec = recognizers[new_state]
        active_rec.Reset()
    else:
        active_rec = None


#############################################
# 3. 音声 callback：常に active_rec のみ使用
#############################################

def callback(indata, frames, time, status):
    global active_rec, current_state

    if active_rec is None:
        return

    data = bytes(indata)

    if active_rec.AcceptWaveform(data):
        res = json.loads(active_rec.Result())
        text = res.get("text", "").strip()

        if not text:
            return

        print(f"[RECOG:{current_state}] {text}")

        cmd = extract_command(text, current_state)

        if cmd:
            print(f" → CMD: {cmd}")

        # FSM の状態遷移
        new_state = fsm_transition(current_state, cmd)
        if new_state != current_state:
            change_state(new_state)

    else:
        # Partial (debug 用)
        pres = json.loads(active_rec.PartialResult())
        if pres.get("partial"):
            print(f"[PARTIAL:{current_state}] {pres['partial']}")


#############################################
# 4. エントリーポイント
#############################################

def main():
    record_wake_sample()

    while True:
        change_state("WAIT_WAKE")
        wait_for_wake_word()
        change_state("ROOT")

        print("Listening…  (Ctrl+C to stop)")
        with sd.RawInputStream(
            samplerate=16000,
            blocksize=8000,
            dtype='int16',
            channels=1,
            callback=callback
        ):
            while True:
                time.sleep(0.1)
                if current_state == "ROOT":
                    if time.time() - last_state_change > ROOT_IDLE_TIMEOUT:
                        print("[STATE] ROOT idle → WAIT_WAKE (re-arm wake word)")
                        break
                elif current_state == "WAIT_WAKE":
                    break
        # Loop back to wait for wake word again


if __name__ == "__main__":
    main()