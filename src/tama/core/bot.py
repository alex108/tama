"""

"""
import re
import asyncio as aio
from typing import List, Dict, Optional
from logging import getLogger

from tama.config import Config, ServerConfig
from tama.irc import IRCClient
from tama.irc.event import *
from tama.core.plugins import *

from .exit_status import ExitStatus

__all__ = ["TamaBot"]

logger = getLogger(__name__)


class TamaBot:
    config: Config
    command_prefix: str

    clients: List[IRCClient]
    plugins: List[Plugin]

    act_commands: Dict[str, Command]
    act_regex: List[Regex]

    ExitStatus = ExitStatus
    _exit_status: Optional[ExitStatus]

    def __init__(self, config: Config):
        self.config = config
        self.command_prefix = config.tama.prefix
        # Client bookkeeping
        self.clients = []
        # Load plugins
        self.plugins = loader.load_plugins("plugins")
        # For registered actions
        self.act_commands = {}
        self.act_regex = []
        # Only set exit status when exiting
        self._exit_status = None
        # Register plugin actions
        self._setup_plugins()

    def connect(self, client: IRCClient):
        self.clients.append(client)
        self._subscribe_client_events(client)

    async def create_clients_from_config(self):
        for name, srv in self.config.server.items():
            client = await IRCClient.create(srv)
            self.connect(client)

    def _setup_plugins(self):
        for plug in self.plugins:
            for act in plug.actions:
                if isinstance(act, Command):
                    self.act_commands[act.name] = act
                elif isinstance(act, Regex):
                    self.act_regex.append(act)

    def _subscribe_client_events(self, client: IRCClient):
        client.bus.subscribe(InvitedEvent, self.on_invite)
        client.bus.subscribe(MessagedEvent, self.on_message)
        client.bus.subscribe(ClosedEvent, self.on_closed)

    def _unsubscribe_client_events(self, client: IRCClient):
        client.bus.unsubscribe(InvitedEvent, self.on_invite)
        client.bus.unsubscribe(MessagedEvent, self.on_message)
        client.bus.unsubscribe(ClosedEvent, self.on_closed)

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
                # We get a config when we lost a client
                elif isinstance(result, ServerConfig):
                    pending.add(aio.create_task(IRCClient.create_after(
                        result, 5
                    )))
            done, pending = await aio.wait(
                pending, return_when=aio.FIRST_COMPLETED
            )

        if len(pending) > 0:
            await aio.wait(pending, return_when=aio.ALL_COMPLETED)

        return self._exit_status

    async def on_invite(self, evt: InvitedEvent):
        evt.client.join(evt.to)

    async def on_message(self, evt: MessagedEvent):
        # Always log message
        logger.info(
            "[rizon:%s] <%s> %s",
            evt.where,
            evt.who.nick,
            evt.message,
        )
        exec_kwargs = dict(channel=evt.where, sender=evt.who, bot=self, client=evt.client)

        # Parse commands
        if evt.message.startswith(self.command_prefix):
            cmd, *text = evt.message.split(" ", 1)
            cmd = cmd[1:]
            if len(text) == 0:
                text = ""
            else:
                text = text[0]

            r = self.act_commands.get(cmd)
            if r:
                if r.is_async:
                    result = await r.async_executor(text, **exec_kwargs)
                else:
                    result = r.executor(text, **exec_kwargs)

                if result:
                    evt.client.privmsg(evt.where, f"{evt.who.nick}, {result}")

            return

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
