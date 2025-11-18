# Chess Voice System

Tkinter GUI で、音声対話フローをキーボード入力で模倣するモックです。  

## 起動

```bash
cd chess_system
python main.py
```

GUI が立ち上がったら、bash上にmを入力することでwake wordを録音してください。  
mが入力されたあとの二秒間録音されます。  
事前に用意された音声ファイルがあればvoice_recog/refに入れてください。  
サンプルwav fileの名前は sample.wavに設定してください。

## FSM モード

1. **WAIT_WAKE**  
   - 常に「wake word」を待っています。  
   - `hey chess` (英語) を入力すると ROOT へ。

2. **ROOT**  
   - 10秒内にplay <move>かimagineと言ってください。  
   - `play <move>` : 即座に実盤に適用し、エンジン応手後 WAIT_WAKE へ戻ります。`<move>` は SAN/ UCI どちらでも OK。  
- `imagine` : IMAGINE モードへ（盤面が青みがかった配色に変わることで、仮想盤を操作中であることがわかります）。
   - 10秒無入力 WAIT_WAKE に戻ります。

3. **IMAGINE_MODE** 
   - 読み筋シミュレータ。`<move>` で仮想盤面を進められます。  
- `take` : Stockfish の候補手を仮想盤面に適用。  
- `back` : IMAGINE 中に加えた指し手を 1 手だけ取り消す（開始位置まで戻るとそれ以上は undo できません）。  
   - `stop` : 状態維持（タイマーのみリセット）。  
   - `return` : 実盤 (ROOT) に戻る。 
   - `back` : 一個前に戻る
   - 30 秒無入力で WAIT_WAKE に落ちます。

## GUI の見方

- **History**: 入力と FSM ログ、エンジン手、ボード文字表示などが流れます。  
- **Command Input**: すべての操作はここで打鍵することでも作動できます。  
- **Timer**: 現在の状態の残り秒数。ROOT / IMAGINE で独立して作動。  
- **Board Tint**: IMAGINE 中は 青系のフィルタが被さり、仮想盤であることが視覚的にわかります。

## 注意点 
- `StockfishEngine` は `/usr/games/stockfish` で起動します。別パスの場合はコンストラクタを修正してください。

