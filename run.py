import logging
import sys

import settings

from player import Bot
from table import TableManager
from manager import EventManager
from websocket_client import TexasPokerClient

kw = {
    'format': '[%(asctime)s] %(message)s',
    'datefmt': '%m/%d/%Y %H:%M:%S',
    'level': logging.DEBUG if settings.DEBUG else logging.INFO,
    'stream': sys.stdout,
}

logging.basicConfig(**kw)


def receive_from(name, flags=0):
    def wrapper(func):
        EventManager.events[name] = func
        logging.info('registered receive_from "%s" to "%s"', func.__name__, name)
        return func

    return wrapper


if __name__ == '__main__':

    bot_name, bot_md5 = "", ""
    if len(sys.argv) >= 3:
        bot_name = str(sys.argv[1])
        bot_md5 = str(sys.argv[2])
    else:
        bot_name = settings.bot_name
        bot_md5 = settings.bot_md5

    client = TexasPokerClient(settings.TRAINING_SERVER_URL)
    client.start()

    try:
        bot = Bot(client=client, name=bot_name, md5=bot_md5)
        bot.join()

        table_mgr = TableManager()
        table_mgr.set_table(0, 0).add_player(bot)
    except KeyboardInterrupt:
        client.on_close()



