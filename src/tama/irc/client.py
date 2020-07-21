"""
Handles the interpretation of parsed IRC messages and converts them to an
observable event stream.
"""
import asyncio as aio
from typing import List, Deque
from collections import deque
from logging import getLogger

from tama.config import ServerConfig
from tama.event import EventBus
from tama.irc.stream import IRCStream, IRCMessage

from .event import *

logger = getLogger(__name__)


class IRCClient:
    __slots__ = (
        "startup_config", "stream", "bus",
        "nickname", "username", "realname",
        "channel_list",
        "_starting_up", "_shutting_down", "_inbound_queue", "_outbound_queue",
        "_on_register",
    )

    # Client data
    startup_config: ServerConfig

    # Connection primitives
    stream: IRCStream
    bus: EventBus

    # User data
    nickname: str
    username: str
    realname: str

    # State keeping
    _channel_list: List[str]

    # Internals
    _starting_up: bool
    _shutting_down: bool
    _inbound_queue: Deque[IRCMessage]
    _outbound_queue: "aio.Queue[IRCMessage]"
    # Actions to perform once the IRC connection is registered.
    # These are not immediately queued on create as the connection is not
    # registered yet.
    _on_register: Deque[IRCMessage]

    def __init__(self, stream: IRCStream, startup_config: ServerConfig):
        self.startup_config = startup_config

        self.stream = stream
        self.bus = EventBus(accept=[
            InvitedEvent, MessagedEvent, ClosedEvent
        ])

        self._starting_up = True
        self._shutting_down = False
        self._inbound_queue = deque()
        self._outbound_queue = aio.Queue()
        self._on_register = deque()

        self.nickname = startup_config.nick
        self.username = startup_config.user
        self.realname = startup_config.realname

        self.channel_list = []

    @classmethod
    async def create(cls, config: ServerConfig) -> "IRCClient":
        if config.port.startswith("+"):
            secure = True
            port = int(config.port)
        else:
            secure = False
            port = int(config.port)
        stream = await IRCStream.create(config.host, port, secure)
        obj = cls(stream, config)
        obj.nick(config.nick)
        obj.user(config.user, config.realname)
        if config.service_auth:
            cmd = config.service_auth.command or "IDENTIFY "
            if config.service_auth.username:
                cmd += config.service_auth.username + " "
            cmd += config.service_auth.password
            obj._on_register.append(IRCMessage(
                command="PRIVMSG",
                middle=(config.service_auth.service or "NickServ",),
                trailing=cmd,
            ))
        return obj

    @classmethod
    async def create_after(
        cls, config: ServerConfig, seconds: int
    ) -> "IRCClient":
        await aio.sleep(seconds)
        return await cls.create(config)

    async def run(self) -> ServerConfig:
        inbound = aio.create_task(self._inbound())
        outbound = aio.create_task(self._outbound())
        pending = []
        while not self._shutting_down:
            done, pending = await aio.wait(
                [inbound, outbound], return_when=aio.FIRST_COMPLETED
            )
            if inbound in done:
                inbound = aio.create_task(self._inbound())
            if outbound in done:
                outbound = aio.create_task(self._outbound())
        # Entered shutdown state, which means the inbound queue reached EOF
        # Don't await any further because nothing can be sent anymore
        # Return startup config when connection dies for easy reconnection
        return self.startup_config

    async def _inbound(self) -> None:
        # Block if we have nothing to process
        if len(self._inbound_queue) == 0:
            new_messages = await self.stream.read_messages()
            # Connection done, shut down
            if new_messages is None:
                self._shutting_down = True
                return
            # Queue parsed messages
            self._inbound_queue.extend(new_messages)

        msg = self._inbound_queue.popleft()
        # TODO: Use logger don't write directly to stdout
        print(">> " + msg.raw[:-2].decode("utf-8"))
        # NOTE: Due to the fact all IRC commands are uppercase we turn them
        # to lower for nicer function dispatching.
        srv_handler = getattr(
            self,
            "handle_server_" + msg.command.lower(),
            self.handle_server_default,
            )
        srv_handler(msg)

    async def _outbound(self):
        # Block until we have a new message to send
        msg = await self._outbound_queue.get()
        # TODO: Use logger don't write directly to stdout
        print("<< " + msg.raw[:-2].decode("utf-8"))
        await self.stream.send_message(msg)

    # Upstream command handlers
    def handle_server_default(self, msg: IRCMessage):
        logger.info(
            "[%s] %s", "rizon", msg.trailing
        )

    def handle_server_ping(self, msg: IRCMessage):
        self.pong(msg.trailing)

    def handle_server_nick(self, msg: IRCMessage):
        who = msg.parse_prefix_as_user()
        if who.nick == self.nickname:
            self.nickname = msg.trailing

    def handle_server_privmsg(self, msg: IRCMessage):
        # If command param is the client nick, set the user as the location
        who = msg.parse_prefix_as_user()
        where = msg.middle[0]
        if where == self.nickname:
            where = who.nick
        self.bus.broadcast(MessagedEvent(
            client=self,
            who=who,
            where=where,
            message=msg.trailing,
        ))

    def handle_server_invite(self, msg: IRCMessage):
        self.bus.broadcast(InvitedEvent(
            client=self,
            who=msg.parse_prefix_as_user(),
            to=msg.trailing,
        ))

    def handle_server_join(self, msg: IRCMessage):
        self.channel_list.append(msg.trailing)

    def handle_server_kick(self, msg: IRCMessage):
        who = msg.parse_prefix_as_user()
        logger.info(
            "Kicked from %s by %s (%s)", msg.middle[0], who.nick, msg.trailing
        )

    def handle_server_error(self, msg: IRCMessage):
        self.bus.broadcast(ClosedEvent(
            client=self,
            message=msg.trailing,
        ))

    # Upstream reply code handlers
    def handle_server_rpl_welcome(self, msg: IRCMessage):
        self._starting_up = False
        while self._on_register:
            m = self._on_register.popleft()
            self._outbound_queue.put_nowait(m)

    def handle_server_err_nicknameinuse(self, msg: IRCMessage):
        # If we are still starting up, then retry with an underscore
        if self._starting_up:
            self.nickname = self.nickname + "_"
            self.nick(self.nickname)

    # Command executors
    def user(self, username: str, realname: str):
        self._outbound_queue.put_nowait(IRCMessage(
            command="USER",
            middle=(username, "0", "*"),
            trailing=realname,
        ))

    def nick(self, nickname: str):
        self._outbound_queue.put_nowait(IRCMessage(
            command="NICK",
            trailing=nickname,
        ))

    def ping(self, payload: str):
        self._outbound_queue.put_nowait(IRCMessage(
            command="PING",
            trailing=payload,
        ))

    def pong(self, payload: str):
        self._outbound_queue.put_nowait(IRCMessage(
            command="PONG",
            trailing=payload,
        ))

    def join(self, channel: str):
        self._outbound_queue.put_nowait(IRCMessage(
            command="JOIN",
            middle=(channel,)
        ))

    def notice(self, target: str, message: str):
        self._outbound_queue.put_nowait(IRCMessage(
            command="NOTICE",
            middle=(target,),
            trailing=message,
        ))

    def privmsg(self, target: str, message: str):
        self._outbound_queue.put_nowait(IRCMessage(
            command="PRIVMSG",
            middle=(target,),
            trailing=message,
        ))

    def quit(self, reason: str):
        self._outbound_queue.put_nowait(IRCMessage(
            command="QUIT",
            trailing=reason,
        ))
