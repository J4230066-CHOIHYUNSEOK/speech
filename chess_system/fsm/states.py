# fsm/states.py

from enum import Enum, auto

class State(Enum):
    WAIT_WAKE = auto()
    ROOT = auto()
    PLAY = auto()
    IMAGINE = auto()
