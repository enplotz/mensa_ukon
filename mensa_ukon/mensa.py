#! /usr/bin/env python

"""Mensa class"""
import logging
import re
import pendulum

from collections import namedtuple
from functools import lru_cache
from requests_html import HTMLSession

from mensa_ukon.emojize import Emojize
from mensa_ukon.constants import Language, CANTEENS
from mensa_ukon.settings import TIMEZONE

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


# Location, dict
Plan = namedtuple('Plan', ['location', 'meals'])

class MensaBase(object):

    def __init__(self, location):
        """Constructor."""
        self.location = location

    def retrieve(self, datum=None, language=None, meals=None, emojize=None):
        # overwrite this
        # TODO how to make design more pythonic?
        # In Java terms: abstract class -> two implementation classes
        pass

    @staticmethod
    def _normalize_key(k: str) -> str:
        return None if not k else k.strip().lower().replace(' ', '_')

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
        return MensaBase._normalize_orthography(MensaBase._normalize_whitespace(MensaBase._strip_additives(text.strip())))

    @staticmethod
    def _text_replace(text: str) -> str:
        return re.sub('Züricher', "Zürcher", text)

class Mensa(MensaBase):

    def __init__(self, location):
        logger.debug(f'Canteen is {location}')
        location = CANTEENS[location]
        self._endpoint = 'https://www.seezeit.com/essen/speiseplaene/{}/'.format(location.key)
        # friggin english endpoint is totally different :(
        self._endpoint_en = 'https://www.seezeit.com/en/food/menus/{}/'.format(location.key.replace('mensa-', '') + '-canteen')
        super(Mensa, self).__init__(location)

    # TODO investigate if server sends some content change code
    # TODO time-bounded eviction
    @lru_cache(maxsize=2)
    def _do_request(self, is_de = True):
        with HTMLSession() as session:
            url = self._endpoint if is_de else self._endpoint_en
            resp = session.get(url)
            code = resp.status_code
            if code != 200:
                logger.warning(f'Non-200 status: {code}')
            return resp.html

    # how to specify tz for pendulum.today?
    def retrieve(self, datum=pendulum.today(tz=TIMEZONE), language=Language.de, filter_meal=None, emojize=True) -> Plan:
        # TODO report invalid date, e.g. /mensa 2018-02-29 to ValueError (invalid date for month)

        logger.debug(f'Retrieving meals for {datum} from {self.location}')

        html = self._do_request(is_de = language == Language.de)

        # Meals are shown for two weeks (with a crippled, non-standard date format >.< )
        # current and next week
        # [Mo-Fr] [Mo-Fr]
        # todays tab is annotated by class "heute"
        # Format: ?? DD.MM.

        # Let's try this without parsing the stupid date format that has no year
        # TODO FIXME server seems to have a timezone with +0 difference :(
        today = pendulum.today(tz=TIMEZONE)

        date_tabs = html.xpath('//div[@class="tx-speiseplan"]/div[@class="tabs"]/a')
        # figure out which index corresponds to today's date
        today_num = 0
        today_kw = 'heute' if language == Language.de else 'today'
        for tab_num, tab in enumerate(date_tabs):
            if today_kw in tab.attrs['class']:
                today_num = tab_num
                break

        # map idx from tabs to real date
        # INVARIANT: today's date is always in the first 5 tabs, i.e. index 0-4
        dates = []
        for tab_num, tab in enumerate(date_tabs):
            # next week gets 2 days from the weekend
            offset = tab_num - today_num + (0 if tab_num <= 4 else 2)
            date = today.add(days=offset)
            dates.append(date)

        tabs = html.xpath('//div[starts-with(@id, "tab")]')
        filter_meal_key = self._normalize_key(filter_meal)
        # find correct date/tab to extract meals from
        correct_tab = None
        for offset, d in enumerate(dates):
            if d == datum:
                logger.debug(f'Found specified datum {d} at {offset}')
                correct_tab = tabs[offset]
                break

        if not correct_tab:
            # no meals for specified day
            logger.debug('No meal for specified day')
            return Plan(self.location, None)

        logger.debug('Meals for date {}'.format(datum))
        meals = {}

        #plan_elem = correct_tab.xpath('//div[starts-with(@class, "speiseplanTagKat")]')
        plan_elem = correct_tab.find('.speiseplanTagKat')

        for meal in plan_elem:
            title = meal.find(".title", first=True).text
            category = meal.find(".category", first=True).text
            logger.debug(f'  {category}\n\t{title}\n')

            meal_type = category.strip()
            norm_meal_type = self._normalize_key(meal_type)
            if not filter_meal or norm_meal_type in filter_meal_key:
                clean_text = self._text_replace(self._clean_text(title.strip()))
                meals[norm_meal_type] = (meal_type, Emojize.replace(clean_text) if emojize else clean_text)

        # e.g. Plan( location = ..., meals = { bio = ("Bioessen", "Title" ), stamm = ("Stammessen", "Title") }
        return Plan(self.location, meals)
