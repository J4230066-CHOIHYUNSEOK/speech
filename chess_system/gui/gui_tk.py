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
import cairosvg
import cv2
import numpy as np
from PIL import Image, ImageTk

from fsm.states import State


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
        self._last_state = self.fsm.get_state()

        self.root.title("Chess Voice System")
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

        # 盤面表示用ラベル
        self.board_label = tk.Label(self.root)
        self.board_label.grid(row=0, column=0, padx=10, pady=10)

        # ----- 右側パネル -----
        side = tk.Frame(self.root)
        side.grid(row=0, column=1, sticky="ns", padx=10, pady=10)

        # Move 履歴
        tk.Label(side, text="History").pack(anchor="w")
        self.history_box = tk.Text(side, width=32, height=20, state="disabled")
        self.history_box.pack(pady=4)

        # コマンド入力欄 いつか消す
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

        bottom = tk.Frame(self.root)
        bottom.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 10))
        bottom.grid_columnconfigure(0, weight=1)
        tk.Label(bottom, text="FSM Messages").grid(row=0, column=0, sticky="w")
        self.message_box = tk.Text(
            bottom, width=80, height=3, wrap="word", state="disabled", font=("Consolas",16)
        )
        self.message_box.grid(row=1, column=0, sticky="ew")

        # 盤面画像保持
        self.board_img = None

        # 初期描画
        self.update_board()
        self.refresh_history()

        # タイマー更新開始
        self._update_timer_bar()

    # ---------------------------------------------------------
    # GUI → FSM：コマンド入力
    # ---------------------------------------------------------
    def _on_enter(self, event=None):
        text = self.cmd_entry.get().strip()
        self.cmd_entry.delete(0, tk.END)

        self.process_text(text)

    def process_text(self, text: str):
        """Centralized handler so both GUI entry and voice bridge share the same flow."""
        text = text.strip()
        if text == "":
            return

        # FSM に渡す
        self.fsm.handle_input(text)

        # ボードが変化していれば更新
        self.update_board()
        self.refresh_history()

        # タイマーをリセット（ROOT/PLAYなどのモードで使う）
        self.timer.reset()

    # ---------------------------------------------------------
    # ボード描画更新
    # ---------------------------------------------------------
    def update_board(self):
        board = self.fsm.get_display_board()

        svg_data = chess.svg.board(board).encode("utf-8")
        png_bytes = cairosvg.svg2png(bytestring=svg_data)

        img = Image.open(io.BytesIO(png_bytes)).convert("RGB")
        if self.fsm.get_state() == State.IMAGINE:
            img = self._apply_imagine_tint(img)
        img = img.resize((400, 400), Image.LANCZOS)

        self.board_img = ImageTk.PhotoImage(img)
        self.board_label.config(image=self.board_img)

    # ---------------------------------------------------------
    # Move履歴 / ログ追加
    # ---------------------------------------------------------
    def refresh_history(self):
        """Rebuild the history panel using proper move numbering."""
        main_moves = self.fsm.get_game_moves()
        imagine_moves = self.fsm.get_imagine_moves()
        history_parts = []

        main_text = self._format_move_pairs(chess.Board(), main_moves)
        if main_text:
            history_parts.append(main_text)

        base = self.fsm.get_imagine_base_board()
        if base and imagine_moves:
            imag_text = self._format_move_pairs(base, imagine_moves)
            if imag_text:
                history_parts.append("Imagine:\n" + imag_text)

        if history_parts:
            combined = "\n\n".join(history_parts)
        else:
            combined = ""

        self._write_text(self.history_box, combined, append=False)

    def show_fsm_message(self, text: str, tag: str = "FSM"):
        """Display only the latest FSM message (clears previous content)."""
        self._write_text(self.message_box, f"[{tag}] {text}", append=False)

    # ---------------------------------------------------------
    # タイマーとGUIバーの同期
    # ---------------------------------------------------------
    def _update_timer_bar(self):
        # タイマー値更新
        self.timer.tick(0.1)
        self.timer_bar.config(maximum=self.timer.max_time)
        self.timer_var.set(self.timer.remaining)
        self.timer_label.config(text=f"{self.timer.remaining:.1f} s")
        current_state = self.fsm.get_state()
        if current_state != self._last_state:
            self._last_state = current_state
            self.update_board()

        # 100msごとに呼ぶ
        self.root.after(100, self._update_timer_bar)

    def _apply_imagine_tint(self, image: Image.Image) -> Image.Image:
        """Apply a subtle blue overlay using OpenCV so IMAGINE mode is obvious."""
        rgb_array = np.array(image)
        bgr = cv2.cvtColor(rgb_array, cv2.COLOR_RGB2BGR)
        overlay = np.full(bgr.shape, (255, 180, 80), dtype=np.uint8) 
        tinted = cv2.addWeighted(bgr, 0.65, overlay, 0.35, 0)
        tinted_rgb = cv2.cvtColor(tinted, cv2.COLOR_BGR2RGB)
        return Image.fromarray(tinted_rgb)

    def _write_text(self, widget: tk.Text, text: str, append: bool):
        widget.config(state="normal")
        if not append:
            widget.delete("1.0", "end")
        widget.insert("end", text)
        widget.see("end")
        widget.config(state="disabled")

    def _format_move_pairs(self, base_board: chess.Board, moves: list[chess.Move]) -> str:
        """Return PGN-like lines (e.g., '1. e4 e5') for the given move list."""
        if not moves:
            return ""

        board = base_board.copy()
        lines = []
        idx = 0

        while idx < len(moves):
            move_num = board.fullmove_number
            if board.turn == chess.WHITE:
                white_move = moves[idx]
                white_san = board.san(white_move)
                board.push(white_move)
                idx += 1

                black_san = ""
                if idx < len(moves):
                    black_move = moves[idx]
                    black_san = board.san(black_move)
                    board.push(black_move)
                    idx += 1

                line = f"{move_num}. {white_san}"
                if black_san:
                    line += f" {black_san}"
            else:
                # Black to move at this ply (rare but possible if starting mid-game)
                black_move = moves[idx]
                black_san = board.san(black_move)
                board.push(black_move)
                idx += 1

                line = f"{move_num}... {black_san}"
                if idx < len(moves):
                    white_move = moves[idx]
                    white_san = board.san(white_move)
                    board.push(white_move)
                    idx += 1
                    line += f" {white_san}"

            lines.append(line)

        return "\n".join(lines)
