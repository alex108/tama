from tama import api, IRCUser, IRCClient, TamaBot

__all__ = ["nick", "say", "message","quit_", "reload"]


@api.command(permissions=["bot_control"])
def nick(text: str, sender: IRCUser = None, client: IRCClient = None) -> None:
    new_nick, *other = text.strip().split(" ", 1)
    if len(other) > 0:
        client.notice(sender.nick, "Invalid nickname")
    client.nick(new_nick)


@api.command(permissions=["bot_control"])
def say(
    text: str, channel: str, sender: IRCUser = None, client: IRCClient = None
) -> None:
    payload = text.strip()
    if payload.startswith("#"):
        channel, *msg = text.strip().split(" ", 1)
        if len(msg) == 0:
            client.notice(sender.nick, "Empty message")
        msg = msg[0]
    else:
        msg = text
    client.privmsg(channel, msg)


@api.command(permissions=["bot_control"])
def message(
    text: str, sender: IRCUser = None, client: IRCClient = None
) -> None:
    target, *msg = text.strip().split(" ", 1)
    if len(msg) == 0:
        client.notice(sender.nick, "Empty message")
    client.privmsg(target, msg[0])


@api.command("quit", permissions=["bot_control"])
def quit_(text: str, bot: TamaBot = None) -> None:
    reason = text.strip()
    bot.shutdown(reason)


@api.command(permissions=["bot_control"])
def reload(text: str, bot: TamaBot = None) -> None:
    reason = text.strip()
    bot.reload(reason)
