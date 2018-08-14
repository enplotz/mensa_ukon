#! /usr/bin/env python


import logging
import sys
import pendulum

import click
from click_datetime import Datetime
from mensa_ukon import version
from mensa_ukon.constants import Language, Verbosity, Format, FORMATTERS, Canteen
from mensa_ukon.mensa import Mensa

logger = logging.getLogger(__name__)


def _setup_logging(verbosity):
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    level = Verbosity.getLoglevelForCount(verbosity)

    for mod in ['scripts', 'mensa_ukon']:
        mod_logger = logging.getLogger(mod)
        mod_logger.addHandler(h)
        mod_logger.setLevel(level)
        mod_logger.info('Verbosity has set the logging level of %s to %s', mod_logger.name, logging.getLevelName(level))


@click.command()
@click.option('-d', '--date', type=Datetime(format='%Y-%m-%d'), default=pendulum.today,
              help='date for the plan (default: today; format: Y-m-d)')
@click.option('-l', '--language', type=click.Choice(Language.__members__), default=Language.DE, help='language of the descriptions')
@click.option('-c', '--canteen', type=click.Choice(Canteen), multiple=False, default='giessberg', help='restrict output to specific canteen')
@click.option('-f', '--format', type=click.Choice(list(Format)), default=Format.plain, help='output format')
@click.option('-v', '--verbosity', count=True)
@click.argument('filter_meal', required=False)
@click.version_option(version=version.__version__)
def meals(date, language, canteen, format, verbosity, filter_meal):
    """This script retrieves specified meals from the canteen plan of the University of Konstanz."""

    _setup_logging(verbosity)

    language = Language.__members__[language]

    logger.debug('Date: {}'.format(date))
    logger.debug('Language: {}'.format(language))
    logger.debug('Canteen: {}'.format(canteen))
    logger.debug('Format: {}'.format(format))
    logger.debug('Verbosity: {}'.format(verbosity))
    logger.debug('Meal filter: {}'.format(filter_meal))

    m = Mensa(canteen)

    logger.info('Retrieving meals...')
    plan = m.retrieve(date, language, filter_meal)

    if plan.meals:
        l = len(plan.meals)
        logger.debug('Found {0} meal{1}!'.format(l, '' if l == 1 else 's'))
        click.echo(FORMATTERS[format](plan))
        sys.exit(0)
    else:
        print(date)
        click.echo('No meals found for date {0}.'.format(date.format('dddd DD MMMM YYYY')))
        sys.exit(0)
