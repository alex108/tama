__all__ = ["InvalidIRCCommandError"]


class InvalidIRCCommandError(Exception):
    """
    Received a valid message, but the command given is not valid IRC.
    """
