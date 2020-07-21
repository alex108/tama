from typing import TYPE_CHECKING
from dataclasses import dataclass

from tama.event import Event
from tama.irc.user import IRCUser

if TYPE_CHECKING:
    from tama.irc.client import IRCClient

__all__ = ["InvitedEvent", "MessagedEvent", "ClosedEvent"]


@dataclass
class InvitedEvent(Event):
    """
    Received an invite to an IRC channel.
    """
    client: "IRCClient"
    who: IRCUser
    to: str


@dataclass
class MessagedEvent(Event):
    """
    Received an IRC message.
    """
    client: "IRCClient"
    who: IRCUser
    where: str
    message: str


@dataclass
class ClosedEvent(Event):
    """
    IRC connection will be closed
    """
    client: "IRCClient"
    message: str
