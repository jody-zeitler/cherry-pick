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
	series_res = requests.get('{0}{1}'.format(base_url, series_url))
	
	season_list = re.findall(r'href="(/title/.*?/episodes\?season=(\d+))', series_res.text)

	if season_filter is not None:
		season_list = [s for s in season_list if s[1] in season_filter.split(',')]

	if len(season_list) < 1:
		print('No seasons found')
		return

	json_data = []

	with open(os.path.join('csv', query.replace(' ', '_') + '.txt'), 'w') as outfile:
		print('Season\tEpisode\tTitle\tRating\tSummary')
		outfile.write('Season\tEpisode\tTitle\tRating\tSummary\n')

		for season in sorted(season_list, key=lambda s: s[1]):
			season_res = requests.get('{0}{1}'.format(base_url, season[0]))
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