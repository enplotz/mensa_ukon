#! /usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from collections import namedtuple

import pendulum
import telegram
from telegram import ChatAction, Update
from telegram.error import (ChatMigrated, Conflict, InvalidToken, NetworkError,
                            TelegramError, TimedOut, Unauthorized)
from telegram.ext import (CallbackContext, CommandHandler, Filters,
                          MessageHandler, Updater)

from mensa_ukon import Mensa, settings
from mensa_ukon.constants import Language
from mensa_ukon.emojize import Emojize


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


class MensaBot(telegram.Bot):


    CMDShortcut = namedtuple('CMDShortcut', ['command', 'meal', 'location', 'short_help'])
    SHORTCUTS = [
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

    GREETING = ('🤖Hello, human!\n'
                'I am a bot to retrieve the culinary offerings of Uni Konstanz\' canteen. '
                'I can understand several date formats like \'today\', \'tomorrow\' and ones '
                'formatted like \'YYYY-MM-DD\'.\n\n'
                'The /news command will show you what new stuff I can do!'
            )

    INTRO_HELP = '🤖 It looks like you may need help.\n'
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
        self.logger.debug('Setting up bot...')

        # remember commands for easy help text
        self.my_commands = []
        self.mensa = Mensa(location=settings.CANTEEN)

        self.updater = Updater(settings.TOKEN, workers=settings.WORKERS, use_context=True)
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

        self._add_bot_command('mensa', lambda update, context: self._mensa_plan(update, args=context.args),
                              self.DATE_HELP, pass_args=True)
        self._add_bot_command('mensaEN', lambda update, context: self._mensa_plan(update, language=Language.EN, args=context.args),
                              self.DATE_HELP, pass_args=True)

        # shortcuts to direct offers for configured locations
        for cmd in self.SHORTCUTS:
            if settings.CANTEEN == cmd.location:
                self._add_meal_command(cmd)

        self.dp.add_error_handler(MensaBot._error)
        self.dp.add_handler(MessageHandler(Filters.command, self._unknown_command))

    @staticmethod
    def _error(update: Update, context: CallbackContext):
        """ Error handling."""
        try:
            raise context.error
        except TimedOut:
            context.bot.logger.error("Request to Telegram API took too long: %s", context.error)
            update.effective_message.reply_text('Unfortunately, it seems that Telegram is not responding to me :(', quote=True)
        except NetworkError:
            context.bot.logger.error("Error communicating with Telegram API: %s", context.error)
        except Conflict:
            context.bot.logger.error("Long poll/webhook conflict: %s", context.error)
        except InvalidToken:
            context.bot.logger.error("Token is no longer valid: %s", context.error)
        except ChatMigrated:
            context.bot.logger.error("Chat was migrated: %s", context.error)
        except TelegramError:
            context.bot.logger.error("There was an error while communicating with Telegram: %s", context.error)
            update.effective_message.reply_text('Unfortunately, there was an error communicating with Telegram :(', quote=True)
        except Unauthorized:
            # I guess since we are not keeping track of conversations ourselves, we cannot remove
            # the bot from the conversation list?
            context.bot.logger.error("Bot has insufficient rights: %s", context.error)
            update.effective_message.reply_text('Unfortunately, Telegram does not allow me to do that!', quote=True)
        except Exception as e:
            context.bot.logger.error("Some other error (%s) occurred: %s", type(e), e)
            update.effective_message.reply_text('Unfortunately, there was an error 😵. Please try again later or file an Issue on GitHub.', quote=True)
            raise e


    def _unknown_command(self, update: Update, context: CallbackContext):
        self.logger.info('Received unknown command: %s', update.effective_message.text)
        update.effective_message.reply_text('Sorry, I do not understand this command.', quote=True)


    def run(self):
        if settings.USE_POLLING:
            self.logger.info('Bot running with polling enabled.')
            self.updater.start_polling()
            self.updater.idle()
        else:
            if settings.IS_HEROKU:
                # https://github.com/python-telegram-bot/python-telegram-bot/wiki/Webhooks#heroku
                webhook_url = f'https://{settings.HEROKU_APP_NAME}.herokuapp.com/{settings.TOKEN}'
                self.updater.start_webhook(listen=settings.LISTEN_IP, port=settings.LISTEN_PORT, url_path=settings.TOKEN, webhook_url=webhook_url)
                # self.setWebhook(url=webhook_url)
            else:
                webhook_url = f'https://{settings.URL}:{settings.LISTEN_PORT}/{settings.TOKEN}'
                self.updater.start_webhook(
                    listen=settings.LISTEN_IP,
                    port=settings.LISTEN_PORT,
                    url_path=settings.TOKEN,
                    cert=settings.CERT,
                    key=settings.CERT_KEY,
                    webhook_url=webhook_url)
                self.setWebhook(url=webhook_url, certificate=open(settings.CERT, 'rb'))
                # You can also set the webhook yourself (via cURL) or delete it sending an empty url.
                # Note that for self-signed certificates, you also have to send the .pem certificate file
                # to the Telegram API.
                # Actually start our bot
            # don't leak token into logs
            self.logger.info('Bot running with webhook on %s', webhook_url.replace(settings.TOKEN, '***TOKEN_OMITTED***'))
            self.updater.idle()


    def _add_bot_command(self, command_text, command, help_info, pass_args=False):
        # the german auto-correct tends to capitalize the first word after the slash...
        # so we will add both variants internally bot not report them in the help menu
        # command = lambda bot, update, args: command(update, args=args)
        for c_text in [command_text, command_text.capitalize()]:
            self.dp.add_handler(CommandHandler(c_text, command, run_async=True, pass_args=pass_args))
        self.my_commands.append((command_text, help_info))


    def _add_meal_command(self, cmd_shortcut):
        for s in [cmd_shortcut.command, cmd_shortcut.command.capitalize()]:
            self.dp.add_handler(CommandHandler(s, lambda update, context: self._mensa_plan(update, filter_meal=cmd_shortcut.meal, args=context.args), run_async=True))


    @staticmethod
    def _format_date_relative(date, language=Language.DE):
        is_de = language == Language.DE
        today = pendulum.today(tz=settings.TIMEZONE)
        if date == today:
            return 'Heute' if is_de else 'Today'
        elif date.diff(today).in_days() == 1:
            return 'Morgen' if is_de else 'Tomorrow'
        else:
            loc = 'de' if is_de else 'en'
            return date.diff_for_humans(locale=loc)


    @staticmethod
    def _parse_datum(date_string : str, fallback_func=None) -> pendulum.date:
        d = date_string.lower().strip()
        if d in ['today', 'heute']:
            return pendulum.today(tz=settings.TIMEZONE)
        if d in ['tomorrow', 'morgen']:
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


    def _news(self, update: Update, context: CallbackContext):
        """Prints news for the bot."""
        self.logger.debug('Received /start command')
        update.effective_message.reply_markdown(text=self._news_content)


    def _print_commands(self):
        # we want to print both commands for the bot, as well as commands to get meals
        return "\n".join(map(lambda c: '/' + c[0] + ' ' + c[1], self.my_commands)) \
               + '\n' \
               + "\n".join(map(lambda c: '/' + c.command + ' ' + c.short_help, [short for short in MensaBot.SHORTCUTS if settings.CANTEEN == short.location]))


    def _start(self, update: Update, context: CallbackContext):
        self.logger.debug('Received /start command')
        update.effective_message.reply_markdown(
            text=self.GREETING + '\n\n' + self.INTRO_COMMANDS + self._print_commands() + self.EXAMPLES,
            disable_web_page_preview=True
            )


    def _bot_help(self, update: Update, context: CallbackContext):
        """Prints help text"""
        self.logger.debug('Received /help command')
        update.effective_message.reply_markdown(
            text=MensaBot.INTRO_HELP + '\n' + MensaBot.INTRO_COMMANDS + self._print_commands() + MensaBot.EXAMPLES, 
            disable_web_page_preview=True
            )


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

    def _msg_text_for_meals(self, date, plan, language=Language.DE):
        msg_text = f'🍴 {plan.location.nice_name} – 🕛 *' + MensaBot._format_date_relative(date, language).title() + '*\n\n'
        self.logger.debug('Preparing menu...')
        if plan.meals is not None:
            msg_text += ''.join(['*{0}{1}:* {2}\n'.format(l[0], Emojize.as_str(l[2]), l[1]) for l in plan.meals.values()]) + '\n'
        else:
            # TODO full localization
            date_str = date.format('dddd, DD. MMMM YYYY', locale=language.name)
            msg_text += ('Keine Speisen gefunden für' if language == Language.DE else 'No meals found for') \
                        + f' {date_str} 😭\n'
        return msg_text


    def _mensa_plan(self, update, language=Language.DE, filter_meal=None, args=None):
        # TODO simplify method...
        # /mensa [today|tomorrow|date]
        # currently, we only support dates* in the args parameter

        if len(args) > 1:
            update.effective_message.reply_markdown(
                text='Give me a single date to fetch meals for.',
                disable_web_page_preview=True
            )
            return

        self.sendChatAction(chat_id=update.effective_message.chat_id, action=ChatAction.TYPING)

        if len(args) > 0:
            self.logger.debug(args)
            try:
                date = MensaBot._parse_datum(args[0])
            except pendulum.parsing.exceptions.ParserError as pe:
                self.logger.info('Got unknown date or date format: %s', args[0])
                update.effective_message.reply_markdown(
                    text='Sorry, I do not understand the date you gave me: {}'.format(args[0]),
                    disable_web_page_preview=True
                )
                return
        else:
            date = pendulum.today(settings.TIMEZONE)

        try:
            if filter_meal:
                self.logger.debug('Filter for: %s', filter_meal)

            # experimental feature: overwrite language when given english instructions
            if len(args) > 0:
                date_string = args[0].lower()
                if date_string in ['today', 'tomorrow']:
                    language = Language.EN

            # dict of meals
            plan = self.mensa.retrieve(date, language=language, filter_meal=filter_meal)
            self.logger.debug('Retrieved meal plan.')

            msg_text = self._msg_text_for_meals(date, plan, language=language)
            try:
                update.effective_message.reply_markdown(
                    text=msg_text,
                    disable_web_page_preview=True
                )
            except Exception as e:
                self.logger.exception(e)
        except (ValueError, ArgumentError) as e:
            update.effective_message.reply_markdown(
                text='\n*Usage:* /mensa [<date>]\ne.g. /mensa 2017-01-01',
                disable_web_page_preview=True
            )
        except NoMealError as nme:
            self.logger.error(nme.message)
            update.effective_message.reply_markdown(
                text=nme.message,
                disable_web_page_preview=True
            )
