from enum import Enum

__all__ = ["ExitStatus"]


class ExitStatus(Enum):
    QUIT = 1
    RECONNECT = 2
    RELOAD = 3
