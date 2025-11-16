import chess
from .stockfish_engine import StockfishEngine


class ImagineSimulator:
    def __init__(self, engine: StockfishEngine | None = None):
        self.engine = engine or StockfishEngine()
        self.base_board: chess.Board | None = None
        self.board: chess.Board | None = None
        self._history: list[chess.Move] = []

    def start(self, board: chess.Board):
        """Capture the current real board as the base for imagination."""
        self.base_board = board.copy()
        self.board = board.copy()
        self._history = []

    def reset(self):
        if self.base_board:
            self.board = self.base_board.copy()
        self._history = []

    def move(self, mov: str):
        if self.board is None:
            raise RuntimeError("ImagineSimulator not started")

        try:
            candidate = self.board.parse_san(mov)
        except Exception:
            candidate = chess.Move.from_uci(mov)

        if candidate not in self.board.legal_moves:
            raise ValueError("Illegal imagine move")

        self.board.push(candidate)
        self._history.append(candidate)

    def bestmove(self):
        if self.board is None:
            raise RuntimeError("ImagineSimulator not started")
        return self.engine.get_bestmove(self.board)

    def make_bestmove(self, move_uci: str):
        if self.board is None:
            raise RuntimeError("ImagineSimulator not started")
        if move_uci is None:
            return
        move = chess.Move.from_uci(move_uci)
        if move not in self.board.legal_moves:
            return
        self.board.push(move)
        self._history.append(move)

    def back(self):
        if self.board is None or not self._history:
            return False
        self.board.pop()
        self._history.pop()
        return True
