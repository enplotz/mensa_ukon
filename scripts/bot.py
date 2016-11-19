import logging
import logging.config
import os

import click
import yaml
from mensa_ukon import version
from mensa_ukon.constants import Canteen, DEFAULT_CANTEENS, Verbosity
from mensa_ukon.mensabot import MensaBot

logger = logging.getLogger('MensaBot')

def _setup_logging(verbosity, default_path='logging.yaml', default_level=logging.INFO, env_key='PTB_LOG_CONF',
                  default_format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'):
    """ Setup logging for the bot.
    :param default_path: default path for config
    :param default_level: default level
    :param env_key: environment key used to alter config path
    :param default_format: default format
    """
    path = default_path
    other_path = os.environ.get(env_key, None)

    if verbosity > 0:
        level = Verbosity.getLoglevelForCount(verbosity)
        default_level = level
        logger.setLevel(default_level)
        logger.info('Overwriting default log level from command line to {}'.format(logging.getLevelName(level)))
        # FIXME correct logging for all libraries and bot...

    if other_path:
        path = other_path
    if os.path.exists(path):
        with open(path, 'rt') as f:
            config = yaml.load(f.read())
        logging.config.dictConfig(config)
        logger.info('Using %s as logging config path.', path)
    else:
        logging.basicConfig(level=default_level, format=default_format)
        logger.info('Using default logging parameters.')


@click.command()
@click.option('-c', '--canteen', type=click.Choice(Canteen), multiple=True, default=DEFAULT_CANTEENS, help='restrict output to specific canteen')
@click.option('-v', '--verbosity', count=True)
@click.version_option(version=version.__version__)
def run_bot(canteen, verbosity):
    # Telegram bot framework setup
    _setup_logging(verbosity)
    logger.info('Starting bot for canteens: {}'.format(canteen))
    # TODO sub-commands for webhook/polling
    MensaBot(canteen).run()


