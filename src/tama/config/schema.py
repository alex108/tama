from typing import Optional, Any, Union, Dict, List

__all__ = ["Config"]

SCHEMA_TYPE = Dict[str, type]

IRC_SCHEMA = {
    "host": str,
    "port": str,
    "nickname": str,
    "username": str,
    "realname": str,
}

TAMA_SCHEMA = {
    "prefix": str,
}


class ConfigSection:
    _config: dict
    _section: str

    def __init__(self, config: dict, section: str, schema: SCHEMA_TYPE = None):
        self._config = config
        self._section = section
        self._validate_exists()
        if schema:
            self._validate_schema(schema)

    def _validate_exists(self):
        if (section := self._config.get(self._section)) is None:
            raise KeyError(self._section)
        if not isinstance(section, dict):
            raise TypeError(f"Config section {self._section} is not a dict")

    def _validate_schema(self, schema: SCHEMA_TYPE):
        for key in schema.keys():
            if (val := self._config[self._section].get(key)) is None:
                raise ValueError(
                    f"Key {key} in section {self._section} is required."
                )
            if not isinstance(val, schema[key]):
                raise ValueError(
                    f"Key {key} in section {self._section} must be of type "
                    f"{schema[key].__name__}."
                )

    def __getattr__(self, item: str) -> Optional[Any]:
        return self._config[self._section].get(item)


class Config:
    _config: dict

    def __init__(self, config: dict):
        self._config = config

    @property
    def irc(self):
        return ConfigSection(self._config, "irc", IRC_SCHEMA)

    @property
    def tama(self):
        return ConfigSection(self._config, "tama", TAMA_SCHEMA)
