from types import ModuleType, FunctionType
from typing import Optional, List

from tama.core.plugins.api_internal import *


class Plugin:
    module_name: str
    module: ModuleType
    actions: List[Action]

    def __init__(self, module_name: str, module: ModuleType):
        self.module_name = module_name
        self.module = module
        self.actions = []
        self._load_actions()

    def _load_actions(self):
        # If the plugin has defined __all__, only load things in __all__
        if (decl_all := getattr(self.module, "__all__", None)) is not None:
            potential_actions = decl_all
        else:
            potential_actions = [
                f for f in dir(self.module)
                if isinstance(getattr(self.module, f), FunctionType)
            ]

        # Check for actions registered
        for pa in potential_actions:
            pa_f = getattr(self.module, pa)
            info: Optional[Action] = getattr(pa_f, "_tama_action", None)
            if not info:
                continue
            if isinstance(info, Action):
                self.actions.append(info)
