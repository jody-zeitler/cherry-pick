#!/usr/bin/env python

# Refresh database documents for any current TV series

import sys, os, subprocess
from datetime import datetime, timedelta
import rethinkdb as r


def main(args):
    conn = r.connect(host='localhost', port=28015, db='cherry').repl()

    today = datetime.now(r.make_timezone('-06:00'))
    threeweeks = today - timedelta(weeks=3)

    series = res = r.table('series').map(
        lambda series:
            series['seasons'].filter(
                lambda season: season['episodes'].filter(
                    lambda ep: r.iso8601(ep['airdate'], default_timezone='-06:00').during(threeweeks, today)
                ).count().gt(0)
            ).pluck('season_number').merge(series.pluck('series_id', 'series_name'))
    ).reduce(lambda a, b: a + b).run()

    if len(series) < 1:
        print("No current series in database")

    for s in series:
        pick = subprocess.Popen([
            '/opt/nodejs/www/cherrypick/cherrypick.py',
            str(s['series_id']),
            '--seasons',
            str(s['season_number'])
        ], stdout=subprocess.PIPE)
        (injson, err) = pick.communicate()
        
        update = subprocess.Popen([
            '/opt/nodejs/www/cherrypick/rethink_import.py',
            '-d',
            'localhost:28015/cherry'
        ], stdin=subprocess.PIPE)
        update.communicate(injson)

    conn.close()

if __name__=="__main__": sys.exit(main(sys.argv))

