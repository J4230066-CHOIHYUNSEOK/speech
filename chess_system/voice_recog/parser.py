# parser.py
from __future__ import annotations

pieces = ["pawn", "knight", "bishop", "rook", "queen", "king"]
files = ["a", "b", "c", "d", "e", "f", "g", "h"]
ranks = ["one", "two", "three", "four", "five", "six", "seven", "eight"]

common_cmds_imagine = ["return", "take", "explain", "evaluate", "back"]
common_cmds_root = ["play", "imagine", "evaluate", "explain"]
wake_word = ["hey chess"]

# Speech → chess notation helpers
rank_word_to_digit = {
    "one": "1",
    "two": "2",
    "three": "3",
    "four": "4",
    "five": "5",
    "six": "6",
    "seven": "7",
    "eight": "8",
}
piece_to_san = {
    "pawn": "",
    "knight": "N",
    "bishop": "B",
    "rook": "R",
    "queen": "Q",
    "king": "K",
}


def parse_move(words):
    """
    Return a normalized move string if words resemble a chess move.
    Converts rank words to digits so downstream chess_system can consume
    SAN-like (e.g., `Ne4`) or UCI-like (`e2e4`) text directly.
    Tolerates filler words (e.g., "queen to a four" -> queen a four).
    """
    words = [w.lower() for w in words]

    def first_after(start_idx, valid_set):
        for i in range(start_idx, len(words)):
            if words[i] in valid_set:
                return i, words[i]
        return None, None

    # piece → file → rank (with possible filler tokens in between)
    i_piece, piece = first_after(0, pieces)
    if piece:
        i_file, file = first_after(i_piece + 1, files)
        if file:
            i_rank, rank = first_after(i_file + 1, ranks)
            if rank:
                square = _to_square(file, rank)
                if not square:
                    return None
                prefix = piece_to_san.get(piece, "")
                return f"{prefix}{square}"

    # file → rank → file → rank (with fillers)
    i_f1, f1 = first_after(0, files)
    if f1:
        i_r1, r1 = first_after(i_f1 + 1, ranks)
        if r1:
            i_f2, f2 = first_after(i_r1 + 1, files)
            if f2:
                i_r2, r2 = first_after(i_f2 + 1, ranks)
                if r2:
                    from_sq = _to_square(f1, r1)
                    to_sq = _to_square(f2, r2)
                    if from_sq and to_sq:
                        return f"{from_sq}{to_sq}"

    # single pawn destination: file → rank
    i_file1, file1 = first_after(0, files)
    if file1:
        i_rank1, rank1 = first_after(i_file1 + 1, ranks)
        if rank1:
            square = _to_square(file1, rank1)
            if square:
                return square

    return None


def _to_square(file_word: str | None, rank_word: str | None) -> str | None:
    if not file_word or not rank_word:
        return None
    if file_word not in files or rank_word not in ranks:
        return None
    digit = rank_word_to_digit.get(rank_word)
    if not digit:
        return None
    return f"{file_word}{digit}"


def extract_command(text: str, state: str):
    """
    状態ごとに text を解析してコマンドを返す。
    マッチしなければ None。
    """

    text = text.strip().lower()
    if not text:
        return None

    words = text.split()

    # Wake handling stays with lWake, but keep a guard for completeness
    if state == "WAIT_WAKE":
        if text in wake_word:
            return text
        return None

    # ======================================================
    # ROOT : play [move] / imagine / evaluate / explain
    # ======================================================
    if state == "ROOT":
        # single-word commands
        if len(words) == 1 and words[0] in common_cmds_root:
            return words[0]

        # play + move
        if words and words[0] == "play":
            move = parse_move(words[1:])
            if move:
                return f"play {move}"
            return None

        # # bare move (no play prefix)
        # move = parse_move(words)
        # if move:
        #     return move
        # return None

    # ======================================================
    # IMAGINE : chess moves + imagine specific commands
    # ======================================================
    if state == "IMAGINE":
        if len(words) == 1 and words[0] in common_cmds_imagine:
            return words[0]

        move = parse_move(words)
        if move:
            return move
        return None

    # ======================================================
    # どれにも該当しない場合
    # ======================================================
    return None
