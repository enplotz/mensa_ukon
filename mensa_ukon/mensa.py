#! /usr/bin/env python

'''Mensa class'''
import logging

import click
from mensa import Location

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class Mensa(object):
    '''Mensa class providing functionality to access canteen plans'''

    def __init__(self, canteen, language):
        '''Constructor.'''
        logger.error('wat')
        self.canteen = canteen
        self.language = language

    def retrieve(self, date, meals=None):
        return [
            [
                Location('c0', 'Canteen 0', 'c0'),
                {'k0': 'v0', 'k1': 'v1'}
            ],
            [
                Location('c1', 'Canteen 1', 'c1'),
                {}
            ]
        ]
