from tama import api, TamaBot

__all__ = ["help_"]


@api.command("help")
def help_(
    text: str, channel: str,
    sender: TamaBot.User = None,
    bot: TamaBot = None, client: TamaBot.Client = None
) -> None:
    """<command> - shows help for <command>"""
    command, *other = text.strip().split(" ", 1)
    if len(other) > 0:
        client.notice(sender.nick, "Invalid command name")

    # Return a list of commands if none was specified
    if command == "":
        cmdlist = [cmd for cmd in bot.act_commands]
        client.notice(sender.nick, f"Available commands: {', '.join(cmdlist)}")
        return

    # Only exact matches
    try:
        command = bot.act_commands[command]
        if command.docstring:
            msg = bot.command_prefix + command.name + " " + command.docstring
        else:
            msg = bot.command_prefix + command.name + " - No help available"
        client.message(channel, msg)
    except KeyError:
        client.notice(sender.nick, "No such command")
