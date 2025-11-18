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

        mov = mov.strip()
        candidate = self._parse_move(mov)

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

    def _parse_move(self, mov: str) -> chess.Move:
        if self.board is None:
            raise RuntimeError("ImagineSimulator not started")
        if mov.lower() == "castle":
            return self._castle_move()
        try:
            return self.board.parse_san(mov)
        except Exception:
            candidate = chess.Move.from_uci(mov)
        return candidate

    def _castle_move(self) -> chess.Move:
        """Try short castle first, then long castle for the imagined board."""
        assert self.board is not None
        if self.board.turn == chess.WHITE:
            candidates = ["e1g1", "e1c1"]
        else:
            candidates = ["e8g8", "e8c8"]

        for uci in candidates:
            move = chess.Move.from_uci(uci)
            if move in self.board.legal_moves and self.board.is_castling(move):
                return move
        raise ValueError("Illegal imagine move")
