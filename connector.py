import sys
import json

try:
    import rethinkdb as r
except ImportError:
    r = None


class JSONFile(object):
    def __init__(self, path):
        self.path = path

    def write(self, data):
        with open(self.path, 'w') as outfile:
            print('writing to {}'.format(self.path), file=sys.stderr)
            outfile.write(json.dumps(data))


class RethinkDB(object):
    def __init__(self, host, port, db, replace=False):
        if r is None:
            raise Exception("RethinkDB driver is not installed! Install it with pip/pip3!")

        self.host = host
        self.port = port
        self.db = db
        self.replace = replace

    def test(self):
        self.__connect_db().close()

    def write(self, data):
        with self.__connect_db() as conn:
            self.__check_table()

            series_id = data['series_id']
            series_name = data['series_name']
            document = self.__existence_check(series_id)

            if document:
                if self.replace is True:
                    print('replacing document for {}'.format(series_name), file=sys.stderr)
                    res = self.__replace_document(document, data)
                else:
                    print('updating document for {}'.format(series_name), file=sys.stderr)
                    self.__update_document(document, data)
            else:
                print('inserting document for {}'.format(series_name), file=sys.stderr)
                self.__insert_document(data)

    def __connect_db(self):
        conn = r.connect(host=self.host, port=self.port, db=self.db).repl()
        return conn

    @staticmethod
    def __check_table():
        if 'series' not in r.table_list().run():
            r.table_create('series').run()

    @staticmethod
    def __existence_check(series_id):
        for doc in r.table('series').filter({'series_id': series_id}).run():
            return doc
        return None

    @staticmethod
    def __replace_document(document, data):
        data['id'] = document['id']
        return r.table('series').get(document['id']).replace(data).run()

    @staticmethod
    def __update_document(document, data):
        for season in document['seasons']:
            new_season = [s for s in data['seasons'] if s['season_number'] == season['season_number']]
            if len(new_season) == 0:
                data['seasons'].insert(0, season)

        return r.table('series').get(document['id']).update(data).run()

    @staticmethod
    def __insert_document(data):
        return r.table('series').insert(data).run()
