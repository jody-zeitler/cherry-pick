#!/bin/bash

./cherrypick.py "$@" | ./rethink_import.py -d 'localhost:28015/cherry'

