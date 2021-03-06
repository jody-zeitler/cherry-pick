#!/usr/bin/env python3

# built-in
import sys, os, re, json, argparse
from datetime import datetime

# pip
import requests
from bs4 import BeautifulSoup

# local
import connector

BASE_URL = 'http://www.imdb.com'

def main(args):
    """Turn arguments into function parameters."""
    parser = argparse.ArgumentParser(description='Fetch TV show information from IMDB and store in JSON format.')
    parser.add_argument('query', help='title query to search on')
    parser.add_argument('--seasons', help='season set or range')
    parser.add_argument('--years', help='year set or range')
    parser.add_argument('-o', '--outfile', help='output JSON location')
    parser.add_argument('--db', '--database', help='database connection string "host:port/db"')
    parser.add_argument('--pipe', action='store_true', help='pipe JSON to stdout')
    args = parser.parse_args()

    pick_cherries(args.query, args.seasons, args.outfile, args.db, args.pipe)

def pick_cherries(query, season_filter=None, outpath=None, outdb=None, pipe=False):
    """Common entry point for command-line and imports."""
    file_connector = None
    db_connector = None

    if outpath:
        if not os.path.isdir( os.path.dirname( os.path.abspath(outpath) ) ):
            print_err('output path does not exist!')
            return 1
        file_connector = connector.JSONFile(outpath)

    if outdb:
        (host, port, db) = re.compile(r'[:/]').split(outdb)
        db_connector = connector.RethinkDB(host, port, db)
        db_connector.test()

    json_data = gather_data(query, season_filter)

    if file_connector:
        file_connector.write(json_data)

    if db_connector:
        db_connector.write(json_data)

    if pipe is True:
        print(json.dumps(json_data))

def gather_data(query, season_filter=None):
    """Run the query and return series data as a dictionary."""
    series_id = ''
    if query.startswith('tt'):
        series_id = query
    else:    
        title_res = requests.get('{}/find?q={}&s=tt'.format(BASE_URL, query))
        title_soup = BeautifulSoup(title_res.text)

        result_url = title_soup.select('td.result_text a')[0]['href']
        series_id = re.findall(r'tt\d+', result_url)[0]

    series_url = '{}/title/{}/episodes'.format(BASE_URL, series_id)
    series_res = requests.get(series_url)
    series_soup = BeautifulSoup(series_res.text)

    season_list = [int(option['value']) for option in series_soup.select('select#bySeason option[value]') if option['value'].isdigit() and option['value'] > '0']
    season_years = [int(option['value']) for option in series_soup.select('select#byYear option[value]') if option['value'].isdigit() and option['value'] > '1900']
    series_name = get_first( series_soup.select('a.subnav_heading') )

    if len(season_list) < 1:
        print_err('No seasons found')
        return 2
    
    json_data = {
        "series_id": series_id,
        "series_name": series_name,
        "season_count": len(season_list),
        "years_on_air": "{}-{}".format(min(season_years), max(season_years)),
        "seasons": []
    }

    if season_filter is not None:
        season_list = filter_seasons(season_list, season_filter)

    print_err('Season\tEpisode\tAir Date\tTitle\tRating')

    for season in sorted(season_list):
        season_url = '{}?season={}'.format(series_url, season)
        season_data = get_season(season, season_url)
        if len(season_data['episodes']) > 0:
            json_data["seasons"].append(season_data)

    return json_data

def filter_seasons(season_list, season_filter):
    """Filter discovered seasons using a filter."""
    season_set = set()
    commas = str(season_filter).split(',')
    for segment in commas:
        if '-' in segment:
            dashes = segment.split('-')
            season_set |= set( range(int(dashes[0]), int(dashes[1]) + 1) )
        else:
            season_set.add( int(segment) )
    return [s for s in season_list if s in season_set]

def get_season(season_number, season_url):
    """Return data for a particular season."""
    season_res = requests.get(season_url)
    season_soup = BeautifulSoup(season_res.text)
    episode_list = season_soup.select('.info a[itemprop="name"]')

    season_data = {
        "season_number": season_number,
        "season_year": datetime.now().year,
        "episodes": []
    }
    
    for episode_link in episode_list:
        episode_url = '{}{}'.format(BASE_URL, episode_link["href"])
        episode = get_episode(episode_url)
        
        if episode: 
            if episode["airdate"]:
                if episode["airdate"].year < season_data["season_year"]:
                    season_data["season_year"] = episode["airdate"].year
                episode["airdate"] = episode["airdate"].isoformat()
            
            season_data["episodes"].append(episode)

    return season_data

def get_episode(episode_url):
    """Return data for a particular episode."""
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
        return None

    try:
        print_err('{:d}\t{:d}\t{:%Y-%m-%d}\t{}\t{:.1f}'.format(season_number, episode_number, episode_airdate or datetime.now(), episode_name, episode_rating))
    except UnicodeEncodeError:
        print_err('--Can\'t print unicode sequence--')

    return {
        "season_number": season_number,
        "episode_number": episode_number,
        "episode_name": episode_name,
        "episode_url": episode_url,
        "airdate": episode_airdate,
        "rating": episode_rating,
        "summary": episode_summary
    }

def get_first(collection):
    """Get the first text content of a list of DOM nodes or return empty string."""
    if len(collection) > 0:
        return collection[0].get_text(strip=True)
    else:
        return ''

def try_cast(value, cast=str):
    """Cast the value to a type or return the default value of the type."""
    try:
        return cast(value)
    except:
        return cast()

def parse_date(value):
    """Convert IMDB date string into a datetime object."""
    try:
        return datetime.strptime( value.replace('.', ''), '(%d %b %Y)' ).date()
    except:
        return None

def print_err(line):
    """Print to stderr."""
    return print(line, file=sys.stderr)

if __name__=='__main__': sys.exit(main(sys.argv))
