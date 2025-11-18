# Tkinter チェス GUI デモ
# - 左: python-chess の盤面 (SVG → PNG → Tkinter)
# - 右: 履歴ログ + コマンド入力 + 残りタイムバー
#
# 必要パッケージ:
#   pip install python-chess pillow cairosvg
# ------------------------------------------------------

import io
import time
import tkinter as tk
from tkinter import ttk

import chess
import chess.svg
from PIL import Image, ImageTk
import cairosvg


class ChessGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Chess GUI Demo")

        # 盤面
        self.board = chess.Board()

        # ---- 左側：盤面表示 ----
        self.board_label = tk.Label(self.root)
        self.board_label.grid(row=0, column=0, padx=10, pady=10)

        # ---- 右側：履歴・入力・タイマー ----
        side_frame = tk.Frame(self.root)
        side_frame.grid(row=0, column=1, sticky="ns", padx=10, pady=10)

        # Move 履歴
        tk.Label(side_frame, text="Move History").pack(anchor="w")
        self.history_box = tk.Text(side_frame, width=30, height=20)
        self.history_box.pack(pady=5)

        # 入力フィールド
        tk.Label(side_frame, text="Command Input (例: e2e4, Nf3, quit)").pack(anchor="w")
        self.cmd_entry = tk.Entry(side_frame)
        self.cmd_entry.pack(pady=5, fill="x")
        self.cmd_entry.bind("<Return>", self.on_enter)

        # 残り時間バー
        tk.Label(side_frame, text="Response Timer (seconds)").pack(anchor="w", pady=(10, 0))
        self.timer_var = tk.DoubleVar(value=5.0)
        self.timer_bar = ttk.Progressbar(
            side_frame, maximum=5.0, length=200, variable=self.timer_var
        )
        self.timer_bar.pack(pady=5)

        self.timer_label = tk.Label(side_frame, text="5.0 s")
        self.timer_label.pack(anchor="w")

        # タイマー値と設定
        self.remaining = 5.0    # 秒
        self.timer_interval = 0.1  # 更新間隔 [s]

        # 盤面初期描画
        self.board_img = None
        self.update_board_image()

        # タイマー開始
        self.update_timer()

    # -------------------------------------------------------
    # タイマー (Tkinter の after でメインスレッド内更新)
    # -------------------------------------------------------
    def update_timer(self):
        self.remaining -= self.timer_interval
        if self.remaining <= 0:
            self.remaining = 5.0  # デモなのでタイムアウト時はリセットだけ

        # GUI 反映
        self.timer_var.set(self.remaining)
        self.timer_label.config(text=f"{self.remaining:0.1f} s")

        # 100msごとに再度呼び出し
        self.root.after(int(self.timer_interval * 1000), self.update_timer)

    # -------------------------------------------------------
    # Board を SVG → PNG に変換して Tkinter に表示
    # -------------------------------------------------------
    def update_board_image(self):
        # python-chess で SVG 文字列生成
        svg_data = chess.svg.board(self.board).encode("utf-8")

        # CairoSVG で SVG → PNG (bytes)
        png_bytes = cairosvg.svg2png(bytestring=svg_data)

        # Pillow で PNG 読み込み
        png = Image.open(io.BytesIO(png_bytes))
        png = png.resize((400, 400), Image.LANCZOS)

        # Tkinter 用に変換
        self.board_img = ImageTk.PhotoImage(png)
        self.board_label.config(image=self.board_img)

    # -------------------------------------------------------
    # コマンド入力 (Enterキー)
    # -------------------------------------------------------
    def on_enter(self, event=None):
        cmd = self.cmd_entry.get().strip()
        self.cmd_entry.delete(0, tk.END)

        if cmd == "":
            return

        # 終了コマンド
        if cmd.lower() == "quit":
            self.root.destroy()
            return

        # タイマーリセット
        self.remaining = 5.0

        # SAN / UCI 両対応で指し手解釈
        move = None
        try:
            # SAN (例: Nf3, Qh5+, O-O)
            move = self.board.parse_san(cmd)
        except Exception:
            try:
                # UCI (例: e2e4, g1f3)
                move = chess.Move.from_uci(cmd)
                if move not in self.board.legal_moves:
                    raise ValueError
            except Exception:
                self.history_box.insert(tk.END, f"Invalid: {cmd}\n")
                self.history_box.see(tk.END)
                return

        # 指し手実行
        self.board.push(move)
        self.history_box.insert(tk.END, cmd + "\n")
        self.history_box.see(tk.END)

        # 盤面更新
        self.update_board_image()


def main():
    root = tk.Tk()
    app = ChessGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()