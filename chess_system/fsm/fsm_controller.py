import chess

from .states import State


class FSMController:
    ROOT_TIMEOUT = 10.0
    IMAGINE_TIMEOUT = 30.0

    def __init__(self, board_manager, imagine_sim, logger, timer, wake_detector):
        self.board = board_manager
        self.imag = imagine_sim
        self.log = logger
        self.timer = timer
        self.wake_detector = wake_detector

        self.state = None
        self.timer.on_timeout(self._handle_timeout)
        self._set_state(State.WAIT_WAKE)

    # ============================================================
    # External events
    # ============================================================
    def handle_input(self, text: str):
        text = text.strip()
        if text == "":
            return

        if self.state == State.WAIT_WAKE:
            self._handle_wait_wake(text)
        elif self.state == State.ROOT:
            self._handle_root(text)
        elif self.state == State.IMAGINE:
            self._handle_imagine(text)

    def _handle_timeout(self):
        if self.state == State.ROOT:
            self.log.write("ROOT timeout → WAIT_WAKE")
            self._set_state(State.WAIT_WAKE)
        elif self.state == State.IMAGINE:
            self.log.write("IMAGINE timeout → WAIT_WAKE")
            self._set_state(State.WAIT_WAKE)

    # ============================================================
    # State handlers
    # ============================================================
    def _handle_wait_wake(self, text: str):
        if self.wake_detector.detect(text):
            self.log.write("Wakeword detected → ROOT")
            self._set_state(State.ROOT)
        else:
            self.log.write("Waiting for wakeword. (type 'hey chess')", tag="INFO")

    def _handle_root(self, text: str):
        self.timer.reset()
        lowered = text.lower()

        if lowered.startswith("imagine"):
            self._set_state(State.IMAGINE)
            return

        if lowered.startswith("play"):
            move = text[4:].strip()
            if move:
                self._process_play_move(move)
            else:
                self.log.write("ROOT: say 'play <move>' to move, or 'imagine'.", tag="INFO")
            return

        self.log.write("ROOT: say 'play <move>' or 'imagine' to branch.", tag="INFO")

    def _handle_imagine(self, text: str):
        self.timer.reset()
        lowered = text.lower()

        if lowered == "return":
            self.log.write("IMAGINE: return → ROOT")
            self._set_state(State.ROOT)
            return

        if lowered == "stop":
            self.log.write("IMAGINE: stop (timer reset, stay in imagine)", tag="INFO")
            return

        if lowered == "back":
            if self.imag.back():
                self.log.write("IMAGINE: reverted one imagined move", tag="INFO")
            else:
                self.log.write("IMAGINE: nothing to undo", tag="INFO")
            return

        if lowered == "take":
            best = self.imag.bestmove()
            if best:
                self.imag.make_bestmove(best)
                self.log.write(f"Engine best move (imagine) → {best}")
                self.log.write_move(f"Imagine(Engine): {best}")
            else:
                self.log.write("Engine best move unavailable.")
            return

        try:
            self.imag.move(text)
            self.log.write(f"Imagine move: {text}")
            self.log.write_move(f"Imagine: {text}")
        except Exception:
            self.log.write(f"Invalid imagine move: {text}")

    # ============================================================
    # Helpers
    # ============================================================
    def _process_play_move(self, move_text: str):
        self.timer.reset()
        if not self._apply_main_move(move_text):
            self.log.write("ROOT: invalid move, try again or say wake word later.", tag="INFO")
            return

        # Valid move was made; refresh ROOT timer budget so follow-up commands (if any) start fresh
        self._engine_counter_move()
        self.timer.reset()
        self.log.write("Turn finished")

    def _apply_main_move(self, move_text: str):
        try:
            info = self.board.move(move_text)
            self.log.write(f"Move accepted: {info['san']} ({info['uci']})")
            self.log.write_move(f"Player: {info['san']} ({info['uci']})")
            self.log.write(f"Board:\n{self.board.board}", tag="BOARD")
            return True
        except Exception:
            self.log.write(f"Invalid move: {move_text}")
            return False

    def _engine_counter_move(self):
        reply = self.board.engine_reply()
        if reply:
            self.log.write(f"Engine move: {reply['san']} ({reply['uci']})", tag="ENGINE")
            self.log.write_move(f"Engine: {reply['san']} ({reply['uci']})")
            self.log.write(f"Board:\n{self.board.board}", tag="BOARD")
        else:
            self.log.write("Engine move unavailable or illegal.", tag="ENGINE")

    def _set_state(self, new_state: State):
        if self.state == new_state:
            return
        self._on_exit_state(self.state)
        self.state = new_state
        self._on_enter_state(new_state)

    def _on_enter_state(self, state: State):
        if state == State.WAIT_WAKE:
            self.timer.pause()
            self.timer.reset(restart=False)
            self.log.write("State → WAIT_WAKE (listening for wake word)")
        elif state == State.ROOT:
            self.timer.arm(self.ROOT_TIMEOUT, start=True)
            self.log.write("State → ROOT")
        elif state == State.IMAGINE:
            self.imag.start(self.board.board)
            self.timer.arm(self.IMAGINE_TIMEOUT, start=True)
            self.log.write("State → IMAGINE_MODE")

    def _on_exit_state(self, state: State | None):
        if state == State.IMAGINE:
            self.imag.reset()

    # ------------------------------------------------------------
    # State helpers for GUI
    # ------------------------------------------------------------
    def get_state(self) -> State:
        return self.state

    def get_display_board(self):
        if self.state == State.IMAGINE and self.imag.board:
            return self.imag.board
        return self.board.board

    # ------------------------------------------------------------
    # History helpers for GUI
    # ------------------------------------------------------------
    def get_game_moves(self) -> list[chess.Move]:
        """Return a copy of the main game move stack."""
        return list(self.board.board.move_stack)

    def get_imagine_moves(self) -> list[chess.Move]:
        """Return a copy of the imagine move stack."""
        return list(self.imag._history)

    def get_imagine_base_board(self) -> chess.Board | None:
        """Return the board state when IMAGINE started."""
        return self.imag.base_board
