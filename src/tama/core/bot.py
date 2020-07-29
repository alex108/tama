"""

"""
import re
import asyncio as aio
import logging
import logging.handlers
from typing import List, Dict, Optional, Union
from pathlib import Path

from tama.config import Config
from tama.util.trie import Trie
from tama.irc import IRCClient, IRCUser
from tama.irc.event import *
from tama.core.plugins import *

from .exit_status import ExitStatus
from .client_proxy import ClientProxy

__all__ = ["TamaBot"]


class TamaBot:
    config: Config
    command_prefix: str
    log_folder: str
    log_raw: bool
    log_irc: bool

    clients: List[IRCClient]
    plugins: List[Plugin]

    # Registered actions
    act_commands: Dict[str, Command]
    act_regex: List[Regex]

    act_commands_idx: Trie

    # Enumeration for exit status
    ExitStatus = ExitStatus
    _exit_status: Optional[ExitStatus]

    # Provide access to Client proxy and IRCUser here for a cleaner API
    Client = ClientProxy
    User = IRCUser

    def __init__(self, config: Config):
        self.config = config
        self.command_prefix = config.tama.prefix
        self.log_folder = config.tama.log_folder or "logs"
        # Bloody booleans
        self.log_raw = (
            config.tama.log_raw if config.tama.log_raw is not None else False
        )
        self.log_irc = (
            config.tama.log_irc if config.tama.log_irc is not None else True
        )
        # Client bookkeeping
        self.clients = []
        # Load plugins
        self.plugins = loader.load_plugins("plugins")
        # For registered actions
        self.act_commands = {}
        self.act_regex = []
        self.act_commands_idx = Trie()
        # Only set exit status when exiting
        self._exit_status = None
        # Register plugin actions
        self._setup_plugins()

    def connect(self, client: IRCClient):
        self.clients.append(client)
        self._subscribe_client_events(client)

    async def create_clients_from_config(self):
        for name, srv in self.config.server.items():
            client = await IRCClient.create(name, srv)
            self.connect(client)
            if self.log_raw:
                self._setup_client_raw_logger(client)

    def _setup_plugins(self):
        for plug in self.plugins:
            for act in plug.actions:
                if isinstance(act, Command):
                    self.act_commands[act.name] = act
                    self.act_commands_idx.add(act.name)
                elif isinstance(act, Regex):
                    self.act_regex.append(act)

    def _subscribe_client_events(self, client: IRCClient) -> None:
        client.bus.subscribe(InvitedEvent, self.on_invite)
        client.bus.subscribe(MessagedEvent, self.on_message)
        client.bus.subscribe(ClosedEvent, self.on_closed)
        client.bus.subscribe(BotJoinedEvent, self.on_join)
        client.bus.subscribe(ChannelJoinedEvent, self.on_join)
        client.bus.subscribe(BotPartedEvent, self.on_part)
        client.bus.subscribe(ChannelPartedEvent, self.on_part)
        client.bus.subscribe(BotKickedEvent, self.on_kick)
        client.bus.subscribe(ChannelKickedEvent, self.on_kick)

    def _unsubscribe_client_events(self, client: IRCClient) -> None:
        client.bus.unsubscribe(InvitedEvent, self.on_invite)
        client.bus.unsubscribe(MessagedEvent, self.on_message)
        client.bus.unsubscribe(ClosedEvent, self.on_closed)
        client.bus.unsubscribe(BotJoinedEvent, self.on_join)
        client.bus.unsubscribe(ChannelJoinedEvent, self.on_join)
        client.bus.unsubscribe(BotPartedEvent, self.on_part)
        client.bus.unsubscribe(ChannelPartedEvent, self.on_part)
        client.bus.unsubscribe(BotKickedEvent, self.on_kick)
        client.bus.unsubscribe(ChannelKickedEvent, self.on_kick)

    def _setup_client_raw_logger(self, client: IRCClient) -> None:
        if not self.log_raw:
            return

        log_dir = Path(self.log_folder)
        if not log_dir.is_dir():
            log_dir.mkdir(parents=True)

        hdl = logging.handlers.TimedRotatingFileHandler(
            filename=Path(self.log_folder, f"{client.name}.raw.log"),
            when="midnight",
            encoding="utf-8",
        )
        hdl.setFormatter(logging.Formatter(
            fmt=f"[{client.name}] [%(asctime)s] %(message)s",
            datefmt="%H:%M:%S"
        ))
        client.logger.addHandler(hdl)

    def _get_irc_logger(
        self, client: IRCClient, buffer: str
    ) -> Optional[logging.Logger]:
        if not self.log_irc:
            return

        log_dir = Path(self.log_folder, client.name)
        if not log_dir.is_dir():
            log_dir.mkdir(parents=True)

        log = logging.getLogger(f"tama.server.{client.name}.irc.{buffer}")
        if len(log.handlers) == 0:
            hdl = logging.handlers.TimedRotatingFileHandler(
                filename=log_dir.joinpath(f"{buffer}.log"),
                when="midnight",
                encoding="utf-8",
            )
            hdl.setFormatter(logging.Formatter(
                fmt=f"[{client.name}:{buffer}] [%(asctime)s] %(message)s",
                datefmt="%H:%M:%S"
            ))
            log.addHandler(hdl)

        return log

    async def run(self) -> ExitStatus:
        done = set()
        pending = {
            aio.create_task(c.run()) for c in self.clients
        }
        while self._exit_status is None:
            for task in done:
                result = await task
                # We only get a client when we queued recreating a lost one
                if isinstance(result, IRCClient):
                    self.connect(result)
                    pending.add(aio.create_task(result.run()))
                # We get (name, config) when we lost a client
                elif isinstance(result, tuple):
                    name, cfg = result
                    pending.add(aio.create_task(IRCClient.create_after(
                        name, cfg, 5
                    )))
            done, pending = await aio.wait(
                pending, return_when=aio.FIRST_COMPLETED
            )

        if len(pending) > 0:
            await aio.wait(pending, return_when=aio.ALL_COMPLETED)

        return self._exit_status

    async def on_invite(self, evt: InvitedEvent):
        evt.client.join(evt.to)

    async def on_join(self, evt: Union[BotJoinedEvent, ChannelJoinedEvent]):
        log = self._get_irc_logger(evt.client, evt.channel)
        if log:
            log.info(
                "* %s (%s) has joined %s",
                evt.who.nick, evt.who.address, evt.channel,
            )

    async def on_part(self, evt: Union[BotPartedEvent, ChannelPartedEvent]):
        log = self._get_irc_logger(evt.client, evt.channel)
        if log:
            log.info(
                "* %s (%s) has left %s (%s)",
                evt.who.nick, evt.who.address, evt.channel, evt.message,
            )

    async def on_kick(self, evt: Union[BotKickedEvent, ChannelKickedEvent]):
        log = self._get_irc_logger(evt.client, evt.channel)
        if log:
            log.info(
                "* %s (%s) has kicked %s from %s (%s)",
                evt.who.nick, evt.who.address,
                evt.target, evt.channel, evt.message,
            )

    async def on_message(self, evt: MessagedEvent):
        # Log message before parsing
        log = self._get_irc_logger(evt.client, evt.where)
        if log:
            log.info("<%s> %s", evt.who.nick, evt.message)

        exec_kwargs = dict(
            channel=evt.where,
            sender=evt.who,
            bot=self,
            client=ClientProxy(evt.client, self)
        )

        # Parse commands
        if evt.message.startswith(self.command_prefix):
            cmd, *text = evt.message.split(" ", 1)
            cmd = cmd[1:]
            if len(text) == 0:
                text = ""
            else:
                text = text[0]

            # Check for exact matches
            r = self.act_commands.get(cmd)

            if not r:
                # Check for non-exact matches
                cmd_match = self.act_commands_idx.search(cmd)
                if len(cmd_match) == 0:
                    return
                elif len(cmd_match) == 1:
                    r = self.act_commands.get(cmd_match[0])
                else:
                    dym = "Did you mean: " + cmd_match[0]
                    for m in cmd_match[1:-1]:
                        dym += ", " + m
                    dym += " or " + cmd_match[-1] + "?"
                    evt.client.notice(evt.who.nick, dym)
                    return

            if r.is_async:
                result = await r.async_executor(text, **exec_kwargs)
            else:
                result = r.executor(text, **exec_kwargs)

            if result:
                evt.client.privmsg(evt.where, f"{evt.who.nick}, {result}")

        # Run regexp parsers
        for r in self.act_regex:
            match = re.match(r.pattern, evt.message)
            if match:
                if r.is_async:
                    result = await r.async_executor(match, **exec_kwargs)
                else:
                    result = r.executor(match, **exec_kwargs)

                if result:
                    evt.client.privmsg(evt.where, f"{evt.who.nick}, {result}")

    async def on_closed(self, evt: ClosedEvent):
        # Stop listening for events as we are entering a shutdown state
        self._unsubscribe_client_events(evt.client)

    def shutdown(self, reason: str):
        self._exit_status = ExitStatus.QUIT
        for client in self.clients:
            client.quit(reason)

    def reload(self, reason: str):
        self._exit_status = ExitStatus.RELOAD
        for client in self.clients:
            client.quit(reason)
