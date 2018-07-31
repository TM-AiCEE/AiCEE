import sys
import psutil
import logging
import settings
import datetime
import os
import hashlib
import json

x = ""


def restart_program():

    try:
        p = psutil.Process(os.getpid())
        for handler in p.open_files() + p.connections():
            os.close(handler.fd)
    except Exception as e:
        logging.error(e)

    python = sys.executable
    os.execl(python, python, *sys.argv)


def generate_logs(number):
    global x

    log_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), settings.LOG_FOLDER_NAME)
    if not os.path.exists(log_folder):
        os.mkdir(log_folder)

    s = datetime.datetime.now().strftime('%Y-%m-%d-%H') + str(number)
    n = str(int(hashlib.sha256(s.encode('utf-8')).hexdigest(), 16) % 10 ** 8)
    log_filename = os.path.join(log_folder, n + ".log")
    x = n

    logging.info("[__new_peer_2] save logs in %s, %s", log_filename, x)

    fh = logging.FileHandler(filename=os.path.join(log_filename), mode='w', encoding='utf-8')
    fh.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
    formatter = logging.Formatter('[%(asctime)s] %(message)s')
    fh.setFormatter(formatter)
    logging.getLogger().addHandler(fh)


def generate_summarize_log(data):
    global x

    log_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), settings.LOG_FOLDER_NAME)
    if not os.path.exists(log_folder):
        os.mkdir(log_folder)

    s = datetime.datetime.now().strftime('%Y-%m-%d')
    n = str(int(hashlib.sha256(s.encode('utf-8')).hexdigest(), 16) % 10 ** 8)
    filename = os.path.join(log_folder, n + ".log")

    data['game_id'] = str(x)

    with open(filename, 'w+') as outfile:
        json.dump(data, outfile)