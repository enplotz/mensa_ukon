import importlib
import logging
import logging.config

import click
from dotenv import load_dotenv

import mensa_ukon
from mensa_ukon import version, settings, utils
from mensa_ukon.constants import Canteen, DEFAULT_CANTEENS, Verbosity
from mensa_ukon.mensabot import MensaBot, BotError

logger = logging.getLogger('MensaBot')

def _setup_logging(verbosity, default_level=logging.INFO,
                   default_format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'):
    """ Setup logging for the bot.
    :param default_level: default level
    :param default_format: default format
    """

    if verbosity > 0:
        level = Verbosity.getLoglevelForCount(verbosity)
        default_level = level
        logger.setLevel(default_level)
        logger.info('Overwriting default log level from command line to {}'.format(logging.getLevelName(level)))
        # FIXME correct logging for all libraries and bot...

    logging.basicConfig(level=default_level, format=default_format)
    logger.info('Using default logging parameters.')


@click.command()
@click.option('-c', '--canteen', type=click.Choice(Canteen), multiple=True, default=DEFAULT_CANTEENS, help='restrict output to specific canteen')
@click.option('-e', '--env', help='.env file location to load variables from')
@click.option('-v', '--verbosity', count=True)
@click.version_option(version=version.__version__)
def run_bot(canteen, verbosity, env):
    # Telegram bot framework setup
    _setup_logging(verbosity)
    try:
        utils.load_from_env(env)

        if settings.TOKEN is None:
            logger.exception('Missing required bot token. Quitting...')
            quit()

        logger.info('Starting bot for canteens: {}'.format(canteen))
        # TODO sub-commands for webhook/polling
        MensaBot(canteen).run()
    except BotError as e:
        show_exc = logging.DEBUG == Verbosity.getLoglevelForCount(verbosity)
        logger.error(e, exc_info=show_exc)
        quit()

