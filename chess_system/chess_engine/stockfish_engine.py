import random

import chess
import chess.engine


class StockfishEngine:
    def __init__(self, path="/usr/games/stockfish", depth: int = 12):
        self.depth = depth
        self._engine = None
        try:
            self._engine = chess.engine.SimpleEngine.popen_uci(path)
        except (FileNotFoundError, chess.engine.EngineError, OSError):
            self._engine = None

    def get_bestmove(self, board: chess.Board) -> str | None:
        if self._engine:
            result = self._engine.play(board, chess.engine.Limit(depth=self.depth))
            return result.move.uci()

        # Fallback: return a random legal move so that imagine mode keeps moving.
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return None
        return random.choice(legal_moves).uci()

    def __del__(self):
        if self._engine:
            try:
                self._engine.quit()
            except Exception:
                pass
