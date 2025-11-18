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
        text = text.strip()
        if text.lower() == "castle":
            return self._castle_move(self.board)
        try:
            move = self.board.parse_san(text)
        except Exception:
            move = chess.Move.from_uci(text)

        if move not in self.board.legal_moves:
            raise ValueError("Illegal move")
        return move

    def _castle_move(self, board: chess.Board) -> chess.Move:
        """Try short (kingside) castle first, then long (queenside)."""
        if board is None:
            raise ValueError("Illegal move")

        # Build candidate UCIs based on side to move.
        if board.turn == chess.WHITE:
            candidates = ["e1g1", "e1c1"]
        else:
            candidates = ["e8g8", "e8c8"]

        for uci in candidates:
            move = chess.Move.from_uci(uci)
            if move in board.legal_moves and board.is_castling(move):
                return move
        raise ValueError("Illegal move")
