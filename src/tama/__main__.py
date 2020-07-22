import signal
import asyncio as aio
import logging.config
from types import FrameType

from tama.config import read_config
from tama.core import TamaBot


async def main():
    cfg = read_config("config.toml")
    if cfg.logging:
        logging.config.dictConfig(cfg.logging)

    bot = TamaBot(cfg)
    await bot.create_clients_from_config()

    def sigint_handler(sig: signal.Signals, frm: FrameType):
        bot.shutdown("Keyboard interrupt")

    signal.signal(signal.SIGINT, sigint_handler)

    while (status := await bot.run()) != TamaBot.ExitStatus.QUIT:
        if status == TamaBot.ExitStatus.RELOAD:
            await aio.sleep(5)  # Wait 5 seconds before reloading
            cfg = read_config("config.toml")
            bot = TamaBot(cfg)
            await bot.create_clients_from_config()


if __name__ == "__main__":
    aio.run(main())
