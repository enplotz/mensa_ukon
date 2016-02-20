#! /usr/bin/env python3

import requests
from bs4 import BeautifulSoup
from datetime import date
import argparse
import re, json
from blessings import Terminal

ENDPOINT = 'https://www.max-manager.de/daten-extern/seezeit/html/inc/ajax-php_konnektor.inc.php'

# Some minimum headers we need to send in order to get a response
headers = {
                        'Content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
                        # 'X-Request': 'JSON',
                        # 'X-Requested-With': 'XMLHttpRequest',
                        'Accept-Encoding': 'gzip, deflate'
                    }

FORMATS = ['plain', 'json', 'fancy']
LANGS = ['de', 'en']
LOCATIONS = {'giessberg': 'mensa_giessberg', 'themenpark': 'themenpark_abendessen'}

T = Terminal()

def _post_data(loc, lang, date):
    return 'func=make_spl&loc={0}&lang={1}&date={2}'.format(loc, lang, date)


def _print_json(entries):
    print(json.dumps(entries))


def _print_plain(entries):
    for name, pair in sorted(entries.items()):
        print('{}: {}'.format(pair[0], pair[1]))


def _print_fancy(entries):
    for name, pair in sorted(entries.items()):
        print('{t.bold}{cat}: {t.normal}{desc}'.format(cat=pair[0], desc=pair[1], t=T))


def _normalize(k):
    return k.lower().replace(' ', '_')


def _strip_additives(desc):
    return re.sub('\((\d+,?)+\)', '', desc)


def _extract_meals(responses, filter_meals):
    all_rows = []
    for response in responses:
        soup = BeautifulSoup(response.content, 'html.parser')
        all_rows += soup.find_all('tr')[::2]

    meals = {}
    for row in all_rows:
            # first column in table is category, second is description
            cols = row.find_all('td')
            if len(cols) == 2:
                m = cols[0].text.strip()
                nm = _normalize(m)
                if not filter_meals or nm in (_normalize(meal) for meal in filter_meals):
                    meals[nm] = (m, _strip_additives(cols[1].text.strip()))
    return meals


def _print_formatted(meals, format):
    if format == 'json':
        _print_json(meals)
    elif format == 'plain':
        _print_plain(meals)
    elif format == 'fancy':
        _print_fancy(meals)
    else:
        print('Format not known: {}'.format(format))


def _make_requests(date, loc, lang):
    # date none is: today
    # loc none is: both
    # format none is: plain
    # loc = 'mensa_giessberg'
    # format: 2016-02-22
    # date = (date.today() + timedelta(days=3)).strftime('%Y-%m-%d')

    if loc:
        # we got only one location
        data = _post_data(loc, lang, date)
        return [requests.post(ENDPOINT, headers=headers, data=data)]
    else:
        # we have to make multiple requests
        rs = []
        for key, location in LOCATIONS.items():
            data = _post_data(location, lang, date)
            response = requests.post(ENDPOINT, headers=headers, data=data)
            rs.append(response)
        return rs

def get_meals(date, location=None, language='de', filter_meals=None):
    """Gets the meals at the specified location for the specified day in the specified language.
    """
    return _extract_meals(_make_requests(date, location, language), filter_meals=filter_meals)

if __name__ == '__main__':

    parser = argparse.ArgumentParser(prog='mensa_ukon.py',
        description='Access meal plan of Uni Konstanz like a sane person.')
    parser.add_argument('-d', '--date', dest='date', default=date.today(),
        help='date for the plan (default: today; format: Y-m-d)')
    parser.add_argument('-l', '--location', dest='location', default=None,
        help='location of the mensa (unspecified: both; values: mensa_giessberg, themenpark_abendessen)')
    parser.add_argument('-i', '--language', dest='language', default=LANGS[0], help='language of the descriptions (de (default), en)')
    parser.add_argument('-f', '--format', dest='format', default=FORMATS[0], help='output format (plain (default), json, fancy)')
    parser.add_argument('-m', '--meals', dest='meals', action='append', help='meals to output (nothing specified: all meals; values: small-case meal names with space substituted with _)')
    args = parser.parse_args()

    meals = get_meals(args.date, location=args.location, language=args.language, filter_meals=args.meals)

    if meals and len(meals) > 0:
        _print_formatted(meals, args.format)
    else:
        print('No meals found for day %s.' % args.date)
