#! /usr/bin/env python

"""Mensa class"""
import logging
import re
import urllib.error as error
import urllib.request as request
from functools import lru_cache

import lxml.html
from pendulum import date

from mensa_ukon.emojize import Emojize
from .constants import DEFAULT_CANTEENS, CANTEENS, HEADERS, ENDPOINT, Language

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class Mensa(object):
    """Mensa class providing functionality to access canteen plans"""

    def __init__(self, canteens=DEFAULT_CANTEENS):
        """Constructor."""
        self.canteens = canteens

    @classmethod
    @lru_cache(maxsize=7)
    def _do_request(cls, data):
        # TODO time-bound eviction
        req = request.Request(ENDPOINT, data=data, headers=HEADERS, method='POST')
        with request.urlopen(req) as f:
            return f.read().decode('utf-8')

    @classmethod
    def _make_requests(cls, datum: date, locs: list, lang: str):
        """ Makes requests for the given date in the given language at the specified locations (shortcodes).
        """

        def format_post_data(loc: str, lang: str, datum: date) -> str:
            """Formats POST data according to specified location, language and datum.

            The endpoint is a bit picky, and wants the parameters in exactly the right order, so that does not work:
            return urllib.parse.urlencode({'func': 'make_spl', 'loc' : loc, 'lang': lang, 'date': date})
            Instead we have to build the string ourselves quickly."""
            return 'func=make_spl&loc={0}&lang={1}&date={2}'.format(loc, lang, datum.to_date_string())

        # locs = locs or DEFAULT_CANTEENS
        logger.debug('Requesting for locations: %s', locs)
        locations = [CANTEENS[k] for k in locs]
        rs = {}
        # http = urllib3.PoolManager()
        for loc in locations:
            data = format_post_data(loc.key, lang, datum).encode('ascii')
            try:
                rs[loc.key] = (loc, cls._do_request(data))
            except error.HTTPError as e:
                logger.error(e)
        return rs

    @staticmethod
    def _normalize_key(k: str) -> str:
        return k.strip().lower().replace(' ', '_')

    @staticmethod
    def _strip_additives(text: str) -> str:
        return re.sub('\((\s*(\d+)?[a-z]?[,.]?\s*)+\)', '', text)

    @staticmethod
    def _normalize_whitespace(text: str) -> str:
        return re.sub('\s{2,}', ' ', text)

    @staticmethod
    def _normalize_orthography(text: str) -> str:
        return re.sub('\s,', ',', text)

    @staticmethod
    def _clean_text(text: str) -> str:
        return Mensa._normalize_orthography(Mensa._normalize_whitespace(Mensa._strip_additives(text.strip())))

    @staticmethod
    def _extract_meals(data, filter_meals: list, emojize = True) -> list:
        """Extract meals from responses"""
        canteen_meals = []
        filter_meal_keys = [Mensa._normalize_key(meal) for meal in filter_meals] if filter_meals else []
        for mensa, content in data.values():
            logger.debug('Extracting meals from mensa %s', mensa.key)
            logger.debug('Content\n%s', content)
            doc = lxml.html.fromstring(content)
            rows = doc.cssselect('tr')[::2]
            meals = {}
            for row in rows:
                cols = row.cssselect('td')
                if len(cols) == 2:
                    meal_type = cols[0].text.strip()
                    norm_meal_type = Mensa._normalize_key(meal_type)
                    if not filter_meals or norm_meal_type in filter_meal_keys:
                        clean_text = Mensa._clean_text(cols[1].text.strip())
                        meals[norm_meal_type] = (meal_type, Emojize.replace(clean_text) if emojize else clean_text)
                else:
                    logger.error('Not enough values in column for canteen %s', mensa.key)
            canteen_meals.append((mensa, meals))
        logger.debug(canteen_meals)
        return canteen_meals

    def retrieve(self, datum=date.today, language=Language.de, meals=None, emojize=True):
        if not isinstance(datum, date):
            datum = datum()
        rs = self._make_requests(datum, self.canteens, language)
        return self._extract_meals(rs, filter_meals=meals, emojize=emojize)
