import logging
import json
import sys
import time

from threading import Thread
from websocket import create_connection
from websocket import WebSocketConnectionClosedException
from http import HTTPStatus
from dispatcher import MessageDispatcher
from manager import EventManager


class WebSocketClient(object):
    def __init__(self, url):
        self.url = url
        self.ws = None
        self.stop = None
        self.thread = None
        self.is_connect = False
        self._events = EventManager()
        self._dispatcher = MessageDispatcher(self._events.get_events())
        self.reconnect_count = 0

    def _connect(self):
        logging.info("[TexasPokerClient] connecting to %s", self.url)
        self.ws = create_connection(self.url)
        if self.ws.status == HTTPStatus.SWITCHING_PROTOCOLS:
            logging.info("[TexasPokerClient] %s, status %s", HTTPStatus.SWITCHING_PROTOCOLS.description, self.ws.status)
            self.is_connect = True
        else:
            logging.info("[TexasPokerClient] connect failed: %s", self.ws.status)

    def reconnect(self):
        if self.is_connect:
            self._disconnect()
            self.start()

    def _disconnect(self):
        try:
            if self.ws:
                self.ws.close()
        except WebSocketConnectionClosedException as e:
            logging.debug("[TexasPokerClient] disconnect from server.")

        self.on_close()

    def _listen(self):
        while not self.stop:
            try:
                data = self.ws.recv()
                msg = json.loads(data)
            except ValueError as e:
                self.on_error(e)
            except Exception as e:
                self.on_error(e)
            else:
                self.on_message(msg)

    def start(self):
        def _go():
            self._connect()
            self._listen()
            self._disconnect()

        self.stop = False
        self.on_open()
        self.thread = Thread(target=_go)
        self.thread.start()


class TexasPokerClient(WebSocketClient):

    def on_open(self):
        self._events.init_event()

    def on_message(self, msg):
        self._dispatcher.dispatch_msg(msg)

    def on_close(self):
        if self.is_connect:
            logging.info("[TexasPokerClient] -- Goodbye! --")

    def send(self, message):
        while True:
            if self.is_connect:
                self.ws.send(message)
                break

    def on_error(self, e):
        logging.info("[TexasPokerClient] on_error: %s", e)
        logging.info("[TexasPokerClient] on_error, wait for 5 secs, reconnect to server...")
        self.reconnect_count += 1
        time.sleep(5)
        if self.reconnect_count > 10:
            raise sys.exit(0)


