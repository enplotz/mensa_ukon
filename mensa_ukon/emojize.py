#! /usr/bin/env python

import re
import logging

logger = logging.getLogger(__name__)

class Emoji(object):
    """Hold the Emoji we use."""
    COW = u'\U0001F42E'
    PIG = u'\U0001F437'
    FISH = u'\U0001F41F'
    CHICKEN = u'\U0001F414'
    CHEESE = u'\U0001F9C0'
    SEEDLING = u'\U0001F331'
    SHEEP = u'\U0001F411'


class Emojize:

    IN_PARENS = re.compile('\(([^)]*?)(?:,([^)]*?))?\)')
    # List of possible meals, comma separated.
    TOKENS = [
        (Emoji.COW, re.compile('[RCKB]')),
        (Emoji.PIG, re.compile('Sch|P')),
        (Emoji.FISH, re.compile('F')),
        (Emoji.CHICKEN, re.compile('G')),
        (Emoji.SEEDLING, re.compile('Vegan')),
        (Emoji.CHEESE, re.compile('Veg')),
        (Emoji.SHEEP, re.compile('L')),
    ]

    @classmethod
    def _repl_all_emoji(cls, match_object) -> str:
        """
        Used to replace shorthands with emoji
        :param match_object: match object from a regex match
        :return:
        """
        emoji = []
        for group in match_object.groups():
            if group:
                for e, regex in cls.TOKENS:
                    if regex.fullmatch(group.strip()):
                        emoji.append(e)
                        break
                else:
                    # we have to put back our extracted string, which we could not
                    # match with an Emoji character
                    emoji.append(group)
        return '(' + ", ".join(emoji) + ')'

    @classmethod
    def replace(cls, text: str) -> str:
        """Replaces shorthands of meal types with emojis.
        :param text: description of a meal
        :return: description with substituted text shorthands as emoji characters
        """
        logger.debug('Replacing text %s', text)
        return cls.IN_PARENS.sub(cls._repl_all_emoji, text)

