import whisper
import sounddevice as sd
import numpy as np
import re
import time

# Whisperモデルをロード（medium）
model = whisper.load_model("medium")
rate = 16000

def record(seconds=5):
    print("🎙️ Recording...")
    audio = sd.rec(int(seconds * rate), samplerate=rate, channels=1, dtype=np.float32)
    sd.wait()
    return np.squeeze(audio)

def is_speech(audio, threshold=0.005):
    return np.max(np.abs(audio)) > threshold

# 認識結果補正辞書（よく誤認する単語）
fix_dict = {
    "rook": "rook",
    "roke": "rook",
    "rouge": "rook",
    "knight": "knight",
    "kknight": "knight",
    "night": "knight",
    "bishop": "bishop",
    "b-shop": "bishop",
    "B-shop": "bishop",
    "B shop": "bishop",
    "b shop": "bishop",
    "pawn": "pawn",
    "pong": "pawn",
    "palm": "pawn",
    "queen": "queen",
    "king": "king",
    "a": "A", "b": "B", "c": "C", "d": "D",
    "e": "E", "f": "F", "g": "G", "h": "H",
    "a-1": "A1", "b-2": "B2", "c-3": "C3", "d-4": "D4",
    "e-5": "E5", "f-6": "F6", "g-7": "G7", "h-8": "H8",
}

# 文法パターン: play (piece or location) destination
pattern = re.compile(
    r"play[\s,]+([a-hA-H][1-8]|pawn|rook|knight|bishop|queen|king)[\s,]+([a-hA-H][1-8])",
    re.IGNORECASE
)

print("🎙️ English real-time chess voice recognition started. Ctrl+C to stop.")

try:
    while True:
        audio = record(5)
        if not is_speech(audio):
            print("⏸️ Silence detected, skipping...")
            continue

        result = model.transcribe(audio, language="en")
        text = result["text"].lower()  # 小文字化で正規表現一致を安定

        # 補正辞書
        for k, v in fix_dict.items():
            text = text.replace(k, v.lower())

        # 文法解析
        moves = []
        for match in pattern.finditer(text):
            piece_or_loc = match.group(1).upper()
            dest = match.group(2).upper()
            moves.append(f"{piece_or_loc} → {dest}")

        if not moves:
            print("⚠️ Invalid grammar detected:", text)
        else:
            print("Recognized:", text)
            print("Parsed move(s):", moves)

        time.sleep(0.3)

except KeyboardInterrupt:
    print("\nStopped.")


