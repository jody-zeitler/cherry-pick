#!/usr/bin/env python3

# Refresh database documents for any current TV series

import sys
from datetime import datetime, timedelta
import rethinkdb as r

from cherrypick import pick_cherries

DB_HOST = 'localhost'
DB_PORT = '28015'
DB_DB   = 'cherry'

TIMEZONE = '-06:00'
DAYS_AGO = 21 # days since last episode aired

def main(args):
    with r.connect(host=DB_HOST, port=DB_PORT, db=DB_DB).repl() as conn:
        today = datetime.now(r.make_timezone(TIMEZONE))
        delta = today - timedelta(days=DAYS_AGO)

        # map: seasons with episodes that aired within a timedelta, merged with series ID and name
        # reduce: list concatenation
        series = r.table('series').map(
            lambda series:
                series['seasons'].filter(
                    lambda season: season['episodes'].filter(
                        lambda ep: r.iso8601(ep['airdate'], default_timezone=TIMEZONE).during(delta, today)
                    ).count().gt(0)
                ).pluck('season_number').merge(series.pluck('series_id', 'series_name'))
        ).reduce(lambda a, b: a + b).run()

    if len(series) < 1:
        print("No current series in database")

    for s in series:
        pick_cherries(s['series_id'], s['season_number'], outdb='{}:{}/{}'.format(DB_HOST, DB_PORT, DB_DB))

if __name__=="__main__": sys.exit(main(sys.argv))
