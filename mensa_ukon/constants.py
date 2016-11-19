#! /usr/bin/env python
import json
from enum import Enum, unique
from logging import DEBUG, INFO, WARN, ERROR


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


class FormatProxy:
    def __init__(self, name, func):
        self.name = name
        self.func = func

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)

    def __repr__(self):
        return self.name


@unique
class Format(Enum):
    plain = FormatProxy('plain', lambda canteens: Format.__plain__(canteens))
    json = FormatProxy('json', lambda entries: json.dumps(entries))

    @classmethod
    def __plain__(cls, canteens):
        return '\n'.join(
            ['# {}\n'.format(mensa.nice_name) + '\n'.join(['{}: {}'.format(pair[0], pair[1]) for name, pair in
                                                                 sorted(entries.items())]) for mensa, entries in
             canteens])

    def fmt(self, canteens):
        return self.value(canteens)


@unique
class Language(str, Enum):
    de = 'de'
    en = 'en'


@unique
class Canteen(str, Enum):
    giessberg = 'mensa_giessberg'
    themenpark = 'themenpark_abendessen'
