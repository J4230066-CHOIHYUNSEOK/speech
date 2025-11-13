#!/usr/bin/env python3
# coding: utf-8
#
# Julius 出力をそのまま表示＋cms評価
# usage: python3 get.py dialogue_chess.conf raw_asr.txt
# ------------------------------------------------------

import os
import re
import subprocess
import sys
from pathlib import Path
import statistics

JTALK_BIN = "open_jtalk"
VOICE_PATH = "/usr/share/hts-voice/nitech-jp-atr503-m001/nitech_jp_atr503_m001.htsvoice"
DICT_PATH = "/var/lib/mecab/dic/open-jtalk/naist-jdic"

OUTPUT_DIR = Path(os.environ.get("DIALOGUE_TMP", "/tmp/dialogue")).expanduser()
OUTPUT_WAV = OUTPUT_DIR / "out.wav"
CMS_THRESHOLD = 0.4
NOISE_WORDS = {"uh", "um", "ah", "sp", "silB", "silE"}

# ---------------- util ----------------
def _run_cmd(cmd):
    return subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

def play_audio():
    for cmd in (["play", "-q", str(OUTPUT_WAV)], ["aplay", "-q", str(OUTPUT_WAV)]):
        try:
            _run_cmd(cmd)
            return
        except Exception:
            continue
    print("[WARN] 音声再生に失敗しました。")

def synthesize(answer: str):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    cmd = [JTALK_BIN, "-m", VOICE_PATH, "-ow", str(OUTPUT_WAV), "-x", DICT_PATH]
    try:
        subprocess.run(cmd, input=f"{answer}\n".encode("utf-8"),
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        play_audio()
    except Exception as e:
        print(f"[ERROR] 音声合成に失敗: {e}")
    finally:
        if OUTPUT_WAV.exists():
            OUTPUT_WAV.unlink()

# ---------------- core ----------------
def extract_julius_info(asr_path: str):
    """sentence1 と cmscore1 抽出"""
    text = open(asr_path, encoding="utf-8", errors="ignore").read()
    print("===== Julius raw_asr.txt 全文 =====")
    print(text)
    print("==================================")

    s_m = re.search(r"sentence1:\s*(.*)", text)
    c_m = re.search(r"cmscore1:\s*([0-9\.\s]+)", text)
    if not s_m:
        print("[WARN] sentence1 が見つかりません")
        return "", []
    sentence = re.sub(r"\s+", " ", s_m.group(1)).strip()
    cms = []
    if c_m:
        try:
            cms = [float(x) for x in c_m.group(1).split()]
        except ValueError:
            cms = []
    return sentence, cms

def filter_noise(tokens, cms):
    kept_tokens, kept_cms = [], []
    for t, c in zip(tokens, cms):
        if t not in NOISE_WORDS:
            kept_tokens.append(t)
            kept_cms.append(c)
    return kept_tokens, kept_cms

# ---------------- main ----------------
def main():
    if len(sys.argv) < 3:
        print("Usage: python3 get.py dialogue_chess.conf raw_asr.txt")
        return

    conf_path, asr_path = sys.argv[1], sys.argv[2]
    if not os.path.exists(asr_path):
        print(f"[ERROR] Julius出力が見つかりません: {asr_path}")
        return

    sentence, cms = extract_julius_info(asr_path)
    if not sentence:
        synthesize("もう一度お願いします")
        return

    tokens = re.split(r"\s+", sentence.strip())
    tokens_f, cms_f = filter_noise(tokens, cms)

    print("=== ノイズ除去結果 ===")
    print("Tokens :", tokens_f)
    print("CMS    :", ["{:.3f}".format(c) for c in cms_f])

    mean_cms = statistics.mean(cms_f) if cms_f else 0.0
    print(f"平均CMS: {mean_cms:.3f}")

    if mean_cms < CMS_THRESHOLD:
        print("→ 信頼度が低いので再入力を要求")
        synthesize("もう一度お願いします")
    else:
        text = " ".join(tokens_f)
        print(f"確定文: {text}")
        synthesize(text)

if __name__ == "__main__":
    main()
