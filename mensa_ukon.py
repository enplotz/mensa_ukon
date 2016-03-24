#! /usr/bin/env python3

import argparse
import json
import logging
import re
from datetime import date

import lxml.html
import requests

class Emoji(object):
    """Hold the Emoji we use."""
    COW = u'\U0001F42E'
    PIG = u'\U0001F437'
    FISH = u'\U0001F41F'
    CHICKEN = u'\U0001F414'
    CHEESE = u'\U0001F9C0'
    SEEDLING = u'\U0001F331'

REPLACEMENTS = {
    re.compile('\(R\)|\(C\)|\(K\)|\(B\)') : Emoji.COW,
    re.compile('\(Sch\)|\(P\)'): Emoji.PIG,
    re.compile('\(F\)'): Emoji.FISH,
    re.compile('\(G\)'): Emoji.CHICKEN,
    re.compile('\(Veg\)'): Emoji.CHEESE,
    re.compile('\(Vegan\)'): Emoji.SEEDLING
}

logger = logging.getLogger(__name__)

ENDPOINT = 'https://www.max-manager.de/daten-extern/seezeit/html/inc/ajax-php_konnektor.inc.php'

# Some minimum headers we need to send in order to get a response
headers = {
    'Content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
    # 'X-Request': 'JSON',
    # 'X-Requested-With': 'XMLHttpRequest',
    'Accept-Encoding': 'gzip, deflate'
}

FORMATS = ['plain', 'json']
LANGS = ['de', 'en']


class Location(object):

    def __init__(self, key, nice_name, shortcut):
        self.key = key
        self.nice_name = nice_name
        self.shortcut = shortcut

    def __str__(self):
        return 'Location("%s", "%s", "%s")' % (self.key, self.nice_name, self.shortcut)

    def __repr__(self):
        return self.__str__()

DEFAULT_LOCATIONS = ['mensa_giessberg', 'themenpark_abendessen']

LOCATIONS = [
    Location('mensa_giessberg', 'Uni', 'giessberg'),
    Location('themenpark_abendessen', 'Themenpart & Abendessen', 'themenpark'),
    Location('mensa_htwg', 'HTWG', 'htwg'),
    Location('mensa_friedrichshafen', 'Friedrichshafen', 'fn'),
    Location('mensa_weingarten', 'Weingarten', 'weingarten'),
    Location('mensa_ravensburg', 'Ravensburg', 'rave'),
]

def _post_data(loc, lang, date):
    # The endpoint is a bit picky, and wants the parameters in exactly the right order, so that does not work:
    # return urllib.parse.urlencode({'func': 'make_spl', 'loc' : loc, 'lang': lang, 'date': date})
    # Instead we have to build the string ourselves quickly.
    return 'func=make_spl&loc={0}&lang={1}&date={2}'.format(loc, lang, date)


def _print_json(entries):
    print(json.dumps(entries))


def _print_plain(canteens):
    for mensa, entries in canteens:
        print('> Mensa: %s' % mensa.nice_name)
        for name, pair in sorted(entries.items()):
            print('{}: {}'.format(pair[0], pair[1]))
        print()


def _normalize_key(k):
    return k.lower().replace(' ', '_')


def _strip_additives(desc):
    return re.sub('\((\d+,?)+\)', '', desc)


def _repl_emoji(text):
    for regex, repl in REPLACEMENTS.items():
        text = regex.sub(repl, text)
    return text


def _normalize_whitespace(text):
    return re.sub('  +', ' ', text)


def _extract_meals(data, filter_meals):
    canteen_meals = []
    for mensa, response in data.values():
        logger.debug('Extracting meals from mensa %s' % mensa.key)
        doc = lxml.html.fromstring(response.text)
        rows = doc.cssselect('tr')[::2]
        meals = {}
        for row in rows:
            cols = row.cssselect('td')
            if len(cols) == 2:
                meal_type = cols[0].text.strip()
                norm_meal_type = _normalize_key(meal_type)
                if not filter_meals or norm_meal_type in (_normalize_key(meal) for meal in filter_meals):
                    meals[norm_meal_type] = (meal_type, _repl_emoji(_normalize_whitespace(_strip_additives(cols[1].text.strip()))))
                    logger.debug(meals[norm_meal_type])
            else:
                logger.error('Not enough values in column for canteen %s' % mensa.key)
        canteen_meals.append((mensa, meals))
    logger.debug(canteen_meals)
    return canteen_meals


def _print_formatted(meals, format):
    if format == 'json':
        _print_json(meals)
    elif format == 'plain':
        _print_plain(meals)
    else:
        print('Format not known: {}'.format(format))


def _make_requests(date, locs, lang):
    logger.debug('Requesting for locations: %s' % locs)

    locations = [loc for loc in LOCATIONS if (len(locs) > 0 and loc.shortcut in locs
                                              or (len(locs) == 0 and loc.key in DEFAULT_LOCATIONS))]

    rs = {}
    for loc in locations:
        data = _post_data(loc.key, lang, date)
        try:
            response = requests.post(ENDPOINT, headers=headers, data=data)
            # tell requests, that we want our text as an utf-8 encoded string, because that's what the
            # endpoint gives us back
            response.encoding = 'utf-8'
            rs[loc.key] = (loc, response)
        except requests.ConnectionError as e:
            logger.error(e)
    return rs


def get_meals(date, locations=DEFAULT_LOCATIONS, language='de', filter_meals=None):
    """Gets the meals at the specified locations for the specified day in the specified language.
    Returns: dictionary of canteens, with a dict of meals for each canteen
    """
    return _extract_meals(_make_requests(date, locations, language), filter_meals=filter_meals)


def main():
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)

    parser = argparse.ArgumentParser(prog='mensa',
                                     description='Access meal plan of Uni Konstanz like a sane person.')
    parser.add_argument('-d', '--date', dest='date', default=date.today(),
                        help='date for the plan (default: today; format: Y-m-d)')
    parser.add_argument('-l', '--location', dest='locations', nargs='+', default=DEFAULT_LOCATIONS,
                        help='locations of the canteens (unspecified: some default; values: mensa_giessberg, themenpark_abendessen)')
    parser.add_argument('-i', '--language', dest='language', default=LANGS[0],
                        help='language of the descriptions (de (default), en)')
    parser.add_argument('-f', '--format', dest='format', default=FORMATS[0],
                        help='output format (plain (default), json)')
    parser.add_argument('-m', '--meals', dest='meals', nargs='+',
                        help='meals to output (nothing specified: all meals; values: small-case meal names with space substituted with _)')
    args = parser.parse_args()

    meals = get_meals(args.date, locations=args.locations, language=args.language, filter_meals=args.meals)

    if meals and len(meals) > 0:
        _print_formatted(meals, args.format)
    else:
        print('No meals found for day %s.' % args.date)

if __name__ == '__main__':
    main()
