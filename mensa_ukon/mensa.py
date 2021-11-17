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
    def do_request(self, language=Language.DE):
        url = self.endpoints[language.name]
        logger.debug(f'Retrieving url: {url}')
        resp = self.session.get(url)
        code = resp.status_code
        if code != 200:
            logger.warning(f'Non-200 status: {code}')
        logger.debug(f'Status Code: {code}')
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

        endpoints = { Language.DE.name : 'https://www.seezeit.com/essen/speiseplaene/{}/'.format(location.key),
                      Language.EN.name : 'https://www.seezeit.com/en/food/menus/{}/'.format(location.key.replace('mensa-', '') + '-canteen')
                    }

        super(Mensa, self).__init__(endpoints, location)

    @staticmethod
    def _get_requested_day_index(date_tabs, datum, language):
        # Locale is unused until the English website stops using the German date format...
        # TODO: revisit this issue
        # locale =  language
        logger.debug('Datum: %s', datum)

        for locale in [Language.DE, Language.EN]:
            datum_fmt = datum.format(language.date_fmt, locale=locale.name)
            logger.debug('Datum format: %s', datum_fmt)
            for i, t in enumerate(date_tabs):
                text = str(t.full_text).strip()
                if text == datum_fmt:
                    return i
        logger.debug('Day not found.')

        return None

    # TODO: remove emojise param
    def _retrieve_plan(self, html=None, language=Language.DE, emojize=False) -> list[OrderedDict]:
        if not html:
            html = self.do_request(language).html

        tabs = list(Mensa._tabs(html))
        num_tabs = len(tabs)
        # one tab for each day open
        if num_tabs != self.location.days_open:
            logger.error(f"Could not find {self.location.days_open} tabs: {num_tabs}")

        days = []
        for t in tabs:
            days.append(self._meals(t))
        return days

    @staticmethod
    def _tabs(html):
        soup = BeautifulSoup(html, 'html5lib')
        for tab in soup.find_all('div', id=re.compile("^tab\d+")):
            yield tab

    @staticmethod
    def _meal_title(meal):
        return MensaBase._strip_additives(meal.find('div', class_='title').text)

    @staticmethod
    def _meal_category(meal):
        return meal.find('div', class_='category').text

    @staticmethod
    def _meal_icons(meal):
        emoji = []
        icons = meal.find_all('div', class_='speiseplanTagKatIcon')
        for icon in icons:
            for i in icon.get('class', []):
                if i != 'speiseplanTagKatIcon':
                    e = Emojize.replace_type(i.strip())
                    if e is not '':
                        emoji.append(e)
        return emoji

    def _meals(self, tab):
        meals = tab.find_all('div', class_='speiseplanTagKat')
        day = OrderedDict()
        for m in meals:
            title = Mensa._meal_title(m)
            category = Mensa._meal_category(m)
            icons = Mensa._meal_icons(m)

            normalized_category = self._normalize_key(category)
            clean_text = self._text_replace(self._clean_text(title.strip()))
            day[normalized_category] = (category, clean_text, icons)
        return day

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

    def retrieve(self, datum=None, language=Language.DE, filter_meal=None, emojize=True) -> Plan:
        if not datum:
            datum = pendulum.today(tz=TIMEZONE)
            logger.debug('No explicit date given, using today.')
        html = self.do_request(language)
        return self._retrieve(html, datum, language, filter_meal, emojize)
