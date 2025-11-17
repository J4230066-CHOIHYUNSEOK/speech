# parser.py

pieces = ["pawn", "knight", "bishop", "rook", "queen", "king"]
files = ["a", "b", "c", "d", "e", "f", "g", "h"]
ranks = ["one", "two", "three", "four", "five", "six", "seven", "eight"]

common_cmds_imagine = ["return", "take", "explain", "evaluate", "back"]
common_cmds_root = ["play", "imagine", "evaluate", "explain"]
wake_word = ["hey chess"]


def parse_move(words):
    """
    Return a normalized move string if words resemble a chess move.
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
                return f"{piece} {file} {rank}"

    # file → rank → file → rank (with fillers)
    i_f1, f1 = first_after(0, files)
    if f1:
        i_r1, r1 = first_after(i_f1 + 1, ranks)
        if r1:
            i_f2, f2 = first_after(i_r1 + 1, files)
            if f2:
                i_r2, r2 = first_after(i_f2 + 1, ranks)
                if r2:
                    return f"{f1} {r1} {f2} {r2}"

    return None


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
    # ROOT : play [move] / imagine / evaluate / explain / bare moves
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
