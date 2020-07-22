__all__ = ["InvalidIRCCommandError"]


class InvalidIRCCommandError(Exception):
    """
    Received a valid message, but the command given is not valid IRC.
    """

    command: str

    def __init__(self, command: str) -> None:
        self.command = command
