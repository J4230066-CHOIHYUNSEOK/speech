#!/bin/bash
# ============================================
# 音声対話システム（チェス版）
# 録音 → Julius認識 → 応答生成(get.py) → 音声合成
# ============================================

tmpdirname=/tmp/dialogue_chess
mkdir -p $tmpdirname

# get.py からも参照できるようにテンポラリディレクトリを共有
export DIALOGUE_TMP=$tmpdirname

while true; do
    # --- 音声録音 ---
    filename=${tmpdirname}/input.wav
    echo "[録音中] 話しかけてください (Ctrl-Cで終了)"
    adinrec $filename > /dev/null

    # Ctrl-C等で録音が止まった場合の処理
    [ ! -e $filename ] && rmdir $tmpdirname && exit

    # --- 音声認識 (Julius) ---
    asr_raw=${tmpdirname}/raw_asr.txt
    asr_result=${tmpdirname}/asr_result.txt
    echo $filename > ${tmpdirname}/list.txt

    julius -C asr/grammar.jconf -filelist ${tmpdirname}/list.txt -n 1 -output 3 > ${asr_raw} 2>&1

    rm ${tmpdirname}/list.txt

    # --- 結果統合・ノイズ除去・応答生成 ---
    python3 get.py dialogue/dialogue_chess.conf ${asr_raw}

    # 後処理
    rm $filename ${asr_raw} 2>/dev/null
done

rmdir $tmpdirname