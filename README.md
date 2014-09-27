cherry-pick
===========

Scrapes IMDB ratings for an entire run of a television series and plots them with gRaphaël

This tool allows the best episodes to be skimmed from lightly-serialized shows while maintaining the overarching continuity.

A Python script runs with a title query and gathers episode information into a JSON structure that is consumed by the graph. The data can be served as static files or dynamically with a database - tweak the endpoints to your needs.

> Note: this is a web scaper and is subject to break at any point due to document restructuring on IMDB's part.

A connector for RethinkDB is provided to load results into a database.

Install
-------

The script is made for Python 3 and uses the Requests and Beautiful Soup packages, as saved in the requirements file:

	pip install -r requirements.txt

Install the `rethinkdb` package to use the database connector.

Usage
-----

	python cherrypick.py [-h] [--seasons SEASONS] [-o OUTFILE] query

The **query** should be precise enough to ensure that the target show is the first result in a title query on IMDB. The **seasons** parameter can be a comma-delimited list or a hyphen-delimited range or a combination of both.

	python cherrypick.py "red dwarf" --seasons 1,3,5-7 -o red_dwarf.json

To use the database connector, provide the connection string in the format `host:port/db`.

	python cherrypick.py "the it crowd" --db localhost:28015/cherry

You can also pipe the JSON through stdout with the `--pipe` option. Program messages are sent over stderr.
