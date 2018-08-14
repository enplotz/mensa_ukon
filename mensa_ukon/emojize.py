# -*- coding: utf-8 -*-
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

    # List of possible meals, comma separated.
    TOKENS = [
        (Emoji.COW, re.compile('[RCKB]')),
        (Emoji.PIG, re.compile('Sch|P')),
        (Emoji.FISH, re.compile('F')),
        (Emoji.CHICKEN, re.compile('G|Po')),
        (Emoji.SEEDLING, re.compile('Vegan')),
        (Emoji.CHEESE, re.compile('Veg')),
        (Emoji.SHEEP, re.compile('L')),
    ]

    @classmethod
    def replace_type(cls, type: str) -> str:
        for e, regex in cls.TOKENS:
            if regex.fullmatch(type):
                return e
        return ''

    @staticmethod
    def as_str(emojis):
        if len(emojis) == 0:
            return ''
        return ' ' + ' '.join(emojis)