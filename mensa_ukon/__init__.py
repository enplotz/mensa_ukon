'''An in-official library to retrieve the canteen plan of the University of Konstanz'''

import logging

from enum import Enum, unique

from logging import DEBUG, INFO, WARN, ERROR, NullHandler
from logging.config import dictConfig


from .mensa import Mensa
from .version import __version__  # flake8: noqa

logging.getLogger(__name__).addHandler(NullHandler())

__all__ = [
    'Mensa', 'MensaBot'
]

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


logging_config = dict(
    version = 1,
    formatters = {
        'f': {'format':
              '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'}
        },
    handlers = {
        'h': {'class': 'logging.StreamHandler',
              'formatter': 'f',
              'level': logging.DEBUG}
        },
    root = {
        'handlers': ['h'],
        'level': logging.DEBUG,
        },
    loggers = {
        'mensa_ukon.mensa': {
            'handlers': ['h'],
            'level': 'WARN',
            'propagate': False
        },
        'scripts.mensa_cli': {
            'handlers': ['h'],
            'level': 'WARN',
            'propagate': False
        },
        'scripts.bot': {
            'handlers': ['h'],
            'level': 'WARN',
            'propagate': False
        },
        'telegram': {
            'handlers': ['h'],
            'level': 'WARN',
        },
        'telegram.bot': {
            'handlers': ['h'],
            'level': 'WARN',
        },
        'telegram.ext.updater': {
            'handlers': ['h'],
            'level': 'WARN',
        },
        'telegram.ext.dispatcher': {
            'handlers': ['h'],
            'level': 'WARN',
        }
    }
)


def setup_logging(verbosity):
    level = Verbosity.getLoglevelForCount(verbosity)
    name =  logging.getLevelName(level)
    logging_config['loggers']['scripts.mensa_cli']['level'] = name
    logging_config['loggers']['scripts.bot']['level'] = name
    logging_config['loggers']['mensa_ukon.mensa']['level'] = name
    dictConfig(logging_config)
    logging.getLogger(__name__).info('Verbosity has set the logging level to %s', name)

