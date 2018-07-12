import logging
import json

from collections import namedtuple

logger = logging.getLogger(__name__)


class JsonDecryptor(object):
    @staticmethod
    def to_object(data):
        o = json.loads(data, object_hook=lambda d: namedtuple('o', d.keys())(*d.values()))
        return o


class MessageDispatcher(object):
    def __init__(self, events):
        self.events = events

    def dispatch_msg(self, msg):
        json_msg = json.dumps(msg, ensure_ascii=False)
        data = JsonDecryptor().to_object(json_msg)
        for key, value in self.events.items():
            if key == data.eventName:
                self.events[key](data)
                logging.info('receive_from_events [%s] from server.', data.eventName)


