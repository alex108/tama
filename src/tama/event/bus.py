"""
Defines an event bus that broadcasts a sequence of events to a series of
subscribers. The event handlers may be coroutines, which will be executed
within the current event loop.
"""
import asyncio as aio
from typing import (
    Type, TypeVar, Union, Callable, Awaitable, Dict, List, Collection
)

from .event import Event

__all__ = ["EventBus"]

T = TypeVar("T")
E = TypeVar("E", bound=Event)

RET = Union[None, Awaitable[None]]


class EventBus:
    event_handlers: Dict[Type[E], List[Callable[[E], RET]]]

    def __init__(self, accept: Collection[Type[Event]] = ()) -> None:
        """
        Creates a new EventBus.

        :param accept: Collection of accepted Event subclasses.
        """
        for event_type in accept:
            if not issubclass(event_type, Event):
                raise TypeError
        self.event_handlers = {
            event_type: [] for event_type in accept
        }

    def subscribe(self, event_type: Type[E], handler: Callable[[E], RET]) -> None:
        """
        Attach a new subscriber for the given event type. The handler function
        will be called with an instance of the given event as argument.

        :param event_type: Any accepted subclass of Event.
        :param handler: Function receiving the given Event as argument.
        :return: None
        """
        if event_type not in self.event_handlers:
            raise TypeError
        self.event_handlers[event_type].append(handler)

    def unsubscribe(self, event_type: Type[E], handler: Callable[[E], RET]) -> None:
        """
        Remove a subscriber for a given Event.

        :param event_type: Any accepted subclass of Event.
        :param handler: Subscriber to remove.
        :return: None
        """
        if event_type not in self.event_handlers:
            raise TypeError
        self.event_handlers[event_type].remove(handler)

    def broadcast(self, event: E) -> None:
        """
        Broadcasts a Event to all relevant subscribers.

        :param event: Event that will be broadcast.
        :return: None
        """
        if (event_type := type(event)) not in self.event_handlers:
            raise TypeError
        for handler in self.event_handlers[event_type]:
            if aio.iscoroutinefunction(handler):
                aio.ensure_future(handler(event))
            else:
                handler(event)
