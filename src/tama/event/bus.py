"""
Defines an event bus that broadcasts a sequence of signals to a series of
subscribers. The signal handlers may be coroutines, which will be executed
within the current event loop.
"""
import asyncio as aio
from typing import (
    Type, TypeVar, Union, Callable, Awaitable, Dict, List, Collection
)

from .signal import Signal

__all__ = ["EventBus"]

T = TypeVar("T")
S = TypeVar("S", bound=Signal)

RET = Union[None, Awaitable[None]]


class EventBus:
    signal_handlers: Dict[Type[S], List[Callable[[S], RET]]]

    def __init__(self, accept: Collection[Type[Signal]] = ()) -> None:
        """
        Creates a new EventBus.

        :param accept: Collection of accepted Signal subclasses.
        """
        for signal_type in accept:
            if not issubclass(signal_type, Signal):
                raise TypeError
        self.signal_handlers = {
            signal_type: [] for signal_type in accept
        }

    def subscribe(self, signal_type: Type[S], handler: Callable[[S], RET]) -> None:
        """
        Attach a new subscriber for the given signal type. The handler function
        will be called with an instance of the given signal as argument.

        :param signal_type: Any accepted subclass of Signal.
        :param handler: Function receiving the given Signal as argument.
        :return: None
        """
        if signal_type not in self.signal_handlers:
            raise TypeError
        self.signal_handlers[signal_type].append(handler)

    def unsubscribe(self, signal_type: Type[S], handler: Callable[[S], RET]) -> None:
        """
        Remove a subscriber for a given Signal.

        :param signal_type: Any accepted subclass of Signal.
        :param handler: Subscriber to remove.
        :return: None
        """
        if signal_type not in self.signal_handlers:
            raise TypeError
        self.signal_handlers[signal_type].remove(handler)

    def broadcast(self, signal: S) -> None:
        """
        Broadcasts a Signal to all relevant subscribers.

        :param signal: Signal that will be broadcast.
        :return: None
        """
        if (signal_type := type(signal)) not in self.signal_handlers:
            raise TypeError
        for handler in self.signal_handlers[signal_type]:
            if aio.iscoroutinefunction(handler):
                aio.ensure_future(handler(signal))
            else:
                handler(signal)
