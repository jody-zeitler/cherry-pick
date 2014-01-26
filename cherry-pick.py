#!/usr/bin/env python

import sys,os,re,json
import requests
from bs4 import BeautifulSoup

base_url = 'http://www.imdb.com'

def main(args):
	if len(args) < 2:
		print('pass a title query')
		return

	query = args[1]

	if len(args) > 2:
		season_filter = args[2]
	else:
		season_filter = None

	title_res = requests.get('{0}/find?q={1}&s=tt'.format(base_url, query))
	title_soup = BeautifulSoup(title_res.text)

	series_url = title_soup.select('td.result_text a')[0]['href']
	series_id = re.findall(r'tt\d+', series_url)[0]

	base_season_url = '{0}/title/{1}/episodes'.format(base_url, series_id)
	series_res = requests.get(base_season_url)
	series_soup = BeautifulSoup(series_res.text)

	season_list = [int(option['value']) for option in series_soup.select('select#bySeason option') if option['value'].isdigit() and option['value'] > '0']

	if len(season_list) < 1:
		print('No seasons found')
		return
	
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

	json_data = []

	if not os.path.isdir('csv'):
		os.mkdir('csv')
	if not os.path.isdir('json'):
		os.mkdir('json')

	with open(os.path.join('csv', query.replace(' ', '_') + '.txt'), 'w') as outfile:
		print('Season\tEpisode\tTitle\tRating\tSummary')
		outfile.write('Season\tEpisode\tTitle\tRating\tSummary\n')

		for season in sorted(season_list):
			season_res = requests.get('{0}?season={1}'.format(base_season_url, season))
			season_soup = BeautifulSoup(season_res.text)
			episode_list = season_soup.select('.info a[itemprop="name"]')
			
			for episode_link in episode_list:
				episode_url = '{0}{1}'.format(base_url, episode_link['href'])
				episode_res = requests.get(episode_url)
				episode_soup = BeautifulSoup(episode_res.text)

				episode_label = get_first( episode_soup.select('.tv_header span.nobr') )
				match = re.match(r'Season (\d+), Episode (\d+)', episode_label)

				season_number = try_cast(match.group(1), int)
				episode_number = try_cast(match.group(2), int)
				episode_name = get_first( episode_soup.select('.header span.itemprop') )
				episode_rating = try_cast( get_first( episode_soup.select('span[itemprop="ratingValue"]') ), float)
				episode_summary = get_first( episode_soup.select('p[itemprop="description"]') ).replace('\n', ' ').replace('See full summary»', '')

				if episode_rating == 0:
					continue

				json_data.append({
					'season_number': season_number,
					'episode_number': episode_number,
					'episode_name': episode_name,
					'episode_rating': episode_rating,
					'episode_summary': episode_summary,
					'episode_url': episode_url
				})
				try:
					print('{0:d}\t{1:d}\t{2}\t{3:.1f}\t{4}'.format(season_number, episode_number, episode_name, episode_rating, episode_summary))
				except UnicodeEncodeError:
					print('--Can\'t print unicode sequence--')
				outfile.write('{0:d}\t{1:d}\t{2}\t{3:.1f}\t{4}\n'.format(season_number, episode_number, episode_name, episode_rating, episode_summary))

	with open(os.path.join('json', query.replace(' ', '_') + '.json'), 'w') as outfile:
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

if __name__=='__main__': sys.exit(main(sys.argv))