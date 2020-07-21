"""
Provides utilities to broadcast a series of events to subscribed observers.
This is akin to an implementation of the observer pattern, with the central
event bus acting as an observable.
"""
from .event import Event
from .bus import EventBus

__all__ = ["Event", "EventBus"]
