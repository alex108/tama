from enum import Enum

__all__ = ["ExitStatus"]


class ExitStatus(Enum):
    QUIT = 1
    RELOAD = 2
