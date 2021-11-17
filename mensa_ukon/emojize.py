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
    GAME = u'\U0001F98C'
    STAR = u'\U00002B50'


class Emojize:

    # List of possible meals, comma separated.
    # The new mensa website uses simple CSS classes to display icons
    # So we do not need regexs anymore :)
    TOKENS = [
        (Emoji.CHEESE, 'Veg'),
        (Emoji.SEEDLING, 'Vegan'),
        (Emoji.PIG, 'Sch'),
        (Emoji.COW, 'R'),
        (Emoji.CHICKEN, 'G'),
        (Emoji.SHEEP, 'L'),
        (Emoji.GAME, 'W'),
        (Emoji.FISH, 'F'),
        (Emoji.STAR, 'B')
    ]

    @classmethod
    def replace_type(cls, type: str) -> str:
        for e, css_class in cls.TOKENS:
            if type is not None and css_class in type:
                return e
        return ''

    @staticmethod
    def as_str(emojis):
        if len(emojis) == 0:
            return ''
        return ' ' + ' '.join(emojis)