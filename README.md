cherry-pick
===========

Scrapes IMDB ratings for an entire run of a television series and plots them with gRaphaël

This tool allows the best episodes to be skimmed from lightly-serialized shows while maintaining the overarching continuity.

A Python script runs with a title query and gathers episode information into a JSON structure that is consumed by the graph. It will also print tab-delimited results through stdout. Each new show needs to be added to the select menu in the HTML, or you can provide a 'shows' GET endpoint that provides a JSON array of file names.

Install
-------

The script is made for Python 3 and uses the Requests and Beautiful Soup packages, as saved in the requirements file:

	pip install -r requirements.txt

Usage
-----

	python cherry-pick.py [-h] [--seasons SEASONS] [-o OUTFILE] query

The **query** should be precise enough to ensure that the target show is the first result in a title query on IMDB. The **seasons** parameter can be a comma-delimited list or a hyphen-delimited range or a combination of both.

	python cherry-pick.py "red dwarf" --seasons 1,3,5-7
