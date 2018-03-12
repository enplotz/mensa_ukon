import logging
import logging.config

import click

from mensa_ukon import version
from mensa_ukon.constants import Verbosity, Canteen
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
@click.option('-v', '--verbosity', count=True)
@click.version_option(version=version.__version__)
def run_bot(verbosity):
    _setup_logging(verbosity)
    try:
        bot = MensaBot()
        # TODO simple plugins for different canteens
        logger.info('Running bot.')
        bot.run()
    except BotError as e:
        show_exc = logging.DEBUG == Verbosity.getLoglevelForCount(verbosity)
        logger.error(e, exc_info=show_exc)
        quit()

if __name__ == '__main__':
    run_bot()
