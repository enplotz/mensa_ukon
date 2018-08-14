import logging
import logging.config

import click

from mensa_ukon import version, setup_logging, Verbosity
from mensa_ukon.constants import Verbosity
from mensa_ukon.mensabot import MensaBot, BotError

@click.command()
@click.option('-v', '--verbosity', count=True)
@click.version_option(version=version.__version__)
def run_bot(verbosity):
    setup_logging(verbosity)
    try:
        bot = MensaBot()
        # TODO simple plugins for different canteens
        bot.logger.info('Running bot.')
        bot.run()
    except BotError as e:
        show_exc = logging.DEBUG == Verbosity.getLoglevelForCount(verbosity)
        logging.getLogger(__name__).error(e, exc_info=show_exc)
        quit()

if __name__ == '__main__':
    run_bot()
