#! /usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from collections import namedtuple

import pendulum
import telegram
from pendulum.parsing.exceptions import ParserError
from telegram import ChatAction
from telegram import ParseMode
from telegram.error import (Unauthorized, BadRequest, TimedOut, NetworkError, ChatMigrated, TelegramError)
from telegram.ext import CommandHandler
from telegram.ext import Filters
from telegram.ext import MessageHandler
from telegram.ext import Updater
from telegram.ext.dispatcher import run_async

from mensa_ukon import Mensa
from mensa_ukon import settings
from mensa_ukon.constants import Language


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


class NoMealError(BotError):
    def __init__(self, meal: str):
        super(NoMealError, self).__init__('No meal found for \'{}\'.'.format(meal.capitalize()))


class BotConfigurationError(BotError):
    def __init__(self, msg: str):
        super(BotConfigurationError, self).__init__('Error configuring bot: \'{}\'.'.format(msg))


@run_async
def msg_async(bot, *args, **kwargs):
    kwargs['timeout'] = 2
    try:
        bot.sendMessage(*args, **kwargs)
    except Exception as e:
        exc(bot, e)


def exc(bot, ex):
    """Exception handling."""
    # TODO use logger from MensaBot instance and not Telegram bot instance
    bot.logger.exception(ex)


class MensaBot(telegram.Bot):

    CMDShortcut = namedtuple('CMDShortcut', ['command', 'meal', 'location', 'short_help'])
    SHORTCUTS = [
        CMDShortcut('stamm', 'stammessen', 'giessberg', 'Show main meal'),
        CMDShortcut('wahl', 'wahlessen', 'giessberg', 'Show alternative meal'),
        CMDShortcut('vegi', 'vegetarisch', 'giessberg', 'Show vegetarian meal'),
        # Upcoming 3 meals
        CMDShortcut('teller', 'seezeit-teller', 'giessberg', 'Show Seezeit-Teller'),
        CMDShortcut('kombi', 'kombinierbar', 'giessberg', 'Show KombinierBar'),
        CMDShortcut('hinweg', 'hin&weg', 'giessberg', 'Show hin&weg'),
        CMDShortcut('eintopf', 'eintopf', 'giessberg', 'Show stew'),
        CMDShortcut('pasta', 'Al stuDente', 'giessberg', 'Show Pasta Bar'),
        CMDShortcut('abendessen', 'abendessen', 'giessberg', 'Show dinner'),
        CMDShortcut('grill', 'grill', 'giessberg', 'Show grill'),
        CMDShortcut('bio', 'bioessen', 'giessberg', 'Show bio'),
        CMDShortcut('wok', 'wok', 'giessberg', 'Show wok'),
    ]

    GREETING = 'Hello, human!\n' \
               'I am a bot to retrieve the culinary offerings of Uni Konstanz\' canteen. ' \
               'I can understand several date formats like \'today\', \'tomorrow\' and ones ' \
               'formatted like \'YYYY-MM-DD\'.\n' \
               'Please forgive me if I sometimes do not work, you see, ' \
               'I\'m quite new and still adjusting to this world :).\n\n' \
               'The /news command will show you what new stuff I can do!\n\n'

    INTRO_HELP = 'It looks like you may need help.\n'
    INTRO_COMMANDS = 'Here are my *commands*:\n'

    DATE_HELP = '\[<date>] get what offerings are waiting for you at the specified date ' \
                'formatted like \'YYYY-MM-DD\'.'

    EXAMPLES = ' \n\n' \
               '*Examples:*\n' \
               '/mensa tomorrow\n' \
               '/mensa 2016-02-24\n'

    @staticmethod
    def _token():
        if settings.TOKEN is None:
            raise BotConfigurationError('Missing bot token.')
        return settings.TOKEN

    def __init__(self):
        # TODO fix settings module needing import before MensaBot init...
        super(MensaBot, self).__init__(MensaBot._token())
        self.logger = logging.getLogger(__name__)
        self.logger.debug('Setting up Bot...')

        self.commands = []
        self.mensa = Mensa(location=settings.CANTEEN)


        self.updater = Updater(settings.TOKEN, workers=settings.WORKERS)
        self.dp = self.updater.dispatcher

        #self.dp.add_handler(CommandHandler('inline', self._inline_test))
        #self.dp.add_handler(CallbackQueryHandler(self._inline_selected))

        # self.dp.add_handler(InlineQueryHandler(self._inlinequery))

        # Custom command handlers
        self._add_bot_command('start', self._start, 'start bot')
        self._add_bot_command('help', self._bot_help, 'display help message')

        # A missing news file should not bring the bot to a crash
        # so if there are no news, the command is not present.
        # This might also happen if we run a script directly, so that the working directory is not
        # as expected.
        try:
            with open('news.md') as f:
                self._news_content = f.read()
                self._add_bot_command('news', self._news, 'display bot news')
        except IOError as e:
            self.logger.warning(e)

        self._add_bot_command('mensa', lambda bot, update, args: self._mensa_plan(update, args=args),
                              self.DATE_HELP, pass_args=True)
        self._add_bot_command('mensaEN', lambda bot, update, args: self._mensa_plan(update, language=Language.en, args=args),
                              self.DATE_HELP, pass_args=True)

        # shortcuts to direct offers for configured locations
        for cmd in self.SHORTCUTS:
            if settings.CANTEEN == cmd.location:
                self._add_meal_command(cmd)

        self.dp.add_error_handler(MensaBot._error)
        self.dp.add_handler(MessageHandler(Filters.command, self._unknown_command))

    @staticmethod
    def _error(bot, update, error):
        """ Error handling."""
        bot.logger.error("An error (%s) occurred: %s", type(error), error.message)
        try:
            raise error
        except Unauthorized:
            # I guess since we are not keeping track of conversations ourselves, we cannot remove
            # the bot from the conversation list?
            pass
        # TODO handle remaining errors...
        except BadRequest:
            pass
        except TimedOut:
            pass
        except NetworkError:
            pass
        except ChatMigrated as e:
            pass
        except TelegramError:
            pass

    def _unknown_command(self, bot, update):
        bot.logger.info('Received unknown command: %s', update.message)
        msg_async(bot=bot, chat_id=update.message.chat.id, text='Sorry, I do not understand that command.\n')
        self._bot_help(bot, update)

    def _msg_async(self, chat_id, text):
        msg_async(bot=self, chat_id=chat_id, text=text,
                                          parse_mode=ParseMode.MARKDOWN,
                                          disable_web_page_preview=True)
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
            self.dp.add_handler(CommandHandler(s, lambda bot, update, args: self._mensa_plan(update, filter_meal=cmd_shortcut.meal, args=args),
                                               pass_args=True))

    @staticmethod
    def _format_date_relative(date, language=Language.de):
        is_de = language == Language.de
        if date.is_today():
            return 'Heute' if is_de else 'Today'
        elif date.is_tomorrow():
            return 'Morgen' if is_de else 'Today'
        else:
            loc = 'de' if is_de else 'en'
            return date.diff_for_humans(locale=loc)

    # except pendulum.parsing.exceptions.ParserError as e:
    @staticmethod
    def _parse_datum(date_string : str, fallback_func=None) -> pendulum.date:
        if date_string in ['today', 'heute', 'Today', 'Heute']:
            return pendulum.today(tz=settings.TIMEZONE)
        if date_string in ['tomorrow', 'morgen', 'Tomorrow', 'Morgen']:
            return pendulum.tomorrow(tz=settings.TIMEZONE)

        # the fallback function is only used when it's defined and parsing fails
        # its resulting value will still be "validated" later
        try:
            date = pendulum.parse(date_string, tz=settings.TIMEZONE)
        except pendulum.parsing.exceptions.ParserError as e:
            if fallback_func:
                date = fallback_func(tz=settings.TIMEZONE)
            else:
                raise e

        # we currently do not support lookup for past dates in bot query parameters
        today = pendulum.today(tz=settings.TIMEZONE)
        if today > date:
            raise pendulum.parsing.exceptions.ParserError('No past dates allowed.')
        return date

    @staticmethod
    def _str_for_single_meal(bot, meals: dict, meal: str) -> str:
        try:
            return '*{0}:* {1}'.format(*meals[Mensa._normalize_key(meal)])
        except KeyError:
            # meal not present
            bot.logger.error(meal)
            bot.logger.error(meals)
            pass
        raise NoMealError(meal)

    def _news(self, bot, update):
        """Prints news for the bot."""
        chat_id = update.message.chat.id
        msg_async(bot=bot, chat_id=chat_id, text=self._news_content, parse_mode=ParseMode.MARKDOWN)

    def _print_commands(self):
        # we want to print both commands for the bot, as well as commands to get meals
        return "\n".join(map(lambda c: '/' + c[0] + ' ' + c[1], self.commands)) \
               + '\n' \
               + "\n".join(map(lambda c: '/' + c.command + ' ' + c.short_help, [short for short in MensaBot.SHORTCUTS if settings.CANTEEN == short.location]))

    def _start(self, bot, update):
        chat_id = update.message.chat.id
        bot.sendMessage(chat_id=chat_id, text=self.GREETING + '\n' + self.INTRO_COMMANDS + self._print_commands() + self.EXAMPLES,
                        parse_mode=ParseMode.MARKDOWN,
                        disable_web_page_preview=True)

    def _bot_help(self, bot, update):
        """Prints help text"""
        chat_id = update.message.chat.id
        msg_async(bot=bot, chat_id=chat_id,
                        text=MensaBot.INTRO_HELP + MensaBot.INTRO_COMMANDS + self._print_commands() + MensaBot.EXAMPLES,
                        parse_mode=ParseMode.MARKDOWN,
                        disable_web_page_preview=True)

    # TODO custom keyboard with emoji as meals

    # def _inline_test(self, bot, update):
    #  keyboard = [[InlineKeyboardButton("Stamm", callback_data='stamm'),
    #  InlineKeyboardButton("Wahl", callback_data='wahl')],
    # [InlineKeyboardButton("Bio", callback_data='bio')]]
    #
    #     reply_markup = InlineKeyboardMarkup(keyboard)
    #     update.message.reply_text('Please choose:', reply_markup=reply_markup)
    #
    # def _inline_selected(self, bot, update):
    #     query = update.callback_query
    #     bot.editMessageText(text='Selected option: {}'.format(query.data),
    #                         chat_id=query.message.chat_id,
    #                         message_id=query.message.message_id)

    # def _inlinequery(self, bot, update):
    #     query = update.inline_query.query
    #     self.logger.debug('Got query: %s', query)
    #
    #     # TODO assume for now that the query contains only the date string
    #     # later on, we could try to intelligently parse the query and derive intents
    #     # e.g., certain meal types (meat, vegan, vegetarian) at certain dates, or a specific meal (e.g., stammessen)
    #     try:
    #         date = self._parse_datum(query, fallback_func=pendulum.today)
    #     except pendulum.parsing.exceptions.ParserError:
    #         date = pendulum.today(settings.TIMEZONE)
    #
    #     meals = self.mensa.retrieve(date, Language.de)
    #
    #     results = list()
    #     for location in meals:
    #         for meal in location[1].items():
    #             meal = meal[1]
    #
    #             # thumb_url='https://www.seezeit.com/fileadmin/template/images/icons/speiseplan/Veg.png'
    #             results.append(InlineQueryResultArticle(
    #                 id=uuid4(),
    #                 title=meal[0],
    #                 description=meal[1],
    #                 input_message_content=InputTextMessageContent(
    #                     '🕛 *{}*\n*{}*: {}'.format(
    #                                                MensaBot._format_date_relative(date).title(), meal[0], meal[1]),
    #                     parse_mode=ParseMode.MARKDOWN)))
    #
    #     if len(results) > 0:
    #         results.insert(0, InlineQueryResultArticle(
    #             id=uuid4(),
    #             title='Return the whole list of meals',
    #             input_message_content=InputTextMessageContent(self._msg_text_for_meals(date, meals),
    #                                                           parse_mode=ParseMode.MARKDOWN)
    #         ))
    #     else:
    #         results.append(InlineQueryResultArticle(
    #             id=uuid4(),
    #             title='😭 No meals',
    #             description='There are no meals for specified date: {}.'.format(MensaBot._format_date_relative(date).title()),
    #             input_message_content=InputTextMessageContent(self._msg_text_for_meals(date, meals),
    #                                                           parse_mode=ParseMode.MARKDOWN)
    #         ))
    #     update.inline_query.answer(results)

    def _msg_text_for_meals(self, date, plan, language=Language.de):
        msg_text = f'🍴 {plan.location.nice_name} – 🕛 *' + MensaBot._format_date_relative(date, language).title() + '*\n\n'

        if plan.meals:
            msg_text += ''.join(['*{0}:* {1}\n'.format(l[0], l[1]) for l in plan.meals.values()]) + '\n'
        else:
            date_str = date.format('%A, %d. %B %Y', locale='de')
            # TODO full localization
            msg_text += ('Keine Speisen gefunden für' if language == Language.de else 'No meals found for') + f' {date_str} 😭\n'
        return msg_text

    def _mensa_plan(self, update, language=Language.de, filter_meal=None, args=None):
        # TODO simplify method...
        # /mensa [today|tomorrow|date]
        # currently, we only support dates* in the args parameter
        chat_id = update.message.chat.id
        if len(args) > 1:
            self._msg_async(chat_id, text='Give me a single date to fetch meals for.')
            return

        self.sendChatAction(chat_id=chat_id, action=ChatAction.TYPING)

        if len(args) > 0:
            try:
                date = MensaBot._parse_datum(args[0])
            except pendulum.parsing.exceptions.ParserError:
                self.logger.info('Got unknown date format: %s', args[0])
                self._msg_async(chat_id=chat_id, text='Sorry, I do not understand the date you gave me: {}'.format(args[0]))
                return
        else:
            date = pendulum.today(settings.TIMEZONE)

        try:
            if filter_meal:
                self.logger.debug('Filter for: %s', filter_meal)
            # dict of meals
            plan = self.mensa.retrieve(date, language=language, filter_meal=filter_meal)

            msg_text = self._msg_text_for_meals(date, plan, language=language)
            try:
                msg_async(bot=self, chat_id=chat_id, text=msg_text,
                                parse_mode=ParseMode.MARKDOWN,
                                disable_web_page_preview=True)
            except Exception as e:
                exc(self, e)
        except (ValueError, ArgumentError) as e:
            self._msg_async(chat_id=chat_id, text='\n*Usage:* /mensa [<date>]\ne.g. /mensa 2017-01-01')
            exc(self, e)
        except NoMealError as nme:
            self.logger.error(nme.message)
            msg_async(bot=self, chat_id=chat_id, text=nme.message)
