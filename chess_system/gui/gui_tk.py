# gui/gui_tk.py
# --------------------------------------------------
# Tkinter GUI 盤面表示＋コマンド入力＋ログ＋タイムバー
# FSM と独立して動き、main.py から「FSM を渡して」
# 入力を FSM に流す構造になっている。
# --------------------------------------------------

import io
import tkinter as tk
from tkinter import ttk

import chess
import chess.svg
from PIL import Image, ImageTk
import cairosvg


class ChessGUI:
    def __init__(self, root, fsm_controller, timer):
        """
        root: Tk()
        fsm_controller: FSMController インスタンス
        timer: Timer オブジェクト（util/timer.py）
        """
        self.root = root
        self.fsm = fsm_controller
        self.timer = timer

        self.root.title("Chess Voice System GUI")

        # 盤面表示用ラベル
        self.board_label = tk.Label(self.root)
        self.board_label.grid(row=0, column=0, padx=10, pady=10)

        # ----- 右側パネル -----
        side = tk.Frame(self.root)
        side.grid(row=0, column=1, sticky="ns", padx=10, pady=10)

        # Move 履歴
        tk.Label(side, text="History").pack(anchor="w")
        self.history_box = tk.Text(side, width=32, height=20)
        self.history_box.pack(pady=4)

        # コマンド入力欄
        tk.Label(side, text="Command Input").pack(anchor="w")
        self.cmd_entry = tk.Entry(side)
        self.cmd_entry.pack(fill="x", pady=4)
        self.cmd_entry.bind("<Return>", self._on_enter)

        # タイマー
        tk.Label(side, text="Timer").pack(anchor="w")
        self.timer_var = tk.DoubleVar(value=self.timer.remaining)
        self.timer_bar = ttk.Progressbar(
            side,
            maximum=self.timer.max_time,
            length=200,
            variable=self.timer_var,
        )
        self.timer_bar.pack(pady=4)

        self.timer_label = tk.Label(side, text=f"{self.timer.remaining:.1f} s")
        self.timer_label.pack(anchor="w")

        # 盤面画像保持
        self.board_img = None

        # 初期描画
        self.update_board()

        # タイマー更新開始
        self._update_timer_bar()

    # ---------------------------------------------------------
    # GUI → FSM：コマンド入力
    # ---------------------------------------------------------
    def _on_enter(self, event=None):
        text = self.cmd_entry.get().strip()
        self.cmd_entry.delete(0, tk.END)

        if text == "":
            return

        # 1) 履歴に表示
        self.append_history(f"[Input] {text}")

        # 2) FSM に渡す
        self.fsm.handle_input(text)

        # 3) ボードが変化していれば更新
        self.update_board()

        # 4) タイマーをリセット（ROOT/PLAYなどのモードで使う）
        self.timer.reset()

    # ---------------------------------------------------------
    # ボード描画更新
    # ---------------------------------------------------------
    def update_board(self):
        board = self.fsm.board.board  # BoardManager の chess.Board

        svg_data = chess.svg.board(board).encode("utf-8")
        png_bytes = cairosvg.svg2png(bytestring=svg_data)

        img = Image.open(io.BytesIO(png_bytes))
        img = img.resize((400, 400), Image.LANCZOS)

        self.board_img = ImageTk.PhotoImage(img)
        self.board_label.config(image=self.board_img)

    # ---------------------------------------------------------
    # Move履歴 / ログ追加
    # ---------------------------------------------------------
    def append_history(self, text):
        self.history_box.insert("end", text + "\n")
        self.history_box.see("end")

    # ---------------------------------------------------------
    # タイマーとGUIバーの同期
    # ---------------------------------------------------------
    def _update_timer_bar(self):
        # タイマー値更新
        self.timer.tick(0.1)
        self.timer_bar.config(maximum=self.timer.max_time)
        self.timer_var.set(self.timer.remaining)
        self.timer_label.config(text=f"{self.timer.remaining:.1f} s")

        # 100msごとに呼ぶ
        self.root.after(100, self._update_timer_bar)
