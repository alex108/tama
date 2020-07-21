from typing import Optional, List
from tama.irc.stream import IRCMessage

CTCP_COMMANDS = {
    "ACTION",      # ACTION <text>
    "CLIENTINFO",  # CLIENTINFO
    "DCC",         # DCC <type> <argument> <host> <port>
    "FINGER",      # [Obsolete] FINGER
    "PING",        # PING <info>
    "SOURCE",      # [Obsolete] SOURCE
    "TIME",        # TIME
    "VERSION",     # VERSION
    "USERINFO",    # [Obsolete] USERINFO
}


class CTCPMessage:
    command: str
    params: List[str]
    text: Optional[str]

    def __init__(
        self, command: str, params: List[str] = None, text: str = None
    ) -> None:
        self.command = command
        self.params = params or []
        self.text = text

    @staticmethod
    def is_ctcp(msg: IRCMessage) -> bool:
        """
        Checks if a given IRC message is a CTCP message.

        :param msg: Message to check.
        :return:
        """
        return (
            len(msg.middle) == 1
            and msg.middle[0] == "PRIVMSG"
            and msg.trailing.startswith("\x01")
            and msg.trailing.endswith("\x01")
        )

    @classmethod
    def parse(cls, msg: IRCMessage) -> "CTCPMessage":
        ctcp: str = msg.trailing[1:-1]
        cmd, *trailing = ctcp.split(" ", 1)
        if len(trailing) == 0:
            trailing = None
        parser = getattr(cls, "parse_" + cmd.lower(), cls.parse_default)
        return parser(msg, cmd, trailing)

    @classmethod
    def parse_default(
        cls, msg: IRCMessage, cmd: str, trailing: str = None
    ) -> "CTCPMessage":
        return cls(cmd, None, trailing)
