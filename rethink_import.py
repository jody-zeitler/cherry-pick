#!/usr/bin/env python

import sys, os, argparse, re, json
import rethinkdb as r

def main(args):
    parser = argparse.ArgumentParser(description='Import cherry-pick JSON into RethinkDB.')
    parser.add_argument('input', help='input JSON file')
    parser.add_argument('-d', '--database', required=True, help='database connection string "host:port/db"')
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print('input file does not exist!')
        return 1

    (host, port, db) = re.compile(r'[:/]').split(args.database)
    conn = connect_db(host, port, db)
    
    if 'series' not in r.table_list().run():
        r.table_create('series').run()

    with open(args.input, 'r') as infile:
        try:
            injson = json.loads( infile.read() )
            
            if 'series_id' not in injson.keys():
                print('no series_id present in JSON')
                return 2

            series_id = injson['series_id']
            series_name = injson['series_name']
            db_id = existence_check(injson['series_id'])

            if db_id:
                print('updating document for {}'.format(series_name))
                update_document(db_id, injson)
            else:
                print('inserting document for {}'.format(series_name))
                insert_document(injson)
        except IOError:
            print('could not read file')
        except ValueError:
            print('could not parse JSON')
        except:
            print('could not insert data')

    conn.close()

    return 0

def connect_db(host, port, db):
    conn = r.connect(host=host, port=port, db=db).repl()
    return conn

def existence_check(series_id):
    for doc in r.table('series').filter({'series_id': series_id}).run():
        return doc['id']
    return None

def update_document(id, data):
    r.table('series').get(id).update(data).run()

def insert_document(data):
    r.table('series').insert(data).run()

if __name__=="__main__": sys.exit(main(sys.argv))

