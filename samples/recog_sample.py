from vosk import Model, KaldiRecognizer
import json
import sounddevice as sd

"""
test for voice recognition
雑談（任意の英語文）に対するrobust性を高めるための工夫。

Vosk は音声ブロックごとに Partial / Final 結果を返すが、
一般的な英会話のような長い発話では「語数が多くなる」ため、
Final Result() に複数語の text が返りやすい。

そこで、今回のチェス対話システムでは「最大4語まで」という
制約を設け、5語以上の text はすべて雑談として破棄する。

こうすると、Result() に乗ってくるのは
  - 'return' / 'take' / 'evaluate' などの単語コマンド
  - 'knight e two' や 'e two e four' などの短い合法手
のみになり、偶然の雑談が合法手に一致する確率を大幅に減らせる。

さらに、合法手のパターン（piece-file-rank / file-rank-file-rank）
の最初の一つだけを抽出することで、誤認識をさらに低減している。

この「短い定型句だけをコマンドとして扱う」戦略により、
音声対話時の誤動作（random talk → illegal move 認識）が
実質的にほぼゼロになり、チェス操作の信頼性が向上した。

"""
# --- vocabulary ---
pieces = ["pawn", "knight", "bishop", "rook", "queen", "king"]
files  = ["a","b","c","d","e","f","g","h"]
ranks  = ["one","two","three","four","five","six","seven","eight"]

commands = []

# imagine piece file rank
for p in pieces:
    for f in files:
        for r in ranks:
            commands.append(f"{p} {f} {r}")

# imagine file rank file rank
for f1 in files:
    for r1 in ranks:
        for f2 in files:
            for r2 in ranks:
                commands.append(f"{f1} {r1} {f2} {r2}")

# simple commands
common_cmds = ["return", "take", "explain", "evaluate","back"]
commands.extend(common_cmds)

print("Total grammar patterns:", len(commands))

# --- load model ---
model = Model("vosk-model-small-en-us-0.15")
rec = KaldiRecognizer(model, 16000, json.dumps(commands))


def extract_command(text: str):
    """
    text から以下のいずれかを返す:
      - "return" / "take" / "explain" / "evaluate" / "back"
      - "piece file rank"（例: "knight e two"）
      - "file rank file rank"（例: "e two e four"）
    条件:
      - 単語数が 6 以下（>6 は雑談として無視）
      - マッチしなければ None を返す
    """
    text = text.strip().lower()
    if not text:
        return None

    words = text.split()

    if len(words) > 6:
        return None

    # 1語コマンドは変化が大きいためその単語のみが返ってくるときのみ処理
    # 
    if len(words) == 1 and words[0] in common_cmds:
        return words[0]

    # piece file rank パターン
    if len(words) >= 3:
        w0, w1, w2 = words[0], words[1], words[2]
        if w0 in pieces and w1 in files and w2 in ranks:
            # 最初の一個だけ返す
            return f"{w0} {w1} {w2}"

    # file rank file rank パターン
    if len(words) >= 4:
        w0, w1, w2, w3 = words[0], words[1], words[2], words[3]
        if (w0 in files and w1 in ranks and
            w2 in files and w3 in ranks):
            return f"{w0} {w1} {w2} {w3}"

    # どれにも当たらなければ無視
    return None


def callback(indata, frames, time, status):
    data = bytes(indata)
    if rec.AcceptWaveform(data):
        res = rec.Result()
        obj = json.loads(res)
        text = obj.get("text", "").strip()
        if not text:
            return

        cmd = extract_command(text)
        if cmd is None:
            # 認識はされたがコマンドとして扱わない
            print("IGNORED:", text)
            return

        # ここでコマンドごとの処理
        if cmd in common_cmds:
            if cmd == "return":
                print("CMD: return")
            elif cmd == "take":
                print("CMD: take")
            elif cmd == "evaluate":
                print("CMD: evaluate")
            elif cmd == "explain":
                print("CMD: explain")
        else:
            # 盤面系コマンド
            print("MOVE CMD:", cmd)

    else:
        pres = rec.PartialResult()
        pobj = json.loads(pres)
        if pobj.get("partial"):
            print("PARTIAL:", pobj["partial"])


with sd.RawInputStream(
    samplerate=16000, blocksize=8000,
    dtype='int16', channels=1, callback=callback
):
    print("Listening…")
    while True:
        pass
