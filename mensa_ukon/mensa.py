#! /usr/bin/env python

"""Mensa class"""
import logging
import re
import pendulum

from collections import namedtuple, OrderedDict
from requests_html import HTMLSession
from bs4 import BeautifulSoup

from cachecontrol import CacheControlAdapter
from cachecontrol.heuristics import ExpiresAfter

from mensa_ukon.emojize import Emojize
from mensa_ukon.constants import Language, CANTEENS
from mensa_ukon.settings import TIMEZONE

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())



# Location, dict
Plan = namedtuple('Plan', ['location', 'meals'])

class MensaBase(object):

    def __init__(self, endpoints, location):
        """Constructor."""
        self.location = location
        # dict of language specific endpoints
        # { Language : url-string }
        self.endpoints = endpoints

        adapter = CacheControlAdapter(heuristic=ExpiresAfter(days=1))
        self.session = HTMLSession()
        self.session.mount('https://', adapter)

    def retrieve(self, datum=None, language=None, meals=None, emojize=None) -> Plan:
        # overwrite this
        # TODO how to make design more pythonic?
        # In Java terms: abstract class -> two implementation classes
        pass

    # Helper method to make a language-specific request
    def do_request(self, language=Language.de):
        resp = self.session.get(self.endpoints[language])
        code = resp.status_code
        if code != 200:
            logger.warning(f'Non-200 status: {code}')
        return resp.html

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
        logger.info(f'Canteen is {location}')
        location = CANTEENS[location]

        endpoints = { Language.de : 'https://www.seezeit.com/essen/speiseplaene/{}/'.format(location.key),
                      Language.en : 'https://www.seezeit.com/en/food/menus/{}/'.format(location.key.replace('mensa-', '') + '-canteen')
                    }

        super(Mensa, self).__init__(endpoints, location)

    @staticmethod
    def _get_requested_day_index(date_tabs, datum, language):
        locale =  'de' if language == Language.de else 'en'
        datum_fmt = datum.format('%a. %d.%m.', locale=locale)
        for i, t in enumerate(date_tabs):
            text = str(t.full_text).strip()
            if text == datum_fmt:
                return i
        return None

    def _retrieve_plan(self, html=None, language=Language.de, emojize=False) -> [OrderedDict]:
        if not html:
            html = self.do_request(language).html

        soup = BeautifulSoup(html, 'html5lib')

        tabs = soup.find_all('div', id=re.compile("^tab\d+"))
        num_tabs = len(tabs)
        if num_tabs != 10:
            logger.error(f"Could not find 10 tabs: {num_tabs}")

        days = []
        for t in tabs:
            meals = t.find_all('div', class_='speiseplanTagKat')
            day = OrderedDict()
            for m in meals:
                title = MensaBase._strip_additives(m.find('div', class_='title').text)
                category = m.find('div', class_='category').text

                normalized_category = self._normalize_key(category)
                clean_text = self._text_replace(self._clean_text(title.strip()))
                day[normalized_category] = (category, Emojize.replace(clean_text) if emojize else clean_text)

            days.append(day)
        return days

    # how to specify tz for pendulum.today?
    def _retrieve(self, html, datum, language, filter_meal, emojize) -> Plan:
        # TODO report invalid date, e.g. /mensa 2018-02-29 to ValueError (invalid date for month)

        logger.debug(f'Retrieving meals for {datum} from {self.location}')

        # Meals are shown for two weeks
        # current and next week
        # [Mo-Fr] [Mo-Fr]

        # TODO convert to BS4
        date_tabs = html.xpath('//div[@class="tx-speiseplan"]/div[@class="tabs"]/a')

        day_idx = self._get_requested_day_index(date_tabs, datum, language)

        if day_idx is None:
            # no meals for specified day
            logger.debug('No meal for specified day')
            return Plan(self.location, None)

        logger.debug('Meals for date {}'.format(datum))

        meals = self._retrieve_plan(html=html.html, emojize=emojize)[day_idx]

        if filter_meal:
            filter_meal_key = self._normalize_key(filter_meal)
            meals = { k:v for k,v in  meals.items() if k == filter_meal_key }

        return Plan(self.location, meals)

    def retrieve(self, datum=None, language=Language.de, filter_meal=None, emojize=True) -> Plan:
        if not datum:
            datum = pendulum.today(tz=TIMEZONE)
        html = self.do_request(language)
        return self._retrieve(html, datum, language, filter_meal, emojize)
