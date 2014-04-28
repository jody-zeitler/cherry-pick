#!/usr/bin/env python

import sys, os, re, json, argparse
from datetime import datetime

import requests
from bs4 import BeautifulSoup

base_url = 'http://www.imdb.com'

def main(args):
	parser = argparse.ArgumentParser(description='Fetch TV show information from IMDB and store in JSON format.')
	parser.add_argument('query', help='title query to search on')
	parser.add_argument('--seasons', help='season set or range')
	parser.add_argument('-o', '--outfile', help='output JSON location')
	args = parser.parse_args()

	query = args.query
	season_filter = args.seasons
	outpath = args.outfile

	if outpath and not os.path.isdir( os.path.dirname( os.path.abspath(outpath) ) ):
		print('output path does not exist!')
		return 1
	
	if not outpath:
		outpath = os.path.join('json', query.replace(' ', '_') + '.json')
		if not os.path.isdir('json'):
			os.mkdir('json')

	title_res = requests.get('{}/find?q={}&s=tt'.format(base_url, query))
	title_soup = BeautifulSoup(title_res.text)

	series_url = title_soup.select('td.result_text a')[0]['href']
	series_id = re.findall(r'tt\d+', series_url)[0]

	base_season_url = '{}/title/{}/episodes'.format(base_url, series_id)
	series_res = requests.get(base_season_url)
	series_soup = BeautifulSoup(series_res.text)

	season_list = [int(option['value']) for option in series_soup.select('select#bySeason option[value]') if option['value'].isdigit() and option['value'] > '0']
	season_years = [int(option['value']) for option in series_soup.select('select#byYear option[value]') if option['value'].isdigit() and option['value'] > '1900']
	series_name = get_first( series_soup.select('a.subnav_heading') )

	if len(season_list) < 1:
		print('No seasons found')
		return
	
	json_data = {
		"series_id": series_id,
		"series_name": series_name,
		"season_count": len(season_list),
		"years_on_air": "{}-{}".format(min(season_years), max(season_years)),
		"seasons": []
	}

	# filter season list
	if season_filter is not None:
		season_set = set()
		commas = season_filter.split(',')
		for segment in commas:
			if '-' in segment:
				dashes = segment.split('-')
				season_set |= set( range(int(dashes[0]), int(dashes[1]) + 1) )
			else:
				season_set.add( int(segment) )
		season_list = [s for s in season_list if s in season_set]

	print('Season\tEpisode\tTitle\tRating\tSummary')

	for season in sorted(season_list):
		season_res = requests.get('{}?season={}'.format(base_season_url, season))
		season_soup = BeautifulSoup(season_res.text)
		episode_list = season_soup.select('.info a[itemprop="name"]')

		season_data = {
			"season_number": season,
			"season_year": datetime.now().year,
			"episodes": []
		}
		json_data["seasons"].append(season_data)
		
		for episode_link in episode_list:
			episode_url = '{}{}'.format(base_url, episode_link['href'])
			episode_res = requests.get(episode_url)
			episode_soup = BeautifulSoup(episode_res.text)

			episode_label = get_first( episode_soup.select('.tv_header span.nobr') )
			match = re.match(r'Season (\d+), Episode (\d+)', episode_label)

			season_number = try_cast(match.group(1), int)
			episode_number = try_cast(match.group(2), int)
			episode_name = get_first( episode_soup.select('.header span.itemprop') )
			episode_airdate = parse_date( get_first( episode_soup.select('.header span.nobr') ) )
			episode_rating = try_cast( get_first( episode_soup.select('span[itemprop="ratingValue"]') ), float)
			episode_summary = get_first( episode_soup.select('p[itemprop="description"]') ).replace('\n', ' ').replace('See full summary»', '')

			if episode_rating == 0:
				continue

			if episode_airdate and episode_airdate.year < season_data["season_year"]:
				season_data["season_year"] = episode_airdate.year

			season_data["episodes"].append({
				'season_number': season_number,
				'episode_number': episode_number,
				'episode_name': episode_name,
				'episode_airdate': episode_airdate.isoformat(),
				'episode_rating': episode_rating,
				'episode_summary': episode_summary,
				'episode_url': episode_url
			})
			try:
				print('{0:d}\t{1:d}\t{2}\t{3:.1f}\t{4}'.format(season_number, episode_number, episode_name, episode_rating, episode_summary))
			except UnicodeEncodeError:
				print('--Can\'t print unicode sequence--')

	with open(outpath, 'w') as outfile:
		outfile.write( json.dumps(json_data) )

	print('Done!')

def get_first(collection):
	if len(collection) > 0:
		return collection[0].get_text(strip=True)
	else:
		return ''

def try_cast(value, cast=str):
	try:
		return cast(value)
	except:
		return cast()

def parse_date(value):
	try:
		return datetime.strptime( value.replace('.', ''), '(%d %b %Y)' )
	except:
		return None

if __name__=='__main__': sys.exit(main(sys.argv))