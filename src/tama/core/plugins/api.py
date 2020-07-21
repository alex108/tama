"""
Defines functions available as the public plugin API.
"""
import inspect
import functools
from typing import List, Optional, cast

from .api_internal import *

__all__ = ["command", "regex"]


def command(name: str = None, *, permissions: List[str] = None):
    def decorator(f: Command.Executor):
        sig = inspect.signature(f)

        @functools.wraps(f)
        def wrapper(*args, **kwargs) -> Optional[str]:
            w_kwargs = {
                k: v for k, v in kwargs.items() if k in sig.parameters.keys()
            }
            return f(*args, **w_kwargs)

        setattr(
            wrapper,
            "_tama_action",
            Command(cast(Command.Executor, wrapper), name or f.__name__),
        )
        return wrapper
    return decorator


def regex(pattern: str):
    def decorator(f: Regex.Executor):
        sig = inspect.signature(f)

        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            w_kwargs = {
                k: v for k, v in kwargs.items() if k in sig.parameters.keys()
            }
            return f(*args, **w_kwargs)

        setattr(
            wrapper,
            "_tama_action",
            Regex(cast(Regex.Executor, wrapper), pattern)
        )
        return wrapper
    return decorator
