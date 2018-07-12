import logging
import os

from glob import glob
from importlib import import_module

logger = logging.getLogger(__name__)


class EventManager(object):

    events = {}

    def __init__(self):
        self.plugins = 'plugins.events'

    @staticmethod
    def init_event(plugin='plugins.events'):
        logging.info('loading event plugin "%s"', plugin)
        path_name = None

        from importlib.util import find_spec as importlib_find

        path_name = importlib_find(plugin)
        try:
            path_name = path_name.submodule_search_locations[0]
        except TypeError:
            path_name = path_name.origin

        module_list = [plugin]
        if not path_name.endswith('.py'):
            module_list = glob('{}/[!_]*.py'.format(path_name))
            module_list = ['.'.join((plugin, os.path.split(f)[-1][:-3])) for f in module_list]

        for module in module_list:
            try:
                import_module(module)
            except:
                logger.exception('Failed to import %s', module)

    def get_events(self):
        return self.events


class Event(object):
    def __init__(self, name):
        self.name = name



