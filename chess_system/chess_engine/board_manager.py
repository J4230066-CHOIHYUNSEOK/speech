import chess


class BoardManager:
    def __init__(self, engine=None):
        self.board = chess.Board()
        self.engine = engine

    def move(self, uci_or_san):
        move = self._parse_move(uci_or_san)
        san = self.board.san(move)
        uci = move.uci()
        self.board.push(move)
        return {"uci": uci, "san": san}

    def engine_reply(self):
        if not self.engine:
            return None
        reply_uci = self.engine.get_bestmove(self.board)
        if not reply_uci:
            return None
        move = chess.Move.from_uci(reply_uci)
        if move not in self.board.legal_moves:
            return None
        san = self.board.san(move)
        self.board.push(move)
        return {"uci": reply_uci, "san": san}

    def _parse_move(self, text):
        try:
            move = self.board.parse_san(text)
        except Exception:
            move = chess.Move.from_uci(text)

        if move not in self.board.legal_moves:
            raise ValueError("Illegal move")
        return move
