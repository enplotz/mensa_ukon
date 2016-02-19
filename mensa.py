#! /usr/bin/env python3

import requests
from bs4 import BeautifulSoup
from datetime import timedelta, date
import argparse
import re

ENDPOINT = 'https://www.max-manager.de/daten-extern/seezeit/html/inc/ajax-php_konnektor.inc.php'

# Some minimum headers we need to send in order to get a response
headers = {
						'Content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
						'X-Request': 'JSON',
						'X-Requested-With': 'XMLHttpRequest',
						'Accept-Encoding': 'gzip, deflate'
					}

FORMATS = ['plain'] #, 'json']
LANGS = ['de', 'en']
LOCATIONS = {'giessberg': 'mensa_giessberg', 'themenpark': 'themenpark_abendessen'}


def post_data(loc, lang, date):
	return 'func=make_spl&loc={0}&lang={1}&date={2}'.format(loc, lang, date)


def print_json(rows):
	# TODO json output
	pass


def print_plain(meals):
	for name, description in sorted(meals.items()):
			print('{}: {}'.format(name, description))


def normalize(k):
	return k.lower().replace(' ', '_')


def strip_additives(desc):
	return re.sub('\((\d+,?)+\)', '', desc)

def extract_meals(responses, output_meals):
	all_rows = []
	for response in responses:
		soup = BeautifulSoup(response.text, 'html.parser')
		all_rows += soup.find_all('tr')[::2]

	meals = {}
	for row in all_rows:
			# first is category, second is description
			cols = row.find_all('td')
			k = cols[0].text.strip()
			if not output_meals or k in output_meals or normalize(k) in output_meals:
				meals[k] = strip_additives(cols[1].text.strip())
	return meals


def print_formatted(meals, format):
	if format == 'plain':
		print_plain(meals)
	elif format == 'json':
		print_json(meals)
	else:
		print('Format not known: {}'.format(format))


def make_requests(date, loc, lang):
	# date none is: today
	# loc none is: both
	# format none is: plain
	# loc = 'mensa_giessberg'
	# format: 2016-02-22
	# date = (date.today() + timedelta(days=3)).strftime('%Y-%m-%d')

	if loc:
		# we got only one location
		data = post_data(loc, lang, date)
		return [requests.post(ENDPOINT, headers=headers, data=data)]
	else:
		# we have to make multiple requests
		rs = []
		for key, location in LOCATIONS.items():
			data = post_data(location, lang, date)
			# print(data)
			response = requests.post(ENDPOINT, headers=headers, data=data)
			# print(response.text)
			rs.append(response)
		return rs

# TODO add real library API :)

if __name__ == '__main__':

	parser = argparse.ArgumentParser(prog='python3 -m mensa',
		description='Access Seezeit Uni Konstanz mensa plan like a sane person.')
	parser.add_argument('-d', '--date', dest='date', default=date.today(),
		help='date for the plan (default: today)')
	parser.add_argument('-l', '--location', dest='location', default=None,
		help='location of the mensa (default: both)')
	parser.add_argument('-i', '--language', dest='language', default=LANGS[0], help='language of the descriptions (default: de)')
	parser.add_argument('-f', '--format', dest='format', default=FORMATS[0], help='output format (default: plain)')
	parser.add_argument('-m', '--meals', dest='meals', action='append', help='meals to output (default: all meals)')
	args = parser.parse_args()

	responses = make_requests(args.date, args.location, args.language)
	meals = extract_meals(responses, args.meals)
	if meals and len(meals) > 0:
		print_formatted(meals, args.format)
	else:
		print('No meals found for day %s.' % args.date)
