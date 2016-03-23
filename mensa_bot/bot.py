import datetime
import logging
import logging.config
import os
import re
from os.path import join, dirname

import yaml
from dotenv import load_dotenv
from mensa_ukon import get_meals
from telegram import Updater, Emoji, ParseMode, ChatAction, ReplyKeyboardMarkup

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

logger = logging.getLogger(__name__)

TOKEN = os.environ.get('PTB_TELEGRAM_BOT_TOKEN')
USE_POLLING = os.environ.get('PTB_USE_POLLING', True)
RE_DATE_FORMAT = re.compile('\d{4}-\d{2}-\d{2}')

greetings = 'Hello!\n' \
            'I am a bot to retrieve the culinary offerings of Uni Konstanz\' canteen. ' \
            'I can understand several date formats like \'today\', \'tomorrow\' and ones ' \
            'formatted like \'YYYY-MM-DD\'.\n'

help_text = '*My commands:*\n' \
            '/help         - display help message\n' \
            '/mensa \[<date>] - get what offerings are waiting for you at the specified date\n' \
            '\n' \
            'Examples:\n' \
            '/mensa tomorrow\n' \
            '/mensa 2016-02-24\n'


def start(bot, update):
    chat_id = update.message.chat.id
    bot.sendMessage(bot.sendMessage(chat_id=chat_id,
                                    text=greetings + '\n' + help_text,
                                    parse_mode=ParseMode.MARKDOWN,
                                    disable_web_page_preview=True))


def help(bot, update):
    """Prints help text"""

    chat_id = update.message.chat.id
    bot.sendMessage(chat_id=chat_id,
                    text=help_text,
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=True)


def m_plan_keyboard(bot, update):
    chat_id = update.message.chat.id
    custom_keyboard = [['/mensa today', '/mensa tomorrow']]
    reply_markup = ReplyKeyboardMarkup(custom_keyboard, selective=True, one_time_keyboard=True)
    bot.sendMessage(chat_id=chat_id, text='Quick-access menu.', reply_markup=reply_markup)


def mensa_plan(bot, update, args):
    # /mensa [today|tomorrow|date]
    chat_id = update.message.chat.id
    date = datetime.date.today()
    try:
        if len(args) > 0:
            date_arg = args[0]

            if date_arg == 'today':
                pass
            elif date_arg == 'tomorrow':
                date += datetime.timedelta(days=1)
            else:
                date = datetime.datetime.strptime(date_arg, '%Y-%m-%d').date()

        bot.sendChatAction(chat_id=chat_id, action=ChatAction.TYPING)
        meals = get_meals(date)

        if len(meals) > 0:
            keys = sorted(meals.keys())
            lines = ['%s Meals for %s:\n' % (Emoji.FORK_AND_KNIFE, date.strftime('%Y-%m-%d'))]
            for k in keys:
                lines.append('*%s:* %s' % meals[k])
            msg_text = '\n'.join(lines)
        else:
            msg_text = 'There are no meals for %s %s' % (date.strftime('%Y-%m-%d'), Emoji.LOUDLY_CRYING_FACE)

        bot.sendMessage(chat_id=chat_id, text=msg_text,
                        parse_mode=ParseMode.MARKDOWN,
                        disable_web_page_preview=True)
    except ValueError:
        bot.sendMessage(chat_id, text='Usage: /mensa [<date>]')


def error(bot, update, error, **kwargs):
    """ Error handling """
    try:
        logger.error("An error (%s) occurred: %s"
                     % (type(error), error.message))
    except:
        pass


def unknown(bot, update):
    bot.sendMessage(chat_id=update.message.chat.id, text='Sorry, I do not understand that command.\n')
    help(bot, update)


def setup_logging(default_path='logging.yaml', default_level=logging.INFO, env_key='PTB_LOG_CONF',
                  default_format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'):
    """ Setup logging for the bot.
    :param default_path: default path for config
    :param default_level: default level
    :param env_key: environment key used to alter config path
    """
    path = default_path
    other_path = os.environ.get(env_key, None)
    if other_path:
        path = other_path
    if os.path.exists(path):
        with open(path, 'rt') as f:
            config = yaml.load(f.read())
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=default_level, format=default_format)


def main():
    setup_logging()

    updater = Updater(TOKEN, workers=int(os.environ.get('PTB_WORKERS', 2)))

    dp = updater.dispatcher

    dp.addTelegramCommandHandler('start', start)
    dp.addTelegramCommandHandler('help', help)
    dp.addTelegramCommandHandler('mensa', mensa_plan)
    dp.addTelegramCommandHandler('m', m_plan_keyboard)

    dp.addErrorHandler(error)
    dp.addUnknownTelegramCommandHandler(unknown)

    if USE_POLLING:
        logging.info('Bot running with polling enabled.')
        update_queue = updater.start_polling(poll_interval=1, timeout=5)
        updater.idle()
    else:
        logging.info('Bot running with webhook.')
        # You can also set the webhook yourself (via cURL) or delete it sending an empty url.
        # Note that for self-signed certificates, you also have to send the .pem certificate file
        # to the Telegram API.
        updater.bot.setWebhook(webhook_url=os.environ.get('PTB_WEBHOOK_URL'))
        update_queue = updater.start_webhook(os.environ.get('PTB_WEBHOOK_LISTEN_IP'),
                                             os.environ.get('PTB_WEBHOOK_LISTEN_PORT'))


if __name__ == '__main__':
    main()
