#!/usr/bin/env python3
import subprocess
import time
import os
from pathlib import Path

TMPDIR = Path("/tmp/dialogue_chess")
TMPDIR.mkdir(parents=True, exist_ok=True)
os.environ["DIALOGUE_TMP"] = str(TMPDIR)

def record_audio(filename):
    print("[録音中] 話しかけてください (Ctrl-Cで終了)")
    subprocess.run(["adinrec", filename], stdout=subprocess.DEVNULL)

def run_julius(wavfile, outtxt):
    listfile = TMPDIR / "list.txt"
    listfile.write_text(str(wavfile) + "\n")

    cmd = [
        "julius",
        "-C", "asr/grammar.jconf",
        "-filelist", str(listfile),
        "-n", "1",
        "-output", "3",
    ]
    with open(outtxt, "w") as f:
        subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT)

    listfile.unlink()

def run_getpy(rawtxt):
    subprocess.run(
        ["python3", "get.py", "dialogue/dialogue_chess.conf", rawtxt]
    )

def main_loop():
    while True:
        wavfile = TMPDIR / "input.wav"
        rawtxt  = TMPDIR / "raw_asr.txt"

        record_audio(str(wavfile))

        if not wavfile.exists():
            TMPDIR.rmdir()
            return

        run_julius(str(wavfile), str(rawtxt))
        run_getpy(str(rawtxt))

        # 後処理
        try:
            wavfile.unlink()
            rawtxt.unlink()
        except:
            pass

if __name__ == "__main__":
    main_loop()
