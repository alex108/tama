import os
import sys
import importlib
import importlib.util
from typing import List
from logging import getLogger

from .plugin import Plugin

__all__ = ["load_builtins", "load_plugins"]


def load_builtins() -> List[Plugin]:
    builtin_pkg = "tama.core.plugins.builtins"
    builtins = importlib.import_module(builtin_pkg)
    return [
        Plugin(
            f"{builtin_pkg}.{module_name}",
            importlib.import_module(f"{builtin_pkg}.{module_name}")
        )
        for module_name in builtins.__all__
    ]


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
            getLogger(__name__).info(f"Plugin {py} loaded.")
            plugins.append(Plugin(module_name, module))
        except SyntaxError:
            getLogger(__name__).error(f"Plugin {py} malformed.")
        except Exception as exc:  # noqa
            getLogger(__name__).exception(f"Error while loading plugin {py}:")

    return plugins
