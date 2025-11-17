def load_grammar_for(st):
    pieces = ["pawn", "knight", "bishop", "rook", "queen", "king"]
    files = ["a", "b", "c", "d", "e", "f", "g", "h"]
    ranks = ["one", "two", "three", "four", "five", "six", "seven", "eight"]

    if st == "IMAGINE":
        commands = []
        for p in pieces:
            for f in files:
                for r in ranks:
                    commands.append(f"{p} {f} {r}")
        for f1 in files:
            for r1 in ranks:
                for f2 in files:
                    for r2 in ranks:
                        commands.append(f"{f1} {r1} {f2} {r2}")
        commands.extend(["return", "take", "explain", "evaluate", "back"])
        return commands

    if st == "ROOT":
        commands = ["play", "imagine", "evaluate", "explain"]
        for p in pieces:
            for f in files:
                for r in ranks:
                    commands.append(f"play {p} {f} {r}")
                    commands.append(f"{p} {f} {r}")
        for f1 in files:
            for r1 in ranks:
                for f2 in files:
                    for r2 in ranks:
                        commands.append(f"play {f1} {r1} {f2} {r2}")
                        commands.append(f"{f1} {r1} {f2} {r2}")
        return commands

    if st == "WAIT_WAKE":
        return ["hey chess"]

    return []
