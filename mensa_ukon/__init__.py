'''An in-official library to retrieve the canteen plan of the University of Konstanz'''

import logging
from logging import NullHandler

from .mensa import Mensa
from .version import __version__  # flake8: noqa

logging.getLogger(__name__).addHandler(NullHandler())

__all__ = [
    'Mensa', 'MensaBot'
]
