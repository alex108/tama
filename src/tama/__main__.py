import signal
import asyncio as aio
from types import FrameType

from tama.config import read_config
from tama.irc import IRCClient
from tama.core import TamaBot


async def main():
    cfg = read_config("config.toml")

    client = await IRCClient.create_from_config(cfg)

    bot = TamaBot(cfg)
    bot.set_client(client)

    def sigint_handler(sig: signal.Signals, frm: FrameType):
        bot.shutdown("Keyboard interrupt")

    signal.signal(signal.SIGINT, sigint_handler)

    while (status := await bot.run()) != TamaBot.ExitStatus.QUIT:
        if status == TamaBot.ExitStatus.RECONNECT:
            await aio.sleep(5)  # Wait 5 seconds before reconnecting
            client = await IRCClient.create_from_config(cfg)
            bot.set_client(client)
        if status == TamaBot.ExitStatus.RELOAD:
            await aio.sleep(5)  # Wait 5 seconds before reconnecting
            client = await IRCClient.create_from_config(cfg)
            bot = TamaBot(cfg)
            bot.set_client(client)


if __name__ == "__main__":
    aio.run(main())
