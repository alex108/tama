"""
Provides utilities to broadcast a series of signals to subscribed observers.
This is akin to an implementation of the observer pattern, with the central
event bus acting as an observable.
"""
from .signal import Signal
from .bus import EventBus

__all__ = ["Signal", "EventBus"]
