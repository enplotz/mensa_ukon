#! /usr/bin/python
import logging
from collections import OrderedDict
from collections import namedtuple

import datetime
from typing import cast

import telegram
from mensa_ukon import Mensa
from mensa_ukon import settings
from mensa_ukon.constants import Language

from telegram import ChatAction
from telegram import Emoji
from telegram import ParseMode
from telegram.ext import CommandHandler
from telegram.ext import Filters
from telegram.ext import MessageHandler
from telegram.ext import Updater


class BotError(Exception):
    """Base Error class."""

    def __init__(self, message):
        super(BotError, self).__init__()
        self.message = message

    def __str__(self):
        return '{}'.format(self.message)


class ArgumentError(BotError):
    """This object represents an Argument Error. It is raised, when the Bot is supplied with illegal arguments."""

    def __init__(self, argument):
        super(ArgumentError, self).__init__('Illegal arguments: {}'.format(argument))

class MensaBot(telegram.Bot):

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

    def __init__(self, canteens):
        super(MensaBot, self).__init__(settings.TOKEN)
        self.logger = logging.getLogger(__name__)
        self.commands = []
        self.mensa = Mensa(canteens)
        self.updater = Updater(settings.TOKEN, workers=settings.WORKERS)
        self.dp = self.updater.dispatcher
        # Custom command handlers
        self._add_bot_command('start', self._start, 'start bot')
        self._add_bot_command('help', self._bot_help, 'display help message')
        self._add_bot_command('mensa', lambda bot, update, args: self._mensa_plan_all(update, args=args),
                              self.DATE_HELP, pass_args=True)
        # alias for autocorrected command
        # dp.add_handler(CommandHandler('Mensa', mensa_plan_all, pass_args=True))
        # shortcuts to direct offers
        for cmd in self.SHORTCUTS:
            self._add_meal_command(cmd)
        # Again telegram bot framework code
        self.dp.add_error_handler(self.error)
        self.dp.add_handler(MessageHandler(Filters.command, self.unknown))



    def run(self):
        if settings.USE_POLLING:
            self.logger.info('Bot running with polling enabled.')
            self.updater.start_polling()
            self.updater.idle()
        else:
            webhook_url = 'https://%s:%s/%s' % (settings.URL, settings.LISTEN_PORT, settings.TOKEN)
            self.logger.info('Bot running with webhook on %s', webhook_url)
            # You can also set the webhook yourself (via cURL) or delete it sending an empty url.
            # Note that for self-signed certificates, you also have to send the .pem certificate file
            # to the Telegram API.

            # Send the certificate and set the webhook url
            self.bot.setWebhook(webhook_url=webhook_url, certificate=open(settings.CERT, 'rb'))

            # Actually start our bot
            self.updater.start_webhook(
                listen=settings.LISTEN_IP,
                port=settings.LISTEN_PORT,
                url_path=settings.TOKEN,
                cert=settings.CERT,
                key=settings.CERT_KEY,
                webhook_url=webhook_url)

    def _add_bot_command(self, command_text, command, help_info, pass_args=False):
        # the german auto-correct tends to capitalize the first word after the slash...
        # so we will add both variants internally bot not report them in the help menu
        # command = lambda bot, update, args: command(update, args=args)
        for c_text in [command_text, command_text.capitalize()]:
            self.dp.add_handler(CommandHandler(c_text, command, pass_args=pass_args))
        self.commands.append((command_text, help_info))

    def _add_meal_command(self, cmd_shortcut):
        for s in [cmd_shortcut.command, cmd_shortcut.command.capitalize()]:
            self.dp.add_handler(CommandHandler(s,
                                               lambda bot, update, args: bot._mensa_plan(update,
                                                                                         meal=cmd_shortcut.meal,
                                                                                         args=args),
                                               pass_args=True))

    @staticmethod
    def _sort_meals(location, meals):
        # sort by custom sort-order or meal name if no order is present
        ordered_meals = OrderedDict(sorted(meals.items(), key=lambda t: location.order[t[0]] if location.order else t[0]))
        return ordered_meals

    @staticmethod
    def _print_commands(bot):
        # we want to print both commands for the bot, as well as commands to get meals
        return "\n".join(map(lambda c: '/' + c[0] + ' ' + c[1], bot.commands)) \
               + '\n' \
               + "\n".join(map(lambda c: '/' + c.command + ' ' + c.short_help, bot.SHORTCUTS))

    @staticmethod
    def _start(bot, update):
        chat_id = update.message.chat.id
        bot.sendMessage(chat_id=chat_id, text=bot.GREETING + '\n' + bot.INTRO_COMMANDS + bot.print_commands() + bot.EXAMPLES,
                        parse_mode=ParseMode.MARKDOWN,
                        disable_web_page_preview=True)

    @staticmethod
    def _bot_help(bot, update):
        """Prints help text"""

        chat_id = update.message.chat.id
        bot.sendMessage(chat_id=chat_id,
                        text=bot.INTRO_HELP + bot.INTRO_COMMANDS + bot.print_commands() + bot.EXAMPLES,
                        parse_mode=ParseMode.MARKDOWN,
                        disable_web_page_preview=True)

    # TODO custom keyboard with emoji as meals

    def _mensa_plan_all(self, update, args):
        self._mensa_plan(update, args=args)

    def _mensa_plan(self, update, meal=None, args=None):
        # /mensa [today|tomorrow|date]
        # currently, we only support dates* in the args parameter
        chat_id = update.message.chat.id
        date = datetime.date.today()
        try:
            if args:
                if len(args) > 1:
                    raise ArgumentError(str(args))
                elif len(args) == 1:
                    date_arg = args[0]

                    if date_arg == 'today':
                        pass
                    elif date_arg == 'tomorrow':
                        date += datetime.timedelta(days=1)
                    else:
                        date = datetime.datetime.strptime(date_arg, '%Y-%m-%d').date()

            self.sendChatAction(chat_id=chat_id, action=ChatAction.TYPING)

            self.logger.debug('Filter for: %s', meal)
            # [(Location, Dict)]
            meals = self.mensa.retrieve(date, Language.de,
                              meals=[meal] if meal else None)
            msg_text = ''
            if meal:
                # only print the specific locations' meal
                m = meals[0][1]
                msg_text = '\n'.join(
                    ['%s %s:\n' % (Emoji.FORK_AND_KNIFE, date.strftime('%Y-%m-%d')), '*%s:* %s' % m[meal]])
            else:
                # first mensa, then themenpark
                for loc_meals in meals:
                    if len(loc_meals[1]) > 0:
                        lines = [
                            '\n%s %s %s:\n' % (Emoji.FORK_AND_KNIFE, loc_meals[0].nice_name, date.strftime('%Y-%m-%d'))]

                        ordered_meals = self._sort_meals(loc_meals[0], loc_meals[1])
                        for i in ordered_meals.items():
                            lines.append('*%s:* %s' % i[1])
                        msg_text += '\n'.join(lines) + '\n'
                    else:
                        msg_text += 'No meals found for %s at %s %s\n' % (
                            date.strftime('%Y-%m-%d'), loc_meals[0].nice_name, Emoji.LOUDLY_CRYING_FACE)

            self.sendMessage(chat_id=chat_id, text=msg_text,
                            parse_mode=ParseMode.MARKDOWN,
                            disable_web_page_preview=True)
        except (ValueError, ArgumentError):
            self.sendMessage(chat_id, text='Usage: /mensa [<date>]')

    @staticmethod
    def error(bot, update, err, **kwargs):
        """ Error handling """
        bot.logger.error("An error (%s) occurred: %s", type(err), err.message)

    @staticmethod
    def unknown(bot, update):
        bot.sendMessage(chat_id=update.message.chat.id, text='Sorry, I do not understand that command.\n')
        bot.bot_help(update)
        bot.logger.info('Recieved unknown command: %s', update.message)




