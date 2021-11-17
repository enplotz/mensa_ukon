#! /usr/bin/env python

from collections import OrderedDict
# from enum import Enum, unique
from logging import DEBUG, INFO, WARN, ERROR
from collections import namedtuple as n
from aenum import Enum
from mensa_ukon.emojize import Emojize

# Some minimum headers we need to send in order to get a response
HEADERS = {
    'Content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'Accept-Encoding': 'gzip, deflate'
}

# @unique
class Verbosity(Enum):
    error = ERROR
    warn = WARN
    info = INFO
    debug = DEBUG

    def __str__(self):
        return str(self.value)

    @classmethod
    def getLoglevelForCount(cls, verbosity):
        '''Gets the log level for a specific count of -v switches from click.'''
        # ERROR currently has the highest numerical value we use, so just use it for now
        return Verbosity(
            Verbosity(ERROR).value - (max(min(len(Verbosity.__members__) - 1, verbosity), 0) * 10)).value

# Plan(Location, dict)
FORMATTERS = OrderedDict({
    'plain': lambda plan: '\033[1m# {}\033[0m\n\n'.format(plan.location.nice_name)
                          + '\n'.join(['\033[1m{}{}: \033[0m {}'.format(meal[0], Emojize.as_str(meal[2]), meal[1]) for meal in plan.meals.values()]),
    # 'json': lambda entries: json.dumps(entries)
})

Format = n('Enum', FORMATTERS.keys())._make(FORMATTERS.keys())


# Mo. 13.08.
# Mon. 13.08.
class Language(Enum, init='date_fmt'):
    DE = 'dd DD.MM.'
    EN = 'ddd DD.MM.'


class Location(object):
    def __init__(self, key, nice_name, shortcut, order=None, days_open=10):
        self.key = key
        self.nice_name = nice_name
        self.shortcut = shortcut
        self.order = order
        self.days_open = days_open

    def __str__(self):
        return 'Location("%s", "%s", "%s")' % (self.key, self.nice_name, self.shortcut)

    def __repr__(self):
        return self.__str__()

CANTEENS = OrderedDict({
    'giessberg': Location('mensa-giessberg', 'Uni Konstanz', 'giessberg', days_open=12),
    'htwg': Location('mensa-htwg', 'HTWG', 'htwg'),
    'fn': Location('mensa-friedrichshafen', 'Friedrichshafen', 'fn'),
    'weingarten': Location('mensa-weingarten', 'Weingarten', 'weingarten'),
    'rave': Location('mensa-ravensburg', 'Ravensburg', 'rave'),
})

Canteen = n('Enum', CANTEENS.keys())._make(CANTEENS.keys())
