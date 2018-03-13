import os, pprint, collections, pendulum
from mensa_ukon import Mensa
from mensa_ukon.constants import Language

from requests_html import HTMLSession, AsyncHTMLSession, HTML
from requests_file import FileAdapter

session = HTMLSession()
session.mount('file://', FileAdapter())


def get():
    path = os.path.sep.join((os.path.dirname(os.path.abspath(__file__)), 'giessberg.html'))
    url = f'file://{path}'
    return session.get(url)

class TestMensa:


    def test_normalize_keys(self):

        # test is lowercased and spaces are replaced by underscores
        k1 = 'Key 1'
        exp1 = 'key_1'
        assert exp1 == Mensa._normalize_key(k1)
        assert exp1 == Mensa._normalize_key(exp1)

        k2 = ' KeY 2 '
        exp2 = 'key_2'
        assert exp2 == Mensa._normalize_key(k2)

    def test_strip_additives(self):
        # these should all result in empty strings
        strip = [
            '(1,2,3,4,5)',
            '( 1, 2,3 ,  4,  5,6)',
            '(1, 2,3 , 4,5,6 )',
            '(1a,2b,3c,4,5e)',
            '( 1a, b,c,d, 2,3 ,  4,  5,6)',
            '(1, 2,3a, b,4a,5,6 )',
            '(25a, b,c,31)',
        ]
        for s in strip:
            assert Mensa._strip_additives(s) == ''

        # result in only normal text
        for s in strip:
            assert Mensa._strip_additives('Foo {} bar.'.format(s)) == 'Foo  bar.'

    def test_normalize_whitespace(self):
        assert Mensa._normalize_whitespace('  ') == ' '
        assert Mensa._normalize_whitespace('  a  ') == ' a '
        assert Mensa._normalize_whitespace('a  a') == 'a a'
        assert Mensa._normalize_whitespace('\t\t') == ' '
        assert Mensa._normalize_whitespace(' \t') == ' '

    def test_normalize_orthography(self):
        assert Mensa._normalize_orthography(' ,') == ','
        assert Mensa._normalize_orthography('aaa, ,') == 'aaa,,'

    def test_clean_text(self):
        assert Mensa._clean_text('\tThe quick  brown fox   , jumps over (1,2,2a,b, 9) the lazy dog.  ') == \
               'The quick brown fox, jumps over the lazy dog.'


    def test_find_meals_file(self):
        # 10 days
        # 10 meal types
        r = get()
        assert r.status_code == 200
        m = Mensa(location='giessberg')
        days = m._retrieve_plan(html=r.html.html)
        assert 10 == len(days)
        for day  in days:
            l =  len(day.keys())
            assert 10 == l

    def test_find_meals_online(self):
        m = Mensa(location='giessberg')
        days = m._retrieve_plan()
        assert 10 == len(days)
        for day  in days:
            l =  len(day.keys())
            assert 10 == l

    # TODO fix test: either no meals (for weekend, holidays etc.), or 10
    # def test_retrieve(self):
    #     m = Mensa(location='giessberg')
    #     meals = m._retrieve(get().html, pendulum.today(), filter_meal=None, language=Language.de, emojize=True)
    #     assert 10 == len(meals.meals)
