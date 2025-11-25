# 後期実験  音声対話システムの構築 Vocal_Chess

## セットアップ（Ubuntu）

ターミナルで以下を実行します。

```bash
bash install.sh          # 依存パッケージ＋仮想環境(.speech)作成
```

### conda環境が有効な場合の注意
PortAudio が conda の libstdc++ と衝突することがあります。その場合はシステムの libstdc++ を優先して起動してください。

```bash
env LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu \
    LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libstdc++.so.6 \
    .speech/bin/python chess_system/main.py
```
## 起動
```bash
source .speech/bin/activate
python chess_system/main.py
```
GUI が立ち上がったら、ターミナルで `m` + Enter を押すと始まります。  
`voice_recog/ref/sample.wav` に "hey chess" のサンプルが入っているので、それがwake wordとして使われています。   
認識が弱い／別の wake word にしたい場合のみ `sample.wav` を削除してから      
プログラムを実行してください。そしたら `m` + Enter 後の 2 秒が録音され、その音声が新しい wake word になります。  
自前の音声ファイルを使うなら `voice_recog/ref/sample.wav` として置き換えてください。
## モード

1. **WAIT_WAKE**  
   - 常に「wake word」を待っています。(default: "Hey chess")

2. **ROOT**  
- コマンド一覧
   - `play <move>` : 即座に実盤に適用し、エンジン応手後 WAIT_WAKE へ戻ります。`<move>` は SAN/ UCI どちらでも OK。(e.g. play e4)
   - `imagine` : IMAGINE モードへ（盤面が青みがかった配色に変わることで、仮想盤を操作中であることがわかります）。
- 10秒無入力 WAIT_WAKE に戻ります。

3. **IMAGINE_MODE(読み筋シミュレータ)**   
- コマンド一覧
   - `<move>` : `play <move>`ではなく`<move>` だけで仮想盤面を進められます。  
   - `take` : Stockfish の候補手を仮想盤面に適用。  
   - `back` : IMAGINE 中に加えたmoveを 1 手だけ取り消す（開始位置まで戻るとそれ以上は undo できません）。  
   - `stop` : 状態維持（タイマーのみリセット）。  
   - `return` : 実盤 (ROOT) に戻る。 
- 30 秒無入力で WAIT_WAKE に落ちます。

### Vocal Chessのフローチャート  
![flowchart](https://github.com/user-attachments/assets/3d25a14d-0147-4b27-a2cc-e8dee00f19b3)  

## GUI の見方

![GUI](https://github.com/user-attachments/assets/7e838b3d-ddd4-4030-9d42-c5ea3847bce5)  
- **History**: move履歴が流れます。Imagine modeからreturnすると Imagineの履歴は消されます。  
- **Command Input**: すべての操作はここで打鍵することでも作動できます。  
- **Timer**: 現在の状態の残り時間 

## 注意点 
- `StockfishEngine` は `/usr/games/stockfish` で起動するようにしています。別パスの場合は`chess_engine/stockfish_engine.py`よりパスを修正してください。

### スライド
google slides リンク : [発表スライド](https://docs.google.com/presentation/d/1khmnrlEGaAiaSV3vvXJcYtvVh47HnAIGV0-X4NQ5l_k/edit?usp=sharing)

