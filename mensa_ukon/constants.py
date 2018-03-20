#! /usr/bin/env python
import json
from collections import OrderedDict
from collections import namedtuple as n

# Some minimum headers we need to send in order to get a response
HEADERS = {
    'Content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'Accept-Encoding': 'gzip, deflate'
}

# Plan(Location, dict)
FORMATTERS = OrderedDict({
    'plain': lambda plan: '\033[1m# {}\033[0m\n\n'.format(plan.location.nice_name)
                          + '\n'.join(['\033[1m{}: \033[0m {}'.format(meal[0], meal[1]) for meal in plan.meals.values()]),
    # 'json': lambda entries: json.dumps(entries)
})

Format = n('Enum', FORMATTERS.keys())._make(FORMATTERS.keys())

_languages = ['de', 'en']
Language = n('Enum', _languages)._make(_languages)

class Location(object):
    def __init__(self, key, nice_name, shortcut, order=None):
        self.key = key
        self.nice_name = nice_name
        self.shortcut = shortcut
        self.order = order

    def __str__(self):
        return 'Location("%s", "%s", "%s")' % (self.key, self.nice_name, self.shortcut)

    def __repr__(self):
        return self.__str__()

CANTEENS = OrderedDict({
    'giessberg': Location('mensa-giessberg', 'Uni Konstanz', 'giessberg'),
    'htwg': Location('mensa-htwg', 'HTWG', 'htwg'),
    'fn': Location('mensa-friedrichshafen', 'Friedrichshafen', 'fn'),
    'weingarten': Location('mensa-weingarten', 'Weingarten', 'weingarten'),
    'rave': Location('mensa-ravensburg', 'Ravensburg', 'rave'),
})

Canteen = n('Enum', CANTEENS.keys())._make(CANTEENS.keys())
