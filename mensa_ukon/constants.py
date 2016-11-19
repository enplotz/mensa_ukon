#! /usr/bin/env python
import json
from collections import OrderedDict
from enum import Enum, unique
from logging import DEBUG, INFO, WARN, ERROR
from collections import namedtuple as n

ENDPOINT = 'https://www.max-manager.de/daten-extern/seezeit/html/inc/ajax-php_konnektor.inc.php'

# Some minimum headers we need to send in order to get a response
HEADERS = {
    'Content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'Accept-Encoding': 'gzip, deflate'
}


@unique
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


def _plain(canteens):
    return '\n'.join(
        ['# {}\n'.format(mensa.nice_name) + '\n'.join(['{}: {}'.format(pair[0], pair[1]) for name, pair in
                                                       sorted(entries.items())]) for mensa, entries in
         canteens])


FORMATTERS = OrderedDict({'plain': lambda canteens: _plain(canteens),
            'json': lambda entries: json.dumps(entries)})
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

DEFAULT_CANTEENS = ['giessberg', 'themenpark']

CANTEENS = OrderedDict({
    'giessberg': Location('mensa_giessberg', 'Uni', 'giessberg', {
        'stammessen': 0, 'wahlessen': 1, 'vegetarisch': 2, 'beilagen': 3, 'eintopf': 4, 'al_studente': 5
    }),
    'themenpark': Location('themenpark_abendessen', 'Themenpark & Abendessen', 'themenpark', {
        'wok': 2, 'grill': 0, 'bioessen': 1, 'abendessen': 3
    }),
    'htwg': Location('mensa_htwg', 'HTWG', 'htwg'),
    'fn': Location('mensa_friedrichshafen', 'Friedrichshafen', 'fn'),
    'weingarten': Location('mensa_weingarten', 'Weingarten', 'weingarten'),
    'rave': Location('mensa_ravensburg', 'Ravensburg', 'rave'),
})

Canteen = n('Enum', CANTEENS.keys())._make(CANTEENS.keys())
