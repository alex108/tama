from dataclasses import dataclass

from tama.event import Signal
from tama.irc.user import IRCUser

__all__ = ["InvitedSignal", "MessagedSignal", "ClosedSignal"]


@dataclass
class InvitedSignal(Signal):
    """
    Received an invite to an IRC channel.
    """
    who: IRCUser
    to: str


@dataclass
class MessagedSignal(Signal):
    """
    Received an IRC message.
    """
    who: IRCUser
    where: str
    message: str


@dataclass
class ClosedSignal(Signal):
    """
    IRC connection will be closed
    """
    message: str
