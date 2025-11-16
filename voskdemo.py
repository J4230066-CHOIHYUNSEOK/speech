from vosk import Model, KaldiRecognizer
import json
import sounddevice as sd

# --- vocabulary ---
pieces = ["pawn", "knight", "bishop", "rook", "queen", "king"]
files  = ["a","b","c","d","e","f","g","h"]
ranks  = ["one","two","three","four","five","six","seven","eight"]

# grammar array
phrases = ["imagine", "return", "stop", "take", "play"]

# expand play commands
for p in pieces:
    for f in files:
        for r in ranks:
            phrases.append(f"play {p} {f} {r}")

print("Total patterns:", len(phrases))

# --- load model ---
model = Model("vosk-model-small-en-us-0.15")

rec = KaldiRecognizer(model, 16000, json.dumps(phrases))

# --- stream ---
def callback(indata, frames, time, status):
    data = bytes(indata)
    if rec.AcceptWaveform(data):
        print(rec.Result())
    else:
        print(rec.PartialResult())

with sd.RawInputStream(samplerate=16000, blocksize=8000,
                       dtype='int16', channels=1, callback=callback):
    print("Listening...")
    while True:
        pass