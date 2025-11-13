#!/usr/bin/env python3
# coding: utf-8
#
# チェス音声対話 応答生成モジュール（簡易版）
# Julius出力の sentence1: 行のみ使用
# usage: python3 get.py dialogue_chess.conf raw_asr.txt
# ------------------------------------------------------

import os
import re
import subprocess
import sys
from pathlib import Path

JTALK_BIN = "open_jtalk"
VOICE_PATH = "/usr/share/hts-voice/nitech-jp-atr503-m001/nitech_jp_atr503_m001.htsvoice"
DICT_PATH = "/var/lib/mecab/dic/open-jtalk/naist-jdic"

OUTPUT_DIR = Path(os.environ.get("DIALOGUE_TMP", "/tmp/dialogue")).expanduser()
OUTPUT_WAV = OUTPUT_DIR / "out.wav"

def _run_cmd(cmd):
    return subprocess.run(
        cmd,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )

def play_audio() -> None:
    """再生コマンドを順番に試す"""
    candidates = [
        ["play", "-q", str(OUTPUT_WAV)],
        ["aplay", "-q", str(OUTPUT_WAV)],
    ]
    errors = []
    for cmd in candidates:
        try:
            _run_cmd(cmd)
            return
        except FileNotFoundError:
            errors.append(f"{cmd[0]} が見つかりません。")
        except subprocess.CalledProcessError as exc:
            err = exc.stderr.decode("utf-8", errors="ignore").strip().splitlines()
            err_msg = err[0] if err else "(no detail)"
            errors.append(f"{cmd[0]} 失敗 code={exc.returncode}: {err_msg}")
    print("[WARN] 音声再生に失敗しました: " + " / ".join(errors))

NOISE_WORDS = {"uh", "um", "ah", "sp", "silB", "silE"}

def synthesize(answer: str) -> None:
    """合成音声を生成して再生する"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    cmd = [
        JTALK_BIN,
        "-m",
        VOICE_PATH,
        "-ow",
        str(OUTPUT_WAV),
        "-x",
        DICT_PATH,
    ]

    try:
        subprocess.run(
            cmd,
            input=f"{answer}\n".encode("utf-8"),
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
    except FileNotFoundError:
        print("[ERROR] open_jtalk が見つかりません。")
        return
    except subprocess.CalledProcessError as exc:
        err = exc.stderr.decode("utf-8", errors="ignore").strip()
        detail = f" code={exc.returncode}" if exc.returncode else ""
        if err:
            print(f"[ERROR] 音声合成に失敗しました{detail}: {err}")
        else:
            print(f"[ERROR] 音声合成に失敗しました{detail}.")
        return

    if not OUTPUT_WAV.exists() or OUTPUT_WAV.stat().st_size == 0:
        print("[ERROR] 音声ファイルの生成に失敗しました。")
        if OUTPUT_WAV.exists():
            OUTPUT_WAV.unlink()
        return

    try:
        play_audio()
    finally:
        if OUTPUT_WAV.exists():
            OUTPUT_WAV.unlink()

def load_reply_dict(conf_path: str) -> dict:
    """dialogue_chess.conf を読み込む"""
    reply = {}
    with open(conf_path, "r", encoding="utf-8") as conf:
        for line in conf:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = re.split(r"\s{2,}|\t", line)
            if len(parts) >= 2:
                key = parts[0].strip()
                val = parts[1].strip()
                reply[key] = val
    return reply

def extract_sentence(asr_path: str) -> str:
    """Julius 出力から sentence1 行を抽出"""
    text = open(asr_path, encoding="utf-8", errors="ignore").read()
    m = re.search(r"sentence1:\s*(.*)", text)
    if not m:
        print("[WARN] 認識結果なし")
        return ""
    sentence = m.group(1)
    sentence = re.sub(r"\s+", " ", sentence).strip()
    return sentence

def filter_noise(sentence: str) -> str:
    tokens = re.split(r"\s+", sentence)
    return " ".join([t for t in tokens if t and t not in NOISE_WORDS])

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 get.py dialogue_chess.conf raw_asr.txt")
        return

    conf_path, asr_path = sys.argv[1], sys.argv[2]
    if not os.path.exists(conf_path):
        print(f"[ERROR] 応答辞書が見つかりません: {conf_path}")
        return

    reply = load_reply_dict(conf_path)
    sentence = extract_sentence(asr_path)
    print(f"RAW: {sentence}")
    filtered = filter_noise(sentence)
    print(f"FILTERED: {filtered}")

    answer = reply.get(filtered, "もう一度お願いします")
    print(f"Silly: {answer}")

    synthesize(answer)

if __name__ == "__main__":
    main()
