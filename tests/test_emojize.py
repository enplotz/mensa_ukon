import os
from mensa_ukon import Mensa

from requests_html import HTMLSession
from requests_file import FileAdapter
from bs4 import BeautifulSoup

session = HTMLSession()
session.mount('file://', FileAdapter())

from mensa_ukon.emojize import Emoji, Emojize


class TestEmojize:

    def test_meal_icons(self):
        def get():
            path = os.path.sep.join((os.path.dirname(os.path.abspath(__file__)), 'meal.html'))
            url = f'file://{path}'
            return session.get(url)

        html = get().html.html
        icons = Mensa._meal_icons(BeautifulSoup(html, 'html5lib'))
        assert [Emoji.PIG, Emoji.COW] == icons


if __name__ == '__main__':
    TestEmojize().test_meal_icons()