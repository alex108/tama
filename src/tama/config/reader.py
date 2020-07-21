import toml

from .schema import Config

__all__ = ["read_config"]


def read_config(filename: str) -> Config:
    with open(filename, "r") as config:
        cfg = toml.loads(config.read())
        return Config(cfg)
