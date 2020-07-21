"""
Defines the plugin API internals.
"""
import re
import asyncio as aio
from typing import Protocol, Pattern, Match, Optional, Union, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from tama.irc.user import IRCUser
    from tama.irc.client import IRCClient
    from tama.core.bot import TamaBot

__all__ = ["Action", "Command", "Regex"]


class Action:
    is_async: bool
    executor: Optional[Any]
    async_executor: Optional[Any]

    def __init__(self, executor: Any):
        if aio.iscoroutinefunction(executor):
            self.is_async = True
            self.executor = None
            self.async_executor = executor
        else:
            self.is_async = False
            self.executor = executor
            self.async_executor = None


class Command(Action):
    name: str
    executor: Optional["Command.Executor"]
    async_executor: Optional["Command.AsyncExecutor"]

    class Executor(Protocol):
        def __call__(
            self,
            text: str,
            *,
            channel: str = None,
            sender: "IRCUser" = None,
            bot: "TamaBot" = None,
            client: "IRCClient" = None
        ) -> Optional[str]: ...

    class AsyncExecutor(Protocol):
        async def __call__(
            self,
            text: str,
            *,
            channel: str = None,
            sender: "IRCUser" = None,
            bot: "TamaBot" = None,
            client: "IRCClient" = None
        ) -> Optional[str]: ...

    def __init__(
        self,
        executor: Union["Command.Executor", "Command.AsyncExecutor"],
        name: str
    ):
        super().__init__(executor)
        self.name = name


class Regex(Action):
    pattern: Pattern
    executor: Optional["Regex.Executor"]
    async_executor: Optional["Regex.AsyncExecutor"]

    class Executor(Protocol):
        def __call__(
            self,
            match: Match,
            *,
            channel: str = None,
            sender: "IRCUser" = None,
            bot: "TamaBot" = None,
            client: "IRCClient" = None
        ) -> Optional[str]: ...

    class AsyncExecutor(Protocol):
        async def __call__(
            self,
            match: Match,
            *,
            channel: str = None,
            sender: "IRCUser" = None,
            bot: "TamaBot" = None,
            client: "IRCClient" = None
        ) -> Optional[str]: ...

    def __init__(
        self,
        executor: Union["Regex.Executor", "Regex.AsyncExecutor"],
        pattern: str
    ):
        super().__init__(executor)
        self.pattern = re.compile(pattern)
