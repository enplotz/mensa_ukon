import datetime
import logging
import logging.config
import os
import re
import settings
from collections import \
    OrderedDict

import yaml
from telegram import Emoji, ParseMode, ChatAction, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

from mensa_ukon import get_meals

logger = logging.getLogger(__name__)

RE_DATE_FORMAT = re.compile('\d{4}-\d{2}-\d{2}')

PDF_URL_THIS_WEEK = 'https://www.max-manager.de/daten-extern/seezeit/pdf/wochenplaene/mensa_giessberg/aktuell.pdf'
PDF_URL_NEXT_WEEK = 'https://www.max-manager.de/daten-extern/seezeit/pdf/wochenplaene/mensa_giessberg/naechste-woche.pdf'

NOTIFY_CHATS = []

COMMANDS = []

greetings = 'Hello, human!\n' \
            'I am a bot to retrieve the culinary offerings of Uni Konstanz\' canteen. ' \
            'I can understand several date formats like \'today\', \'tomorrow\' and ones ' \
            'formatted like \'YYYY-MM-DD\'.\n' \
            'Please forgive me if I sometimes do not work, you see, ' \
            'I\'m quite new and still adjusting to this world :).\n\n'

INTRO_HELP = 'So, you need help?\n'

INTRO_COMMANDS = 'Here are my *commands*:\n'

def print_commands():
    return "\n".join(map(lambda c: '/' + c[0] + ' ' + c[1], COMMANDS))

EXAMPLES = ' \n\n' \
           '*Examples:*\n' \
           '/mensa tomorrow\n' \
           '/mensa 2016-02-24\n'


def start(bot, update):
    chat_id = update.message.chat.id
    bot.sendMessage(chat_id=chat_id,
                                    text=greetings + '\n' + INTRO_COMMANDS + print_commands() + EXAMPLES,
                                    parse_mode=ParseMode.MARKDOWN,
                                    disable_web_page_preview=True)


def help(bot, update):
    """Prints help text"""

    chat_id = update.message.chat.id
    bot.sendMessage(chat_id=chat_id,
                    text=INTRO_HELP + INTRO_COMMANDS + print_commands() + EXAMPLES,
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=True)


def m_plan_keyboard(bot, update):
    chat_id = update.message.chat.id
    custom_keyboard = [['/mensa today', '/mensa tomorrow']]
    reply_markup = ReplyKeyboardMarkup(custom_keyboard, selective=True, one_time_keyboard=True)
    bot.sendMessage(chat_id=chat_id, text='Quick-access menu.', reply_markup=reply_markup)


def mensa_plan_stamm(bot, update, args):
    _mensa_plan(bot, update, args, meal='stammessen', meal_location='giessberg')


def mensa_plan_wahl(bot, update, args):
    _mensa_plan(bot, update, args, meal='wahlessen', meal_location='giessberg')


def mensa_plan_veg(bot, update, args):
    _mensa_plan(bot, update, args, meal='vegetarisch', meal_location='giessberg')


def mensa_plan_eintopf(bot, update, args):
    _mensa_plan(bot, update, args, meal='eintopf', meal_location='giessberg')


def mensa_plan_abendessen(bot, update, args):
    _mensa_plan(bot, update, args, meal='abendessen', meal_location='themenpark')


def mensa_plan_bio(bot, update, args):
    _mensa_plan(bot, update, args, meal='bioessen', meal_location='themenpark')


def mensa_plan_wok(bot, update, args):
    _mensa_plan(bot, update, args, meal='wok', meal_location='themenpark')


def mensa_plan_grill(bot, update, args):
    _mensa_plan(bot, update, args, meal='grill', meal_location='themenpark')


def mensa_plan_all(bot, update, args):
    _mensa_plan(bot, update, args)


def _sort_meals(order, meals):
    logger.debug(meals)
    logger.debug(order)
    ordered_meals = OrderedDict(sorted(meals.items(), key=lambda t: order[t[0]]))
    logger.debug(ordered_meals)
    return ordered_meals

def week_plan(bot, update, args, this_week=True):
    url = PDF_URL_THIS_WEEK if this_week else PDF_URL_NEXT_WEEK
    chat_id = update.message.chat.id
    bot.sendPhoto(chat_id=chat_id, photo='https://telegram.org/img/t_logo.png')

def _mensa_plan(bot, update, args=None, chat_id=None, meal=None, meal_location=None):
    # /mensa [today|tomorrow|date]
    chat_id = chat_id or update.message.chat.id
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
        logger.debug('Filtered: %s' % meals)
        msg_text = ''
        if meal:
            # only print the specific locations' meal
            m = meals[0][1]
            msg_text = '\n'.join(['%s %s:\n' % (Emoji.FORK_AND_KNIFE, date.strftime('%Y-%m-%d')), '*%s:* %s' % m[meal]])
        else:
            # first mensa, then themenpark
            for loc_meals in meals:
                if len(loc_meals[1]) > 0:
                    lines = ['\n%s %s %s:\n' % (Emoji.FORK_AND_KNIFE, loc_meals[0].nice_name, date.strftime('%Y-%m-%d'))]

                    ordered_meals = _sort_meals(loc_meals[0].order, loc_meals[1])
                    for i in ordered_meals.items():
                        lines.append('*%s:* %s' % i[1])
                    msg_text += '\n'.join(lines) + '\n'
                else:
                    msg_text += 'No meals found for %s at %s %s\n' % (date.strftime('%Y-%m-%d'), loc_meals[0].nice_name, Emoji.LOUDLY_CRYING_FACE)

        bot.sendMessage(chat_id=chat_id, text=msg_text,
                        parse_mode=ParseMode.MARKDOWN,
                        disable_web_page_preview=True)
    except ValueError:
        bot.sendMessage(chat_id, text='Usage: /mensa [<date>]')

def add_handler(dispatcher, cmd, handler, help_text, pass_args=True):
    COMMANDS.append((cmd, help_text))
    dispatcher.add_handler(CommandHandler(cmd, handler, pass_args=pass_args))

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


SHORTCUTS = [
             ('grill', mensa_plan_grill, 'show grill'),
             ('bio', mensa_plan_bio, 'show bio'),
             ('wok', mensa_plan_wok, 'show wok'),
             ('vegi', mensa_plan_veg, 'show vegetarian meal'),
             ('stamm', mensa_plan_stamm, 'show main meal'),
             ('wahl', mensa_plan_wahl, 'show alternative meal'),
             ('eintopf', mensa_plan_eintopf, 'show stew'),
             ('abendessen', mensa_plan_abendessen, 'show dinner'),
             ]


def todays_menu(bot, chat_id):
    bot.sendMessage(chat_id=chat_id, text='Today\'s menu:')
    _mensa_plan(bot, None, chat_id=chat_id)


def main():
    setup_logging()

    updater = Updater(settings.TOKEN, workers=settings.WORKERS)

    dp = updater.dispatcher

    dp.add_handler(CommandHandler('start', start))
    add_handler(dp, 'help', help, 'display help message', pass_args=False)
    mensa_help = '\[<date>] get what offerings are waiting for you at the specified date ' \
                 'formatted like \'YYYY-MM-DD\'.'
    add_handler(dp, 'mensa', mensa_plan_all, mensa_help)
    # alias for autocorrected command
    dp.add_handler(CommandHandler('Mensa', mensa_plan_all, pass_args=True))
    add_handler(dp, 'm', m_plan_keyboard, 'show quick-access menu', pass_args=False)

    # shortcuts to direct offers
    for cmd, f, h in SHORTCUTS:
        add_handler(dp, cmd, f, h)
        dp.add_handler(CommandHandler(cmd.capitalize(), f))

    dp.add_handler(CommandHandler('week', week_plan))

    dp.add_handler(CommandHandler('todays', lambda bot, update : todays_menu(bot, chat_id=19412593)))

    dp.add_error_handler(error)
    dp.add_handler(MessageHandler([Filters.command], unknown))

    q = updater.job_queue

    logger.debug('Installing notifications for chats: {}'.format(settings.NOTIFY_CHATS))
    for chat in settings.NOTIFY_CHATS:
        q.put(lambda bot : todays_menu(bot, chat_id=chat), 20)

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


if __name__ == '__main__':
    main()
