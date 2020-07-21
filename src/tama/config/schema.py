from dataclasses import dataclass
from typing import Optional, Dict

__all__ = ["Config", "ServerConfig", "TamaConfig"]


@dataclass
class ServerServiceAuthConfig:
    service: Optional[str]
    command: Optional[str]
    username: Optional[str]
    password: str


@dataclass
class ServerConfig:
    host: str
    port: str
    nick: str
    user: str
    realname: str
    service_auth: Optional[ServerServiceAuthConfig]


@dataclass
class TamaConfig:
    prefix: str


@dataclass
class Config:
    server: Dict[str, ServerConfig]
    tama: TamaConfig
