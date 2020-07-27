from typing import TYPE_CHECKING
from dataclasses import dataclass

from tama.event import Event
from tama.irc.user import IRCUser

if TYPE_CHECKING:
    from tama.irc.client import IRCClient

__all__ = [
    "InvitedEvent",
    "JoinedEvent", "BotJoinedEvent", "ChannelJoinedEvent",
    "PartedEvent", "BotPartedEvent", "ChannelPartedEvent",
    "KickedEvent", "BotKickedEvent", "ChannelKickedEvent",
    "MessagedEvent",
    "NoticedEvent",
    "ClosedEvent"
]


@dataclass
class InvitedEvent(Event):
    """
    Received an invite to an IRC channel.
    """
    client: "IRCClient"
    who: IRCUser
    to: str


@dataclass
class JoinedEvent(Event):
    """
    Someone joined an IRC channel.
    """
    client: "IRCClient"
    channel: str
    who: IRCUser


@dataclass
class BotJoinedEvent(JoinedEvent):
    """
    Bot joined an IRC channel.
    """


@dataclass
class ChannelJoinedEvent(JoinedEvent):
    """
    Another nickname joined an active IRC channel.
    """


@dataclass
class PartedEvent(Event):
    """
    Parted an IRC channel.
    """
    client: "IRCClient"
    channel: str
    who: IRCUser
    message: str


@dataclass
class BotPartedEvent(PartedEvent):
    """
    Bot parted an IRC channel.
    """


@dataclass
class ChannelPartedEvent(PartedEvent):
    """
    Another nickname parted an active IRC channel.
    """


@dataclass
class KickedEvent(Event):
    """
    Kicked from an IRC channel.
    """
    client: "IRCClient"
    channel: str
    who: IRCUser
    target: str
    message: str


@dataclass
class BotKickedEvent(KickedEvent):
    """
    Bot was kicked from IRC channel.
    """


@dataclass
class ChannelKickedEvent(KickedEvent):
    """
    Another nickname was kicked from an active IRC channel.
    """


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
class NoticedEvent(Event):
    """
    Received an IRC notice.
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
