from chess_engine.board_manager import BoardManager
from chess_engine.imagine_simulator import ImagineSimulator
from chess_engine.stockfish_engine import StockfishEngine
from fsm.fsm_controller import FSMController
from input.wake_detector_mock import WakeDetectorMock
from util.logger import Logger
from util.timer import Timer


def main():
    import tkinter as tk
    from gui.gui_tk import ChessGUI

    logger = Logger()
    engine = StockfishEngine()
    board = BoardManager(engine=engine)
    imagine = ImagineSimulator(engine=engine)
    timer = Timer(max_time=5.0)
    wake_detector = WakeDetectorMock()
    fsm = FSMController(board, imagine, logger, timer, wake_detector)

    root = tk.Tk()
    gui = ChessGUI(root, fsm, timer)
    logger.attach_gui(gui)
    root.mainloop()


if __name__ == "__main__":
    main()
