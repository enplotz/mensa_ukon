#! /usr/bin/env python3

import argparse
import json
import logging
import re
from collections import OrderedDict
from datetime import date

import lxml.html
import urllib

class Emoji(object):
    """Hold the Emoji we use."""
    COW = u'\U0001F42E'
    PIG = u'\U0001F437'
    FISH = u'\U0001F41F'
    CHICKEN = u'\U0001F414'
    CHEESE = u'\U0001F9C0'
    SEEDLING = u'\U0001F331'


logger = logging.getLogger(__name__)

RE_DATE_FORMAT = re.compile('\d{4}-\d{2}-\d{2}')

PDF_URL_THIS_WEEK = 'https://www.max-manager.de/daten-extern/seezeit/pdf/wochenplaene/mensa_giessberg/aktuell.pdf'
PDF_URL_NEXT_WEEK = 'https://www.max-manager.de/daten-extern/seezeit/pdf/wochenplaene/mensa_giessberg/naechste-woche.pdf'
ENDPOINT = 'https://www.max-manager.de/daten-extern/seezeit/html/inc/ajax-php_konnektor.inc.php'

# Some minimum headers we need to send in order to get a response
headers = {
    'Content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'Accept-Encoding': 'gzip, deflate'
}

FORMATS = ['plain', 'json']
LANGS = ['de', 'en']


class Location(object):
    def __init__(self, key, nice_name, shortcut, order=None):
        self.key = key
        self.nice_name = nice_name
        self.shortcut = shortcut
        self.order = order

    def __str__(self):
        return 'Location("%s", "%s", "%s")' % (self.key, self.nice_name, self.shortcut)

    def __repr__(self):
        return self.__str__()


DEFAULT_LOCATIONS = ['giessberg', 'themenpark']

LOCATIONS = OrderedDict({
    'giessberg': Location('mensa_giessberg', 'Uni', 'giessberg', {
        'stammessen': 0, 'wahlessen': 1, 'vegetarisch': 2, 'beilagen': 3, 'eintopf': 4, 'al_studente': 5
    }),
    'themenpark': Location('themenpark_abendessen', 'Themenpark & Abendessen', 'themenpark', {
        'wok': 2, 'grill': 0, 'bioessen': 1, 'abendessen': 3
    }),
    'htwg': Location('mensa_htwg', 'HTWG', 'htwg'),
    'fn': Location('mensa_friedrichshafen', 'Friedrichshafen', 'fn'),
    'weingarten': Location('mensa_weingarten', 'Weingarten', 'weingarten'),
    'rave': Location('mensa_ravensburg', 'Ravensburg', 'rave'),
})


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


def _clean_text(text):
    return __normalize_orthography(__normalize_whitespace(__strip_additives(text)))


def __strip_additives(text):
    return re.sub('\((\d+[,.]?)+\)', '', text)


def __normalize_whitespace(text):
    return re.sub('\s{2,}', ' ', text)


def __normalize_orthography(text):
    return re.sub('\s,', ',', text)


IN_PARENS = re.compile('\(([^)]*?)(?:,([^)]*?))?\)')
# List of possible meals, comma separated.
TOKENS = [
    (Emoji.COW, re.compile('[RCKB]')),
    (Emoji.PIG, re.compile('Sch|P')),
    (Emoji.FISH, re.compile('F')),
    (Emoji.CHICKEN, re.compile('G')),
    (Emoji.SEEDLING, re.compile('Vegan')),
    (Emoji.CHEESE, re.compile('Veg')),
]


def _repl_all_emoji(match_object):
    """
    Used to replace shorthands with emoji
    :param text: text shorthands inside parenthesis
    :return:
    """
    emoji = []
    for group in match_object.groups():
        if group:
            for e, regex in TOKENS:
                if regex.fullmatch(group.strip()):
                    emoji.append(e)
                    break
            else:
                # we have to put back our extracted string, which we could not
                # match with an Emoji character
                emoji.append(group)
    return '(' + ", ".join(emoji) + ')'


def _repl_emoji(text):
    """Replaces shorthands of meal types with emojis.
    :param text: description of a meal
    :return: description with substituted text shorthands as emoji characters
    """
    logger.debug('Replacing text %s' % text)
    return IN_PARENS.sub(_repl_all_emoji, text)


def _extract_meals(data, filter_meals):
    canteen_meals = []
    filter_meal_keys = [_normalize_key(meal) for meal in filter_meals] if filter_meals else []
    for mensa, content in data.values():
        logger.debug('Extracting meals from mensa %s' % mensa.key)
        logger.debug('Content\n{}'.format(content))
        doc = lxml.html.fromstring(content)
        rows = doc.cssselect('tr')[::2]
        meals = {}
        for row in rows:
            cols = row.cssselect('td')
            if len(cols) == 2:
                meal_type = cols[0].text.strip()
                norm_meal_type = _normalize_key(meal_type)
                if not filter_meals or norm_meal_type in filter_meal_keys:
                    meals[norm_meal_type] = (meal_type, _repl_emoji(_clean_text(cols[1].text.strip())))
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
    """ Makes requests for the given date in the given language at the specified locations (shortcodes).
    """
    locs = locs or DEFAULT_LOCATIONS
    logger.debug('Requesting for locations: %s' % locs)
    locations = [LOCATIONS[k] for k in locs]
    rs = {}
    # http = urllib3.PoolManager()
    for loc in locations:
        data = _post_data(loc.key, lang, date).encode('ascii')
        try:
            req = urllib.request.Request(ENDPOINT, data=data, headers=headers, method='POST')
            with urllib.request.urlopen(req) as f:
                rs[loc.key] = (loc, f.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            logger.error(e)
    return rs


def get_meals(date, locations=None, language='de', filter_meals=None):
    """Gets the meals at the specified locations for the specified day in the specified language.
    Returns: dictionary of canteens, with a dict of meals for each canteen
    """
    return _extract_meals(_make_requests(date, locations, language), filter_meals=filter_meals)


def main_cli():
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.WARNING)

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
    main_cli()
