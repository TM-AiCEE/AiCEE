import logging
import sys
import datetime
import os
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

ROOT_DIR = os.path.dirname(os.path.abspath(__file__)) + '\\logs\\'
if not os.path.exists(ROOT_DIR):
    os.mkdir(ROOT_DIR)

log_filename = ROOT_DIR + datetime.datetime.now().strftime('%Y-%m-%d-%H-%M') + '-bot.log'
fh = logging.FileHandler(filename=os.path.join(log_filename), mode='w', encoding='utf-8')
fh.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
logging.getLogger().addHandler(fh)


def receive_from(name, flags=0):
    def wrapper(func):
        EventManager.events[name] = func
        logging.debug('registered receive_from "%s" to "%s"', func.__name__, name)
        return func

    return wrapper


if __name__ == '__main__':

    bot_name = ""

    if len(sys.argv) >= 2:
        bot_name = str(sys.argv[1])

    else:
        bot_name = settings.bot_name

    logging.info("save logs in %s", log_filename)

    if settings.TRAINING_MODE:
        client = TexasPokerClient(settings.TRAINING_SERVER_URL)
        client.start()
    else:
        client = TexasPokerClient(settings.BATTLE_SERVER_URL)
        client.start()

    try:
        bot = Bot(client=client, name=bot_name)
        bot.join()

        table_mgr = TableManager()
        table_mgr.create(client).add_player(bot)
    except KeyboardInterrupt:
        client.on_close()



