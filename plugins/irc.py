from tama import api, IRCUser, TamaBot

__all__ = ["nick", "say", "quit_", "restart"]


@api.command(permissions=["bot_control"])
def nick(text: str, sender: IRCUser = None, bot: TamaBot = None) -> None:
    new_nick, *other = text.strip().split(" ", 1)
    if len(other) > 0:
        bot.notice(sender.nick, "Invalid nickname")
    bot.nick(new_nick)


@api.command(permissions=["bot_control"])
def say(text: str, sender: IRCUser = None, bot: TamaBot = None) -> None:
    channel, *msg = text.strip().split(" ", 1)
    if len(msg) == 0:
        bot.notice(sender.nick, "Empty message")
    bot.message(channel, msg[0])


@api.command("quit", permissions=["bot_control"])
def quit_(text: str, bot: TamaBot = None) -> None:
    reason = text.strip()
    bot.shutdown(reason)


@api.command(permissions=["bot_control"])
def restart(text: str, bot: TamaBot = None) -> None:
    reason = text.strip()
    bot.reload(reason)
