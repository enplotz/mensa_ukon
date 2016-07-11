import datetime
import logging
import logging.config
import os
from collections import OrderedDict, namedtuple

import yaml
from telegram import Emoji, ParseMode, ChatAction, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

import settings
from mensa import get_meals

logger = logging.getLogger(__name__)

CMDShortcut = namedtuple('CMDShortcut', ['command', 'meal', 'location', 'short_help'])
SHORTCUTS = [
    CMDShortcut('stamm', 'stammessen', 'giessberg', 'Show main meal'),
    CMDShortcut('wahl', 'wahlessen', 'giessberg', 'Show alternative meal'),
    CMDShortcut('vegi', 'vegetarisch', 'giessberg', 'Show vegetarian meal'),
    CMDShortcut('eintopf', 'eintopf', 'giessberg', 'Show stew'),
    CMDShortcut('abendessen', 'abendessen', 'themenpark', 'Show dinner'),
    CMDShortcut('grill', 'grill', 'themenpark', 'Show grill'),
    CMDShortcut('bio', 'bioessen', 'themenpark', 'Show bio'),
    CMDShortcut('wok', 'wok', 'themenpark', 'Show wok'),
]

GREETING = 'Hello, human!\n' \
           'I am a bot to retrieve the culinary offerings of Uni Konstanz\' canteen. ' \
           'I can understand several date formats like \'today\', \'tomorrow\' and ones ' \
           'formatted like \'YYYY-MM-DD\'.\n' \
           'Please forgive me if I sometimes do not work, you see, ' \
           'I\'m quite new and still adjusting to this world :).\n\n'

INTRO_HELP = 'It looks like you may need help.\n'
INTRO_COMMANDS = 'Here are my *commands*:\n'

DATE_HELP = '\[<date>] get what offerings are waiting for you at the specified date ' \
            'formatted like \'YYYY-MM-DD\'.'

EXAMPLES = ' \n\n' \
           '*Examples:*\n' \
           '/mensa tomorrow\n' \
           '/mensa 2016-02-24\n'

BOT_COMMANDS = []


def print_commands():
    # we want to print both commands for the bot, as well as commands to get meals
    return "\n".join(map(lambda c: '/' + c[0] + ' ' + c[1], BOT_COMMANDS)) \
           + '\n' \
           + "\n".join(map(lambda c: '/' + c.command + ' ' + c.short_help, SHORTCUTS))


def start(bot, update):
    chat_id = update.message.chat.id
    bot.sendMessage(chat_id=chat_id, text=GREETING + '\n' + INTRO_COMMANDS + print_commands() + EXAMPLES,
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=True)


def help(bot, update):
    """Prints help text"""

    chat_id = update.message.chat.id
    bot.sendMessage(chat_id=chat_id,
                    text=INTRO_HELP + INTRO_COMMANDS + print_commands() + EXAMPLES,
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=True)

# TODO custom keyboard with emoji as meals

def mensa_plan_all(bot, update, args):
    _mensa_plan(bot, update, args)

def _sort_meals(order, meals):
    ordered_meals = OrderedDict(sorted(meals.items(), key=lambda t: order[t[0]]))
    return ordered_meals

def _mensa_plan(bot, update, meal=None, meal_location=None, args=None):
    # /mensa [today|tomorrow|date]
    # currently, we only support dates* in the args parameter
    chat_id = update.message.chat.id
    date = datetime.date.today()
    try:
        if args and len(args) > 0:
            date_arg = args[0]

            if date_arg == 'today':
                pass
            elif date_arg == 'tomorrow':
                date += datetime.timedelta(days=1)
            else:
                date = datetime.datetime.strptime(date_arg, '%Y-%m-%d').date()

        bot.sendChatAction(chat_id=chat_id, action=ChatAction.TYPING)

        logger.debug('Filter for: %s' % meal)
        # [(Location, Dict)]
        meals = get_meals(date, locations=[meal_location] if meal_location else None,
                          filter_meals=[meal] if meal else None)
        msg_text = ''
        if meal:
            # only print the specific locations' meal
            m = meals[0][1]
            msg_text = '\n'.join(['%s %s:\n' % (Emoji.FORK_AND_KNIFE, date.strftime('%Y-%m-%d')), '*%s:* %s' % m[meal]])
        else:
            # first mensa, then themenpark
            for loc_meals in meals:
                if len(loc_meals[1]) > 0:
                    lines = [
                        '\n%s %s %s:\n' % (Emoji.FORK_AND_KNIFE, loc_meals[0].nice_name, date.strftime('%Y-%m-%d'))]

                    ordered_meals = _sort_meals(loc_meals[0].order, loc_meals[1])
                    for i in ordered_meals.items():
                        lines.append('*%s:* %s' % i[1])
                    msg_text += '\n'.join(lines) + '\n'
                else:
                    msg_text += 'No meals found for %s at %s %s\n' % (
                    date.strftime('%Y-%m-%d'), loc_meals[0].nice_name, Emoji.LOUDLY_CRYING_FACE)

        bot.sendMessage(chat_id=chat_id, text=msg_text,
                        parse_mode=ParseMode.MARKDOWN,
                        disable_web_page_preview=True)
    except ValueError:
        bot.sendMessage(chat_id, text='Usage: /mensa [<date>]')

def add_bot_command(dispatcher, command_text, command, help, pass_args=False):
    dispatcher.add_handler(CommandHandler(command_text, command, pass_args=pass_args))
    BOT_COMMANDS.append((command_text, help))


def add_meal_command(dispatcher, cmd_shortcut):
    callback = CommandHandler(cmd_shortcut.command,
                             lambda bot, update, args :
                                    _mensa_plan(bot, update, cmd_shortcut.meal, cmd_shortcut.location, args=args),
                             pass_args=True)
    dispatcher.add_handler(callback)


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
    logger.info('Recieved unknown command: {}'.format(update.message))


def setup_logging(default_path='mensa_bot/logging.yaml', default_level=logging.INFO, env_key='PTB_LOG_CONF',
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
        logger.info('Using {} as logging config path.'.format(path))
    else:
        logging.basicConfig(level=default_level, format=default_format)
        logger.info('Using default logging parameters.')


# Telegram bot framework setup
setup_logging()
updater = Updater(settings.TOKEN, workers=settings.WORKERS)
dp = updater.dispatcher


# Custom command handlers
add_bot_command(dp, 'start', start, 'start bot')
add_bot_command(dp, 'help', help, 'display help message')
add_bot_command(dp, 'mensa', mensa_plan_all, DATE_HELP, pass_args=True)
# alias for autocorrected command
# dp.add_handler(CommandHandler('Mensa', mensa_plan_all, pass_args=True))

# shortcuts to direct offers
for cmd in SHORTCUTS:
    add_meal_command(dp, cmd)


# Again telegram bot framework code
dp.add_error_handler(error)
dp.add_handler(MessageHandler([Filters.command], unknown))

q = updater.job_queue

if settings.USE_POLLING:
    logging.info('Bot running with polling enabled.')
    update_queue = updater.start_polling()
    updater.idle()
else:
    webhook_url = 'https://%s:%s/%s' % (settings.URL, settings.LISTEN_PORT, settings.TOKEN)
    logging.info('Bot running with webhook on %s' % webhook_url)
    # You can also set the webhook yourself (via cURL) or delete it sending an empty url.
    # Note that for self-signed certificates, you also have to send the .pem certificate file
    # to the Telegram API.

    # Send the certificate and set the webhook url
    updater.bot.setWebhook(webhook_url=webhook_url,
                           certificate=open(settings.CERT, 'rb'))

    # Actually start our bot
    update_queue = updater.start_webhook(
        listen=settings.LISTEN_IP,
        port=settings.LISTEN_PORT,
        url_path=settings.TOKEN,
        cert=settings.CERT,
        key=settings.CERT_KEY,
        webhook_url=webhook_url)
