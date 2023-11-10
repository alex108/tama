"""
Defines functions available as the public plugin API.
"""
import inspect
import functools
import logging
import traceback
import os.path
from typing import List, Optional, Callable, cast

from .api_internal import *

__all__ = ["command", "regex"]


def _wrap_kwargs(f: Callable) -> Callable:
    sig = inspect.signature(f)

    @functools.wraps(f)
    def wrapper(*args, **kwargs) -> Optional[str]:
        w_kwargs = {
            k: v for k, v in kwargs.items() if k in sig.parameters.keys()
        }
        try:
            return f(*args, **w_kwargs)
        except Exception as exc:
            # Highest frame in the stack trace
            suspect_frame = traceback.extract_tb(exc.__traceback__)[-1]
            file = os.path.split(suspect_frame.filename)[1]
            line = suspect_frame.lineno
            logging.getLogger(__name__).exception(
                f"Plugin {file}:{line} threw unhandled {type(exc).__name__}"
            )
            # Swallow the exception after printing
            return "Error!"

    return wrapper


def command(
    name: str = None,
    *,
    permissions: List[str] = None
):
    def decorator(f: Command.Executor):
        wrapper = _wrap_kwargs(f)
        setattr(
            wrapper,
            "_tama_action",
            Command(
                cast(Command.Executor, wrapper),
                name or f.__name__,
                f.__doc__.strip() if f.__doc__ is not None else None
            ),
        )
        return wrapper
    return decorator


def regex(pattern: str):
    def decorator(f: Regex.Executor):
        wrapper = _wrap_kwargs(f)
        setattr(
            wrapper,
            "_tama_action",
            Regex(cast(Regex.Executor, wrapper), pattern)
        )
        return wrapper
    return decorator
