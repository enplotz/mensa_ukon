#! /usr/bin/env python

import logging
from datetime import datetime

import click
from click_datetime import Datetime
from mensa_ukon import version
from mensa_ukon.constants import Language, Canteen, Verbosity, Format
from mensa_ukon.mensa import Mensa

logger = logging.getLogger(__name__)


def _setup_logging(verbosity):
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    logger.addHandler(h)
    level = Verbosity.getLoglevelForCount(verbosity)
    logger.setLevel(level)
    logger.info('Verbosity has set the logging level to %s', logging.getLevelName(level))


@click.command()
@click.option('-d', '--date', type=Datetime(format='%Y-%m-%d'), default=datetime.today,
              help='date for the plan (default: today; format: Y-m-d)')
@click.option('-l', '--language', type=click.Choice(Language), default=Language.de, help='language of the descriptions')
@click.option('-c', '--canteen', type=click.Choice(Canteen), help='restrict output to specific canteen')
@click.option('-f', '--format', type=click.Choice(Format), default=Format.plain, help='output format')
@click.option('-v', '--verbosity', count=True)
# @click_log.simple_verbosity_option()
# @click_log.init(__name__)
@click.argument('meals', nargs=-1)
@click.version_option(version=version.__version__)
def meals(date, language, canteen, format, verbosity, meals):
    '''This script retrieves specified meals from the canteen plan of the University of Konstanz.'''

    _setup_logging(verbosity)

    m = Mensa(canteen, language)
    logger.info('retrieving meals...')
    canteens = m.retrieve(date, meals)
    l = len(canteens)
    if canteens and l > 0:
        logger.debug('found {0} meal{1}!'.format(l, '' if l == 1 else 's'))
        click.echo(format.fmt(canteens))
    else:
        logger.error('No meals found for day {0}.'.format(date))
