import os
import sys
import importlib.util
from typing import List
from logging import getLogger

from .plugin import Plugin

logger = getLogger(__name__)

__all__ = ["load_plugins"]


def load_plugins(path: str) -> List[Plugin]:
    py_files = [
        f for f in os.listdir(path)
        if os.path.isfile(os.path.join(path, f)) and f.endswith(".py")
    ]
    plugins = []
    for py in py_files:
        try:
            module_name = f"tama.plugins.{py[:-3]}"
            spec = importlib.util.spec_from_file_location(
                module_name, os.path.join(path, py)
            )
            if spec is None:
                # Shit broke somehow
                continue
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            logger.info(f"Plugin {py} loaded.")
            plugins.append(Plugin(module_name, module))
        except SyntaxError:
            logger.info(f"Plugin {py} malformed.")

    return plugins
