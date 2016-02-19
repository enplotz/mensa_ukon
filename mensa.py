#! /usr/bin/env python3

import requests
from bs4 import BeautifulSoup
from datetime import timedelta, date
import argparse

ENDPOINT = 'https://www.max-manager.de/daten-extern/seezeit/html/inc/ajax-php_konnektor.inc.php'

# Some minimum headers we need to send in order to get a response
headers = {
						'Content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
						'X-Request': 'JSON',
						'X-Requested-With': 'XMLHttpRequest',
						'Accept-Encoding': 'gzip, deflate'
					}

# TODO
# arguments: date, loc, lang, format
# (*): default

# date:
# today (*), tomorrow, specific date
# loc:
# giessberg, themenpark, all (*)
# lang:
# de (*), en
# format:
# json, plain (*)

FORMATS = ['plain'] #, 'json']
LANGS = ['de', 'en']
LOCATIONS = {'giessberg': 'mensa_giessberg', 'themenpark': 'themenpark_abendessen'}


def post_data(loc, lang, date):
	return 'func=make_spl&loc={0}&lang={1}&date={2}'.format(loc, lang, date)

def print_json(rows):
	# TODO
	pass


def print_plain(rows):
	meals = {}
	for row in rows:
			# first is category, second is description
			cols = row.find_all('td')
			meals[cols[0].text.strip()] = cols[1].text.strip()

	for name, description in sorted(meals.items()):
			print('{}: {}'.format(name, description))


def process_responses(response, format):
	all_rows = []
	for response in responses:
		soup = BeautifulSoup(response.text, 'html.parser')
		all_rows += soup.find_all('tr')[::2]

	if format == 'plain':
		print_plain(all_rows)
	elif format == 'json':
		print_json(all_rows)
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
		data = post_data(location, lang, date)
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




if __name__ == '__main__':

	parser = argparse.ArgumentParser(prog='python3 -m mensa',
		description='Access Seezeit Uni Konstanz mensa plan.')
	parser.add_argument('-d', '--date', dest='date', default=date.today(),
		help='date for the plan (default: today)')
	parser.add_argument('-l', '--location', dest='location', default=None,
		help='location of the mensa (default: both)')
	parser.add_argument('-i', '--language', dest='language', default=LANGS[0])
	parser.add_argument('-f', '--format', dest='format', default=FORMATS[0])
	args = parser.parse_args()

	# print(args)
	responses = make_requests(args.date, args.location, args.language)
	process_responses(responses, args.format)



