import sys
import psutil
import logging
import settings
import datetime
import os
import hashlib
import json, io

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

    d = datetime.datetime.now().strftime('%Y%m%d%H')
    s = d + str(number)
    n = str(int(hashlib.sha256(s.encode('utf-8')).hexdigest(), 16) % 10 ** 5)
    x = n

    if settings.TRAINING_MODE:
        log_filename = os.path.join(log_folder, d + n + "T.log")
    else:
        log_filename = os.path.join(log_folder, d + n + "B.log")

    logging.info("[__new_peer_2] log location: %s.", log_filename)

    fh = logging.FileHandler(filename=os.path.join(log_filename), mode='a', encoding='utf-8')
    fh.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
    formatter = logging.Formatter('[%(asctime)s] %(message)s')
    fh.setFormatter(formatter)
    logging.getLogger().addHandler(fh)


def generate_summarize_log(d):
    global x

    log_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), settings.LOG_FOLDER_NAME)
    if not os.path.exists(log_folder):
        os.mkdir(log_folder)

    s = datetime.datetime.now().strftime('%Y-%m-%d')

    if settings.TRAINING_MODE:
        filename = os.path.join(log_folder, s + "T.log")
    else:
        filename = os.path.join(log_folder, s + "B.log")

    d['game_id'] = str(x)

    if not os.path.isfile(filename):
        with open(filename, 'w', encoding='utf8') as f:
            json.dump(d, f, ensure_ascii=False)
            f.write('\n')
    else:
        with io.open(filename, 'r', encoding='utf8') as f:
            text = f.read()

        with io.open(filename, 'w', encoding='utf8') as f:
            f.write(text)
            json.dump(d, f, ensure_ascii=False)
            f.write('\n')




