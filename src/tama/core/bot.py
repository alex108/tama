"""

"""
import re
from typing import List, Dict, Optional
from logging import getLogger

from tama.config import Config
from tama.irc import IRCClient
from tama.irc.signal import *
from tama.core.plugins import *

from .exit_status import ExitStatus

__all__ = ["TamaBot"]

logger = getLogger(__name__)


class TamaBot:
    client: Optional[IRCClient]
    plugins: List[Plugin]

    command_prefix: str

    act_commands: Dict[str, Command]
    act_regex: List[Regex]

    ExitStatus = ExitStatus
    _exit_status: ExitStatus

    def __init__(self, config: Config):
        self.client = None
        self.command_prefix = config.tama.prefix
        # Load plugins
        self.plugins = loader.load_plugins("plugins")
        # For registered actions
        self.act_commands = {}
        self.act_regex = []
        # By default, reconnect on exit
        self._exit_status = ExitStatus.RECONNECT
        # Register plugin actions
        self._setup_plugins()

    def set_client(self, client: IRCClient):
        self.client = client
        self._subscribe_client_events()

    def _setup_plugins(self):
        for plug in self.plugins:
            for act in plug.actions:
                if isinstance(act, Command):
                    self.act_commands[act.name] = act
                elif isinstance(act, Regex):
                    self.act_regex.append(act)

    def _subscribe_client_events(self):
        self.client.bus.subscribe(InvitedSignal, self.on_invite)
        self.client.bus.subscribe(MessagedSignal, self.on_message)
        self.client.bus.subscribe(ClosedSignal, self.on_closed)

    def _unsubscribe_client_events(self):
        self.client.bus.unsubscribe(InvitedSignal, self.on_invite)
        self.client.bus.unsubscribe(MessagedSignal, self.on_message)
        self.client.bus.unsubscribe(ClosedSignal, self.on_closed)

    async def run(self) -> ExitStatus:
        await self.client.run()
        return self._exit_status

    async def on_invite(self, evt: InvitedSignal):
        self.client.join(evt.to)

    async def on_message(self, evt: MessagedSignal):
        # Always log message
        logger.info(
            "[rizon:%s] <%s> %s",
            evt.where,
            evt.who.nick,
            evt.message,
        )

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
                    result = await r.async_executor(
                        text, sender=evt.who, bot=self
                    )
                else:
                    result = r.executor(text, sender=evt.who, bot=self)

                if result:
                    self.client.privmsg(evt.where, result)

            return

        # Run regexp parsers
        for r in self.act_regex:
            match = re.match(r.pattern, evt.message)
            if match:
                if r.is_async:
                    result = await r.async_executor(
                        match, sender=evt.who, bot=self
                    )
                else:
                    result = r.executor(match, sender=evt.who, bot=self)

                if result:
                    self.client.privmsg(evt.where, result)

    async def on_closed(self, evt: ClosedSignal):
        # Stop listening for events as we are entering a shutdown state
        self._unsubscribe_client_events()

    def nick(self, nickname: str):
        self.client.nick(nickname)

    def message(self, target: str, message: str):
        self.client.privmsg(target, message)

    def notice(self, target: str, message: str):
        self.client.notice(target, message)

    def shutdown(self, reason: str):
        self._exit_status = ExitStatus.QUIT
        self.client.quit(reason)

    def reconnect(self, reason: str):
        self._exit_status = ExitStatus.RECONNECT
        self.client.quit(reason)

    def reload(self, reason: str):
        self._exit_status = ExitStatus.RELOAD
        self.client.quit(reason)
