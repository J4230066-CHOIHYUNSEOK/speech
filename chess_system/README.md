# Chess Voice System (Keyboard Prototype)

Tkinter GUI で、音声対話フローをキーボード入力で模倣するモックです。  
いまはあくまで「後で Julius やマイク入力に差し替える」前提の FSM テスト用です。

## 起動

```bash
pip install -r chess_system/requirements.txt
python3 -m chess_system.main
```

GUI が立ち上がったら、右側の `Command Input` にテキストをタイプして Enter を押して進行します。

## FSM モード

1. **WAIT_WAKE**  
   - 常に「wake word」を待っています。  
   - `hey chess` (英語) を入力すると ROOT へ。

2. **ROOT_COMMAND_MODE**  
   - 5 秒以内にコマンド入力。  
   - `play <move>` : PLAY モードへ。`<move>` は SAN/ UCI どちらでも OK。  
     - ここで `play` だけ入力すると、続く PLAY モードでユーザー手を受け付けます。  
- `imagine` : IMAGINE モードへ（盤面が青みがかった配色に変わり、仮想盤を操作中であることがわかります）。
   - 5 秒無入力で WAIT_WAKE に戻ります。

3. **PLAY_MODE**  
   - 実際の対局想定モード。ユーザー手入力後、即座に Stockfish の応手が入り、ターン終了とともに WAIT_WAKE に戻ります。  
   - `stop` : 途中終了して WAIT_WAKE。
   - 不正手の場合は再入力を促します。

4. **IMAGINE_MODE** 
   - 読み筋シミュレータ。`<move>` で仮想盤面を進められます。  
- `take` : Stockfish の候補手を仮想盤面に適用。  
- `back` : IMAGINE 中に加えた指し手を 1 手だけ取り消す（開始位置まで戻るとそれ以上は undo できません）。  
   - `stop` : 状態維持（タイマーのみリセット）。  
   - `return` : 実盤 (ROOT) に戻る。 
   - `back` : 一個前に戻る
   - 30 秒無入力で WAIT_WAKE に落ちます。

## GUI の見方

- **History**: 入力と FSM ログ、エンジン手、ボード文字表示などが流れます。  
- **Command Input**: すべての操作はここで打鍵します。  
- **Timer**: 現在の状態の残り秒数。ROOT / PLAY / IMAGINE で独立して作動。  
- **Board Tint**: IMAGINE 中は OpenCV で青系のフィルタが被さり、仮想盤であることが視覚的にわかります。

## 今後の置き換えポイント

- `input/wake_detector_mock.py` と GUI でのテキスト入力は、将来的に Julius/音声認識結果に差し替える想定です。  
- `StockfishEngine` は `/usr/games/stockfish` で起動します。別パスの場合はコンストラクタを修正してください。

以上の構成で、キーボードだけで想定の音声対話シナリオを再現できます。
'
