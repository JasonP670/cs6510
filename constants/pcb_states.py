from enum import Enum

class PCBState(Enum):
    """
    Process Control Block (PCB) states.
    """
    NEW = 1
    READY = 2
    RUNNING = 3
    WAITING = 4
    TERMINATED = 5