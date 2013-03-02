#! /usr/bin/env python
# -*- coding: utf-8 -*-
#

import psycopg2, re, datetime, sys, os, os.path, glob
from wowauc.Pusher import Pusher
from wowauc.Parser import Parser

exec file("wowauc.conf", "rt").read()

CURDIR = os.path.dirname(os.path.abspath(__file__)) + "/"

SRCDIR  = CURDIR + dir_fetched + "/"
TMPDIR  = CURDIR + dir_importing + "/"
DSTDIR  = CURDIR + dir_imported + "/"

moving = True # false for debug

if __name__ == '__main__':
    pusher = Pusher(debug = True)
    pusher.connect(dbhost, dbname, dbuser, dbpass)
    parser = Parser(pusher, 'eu', 'en_US', True)
    try:
        for fname in sorted(glob.glob(SRCDIR + '*.json')):
            if moving:
                tname = TMPDIR + os.path.basename(fname)
                dname = DSTDIR + os.path.basename(fname)
                os.rename(fname, tname)
                parser.parse_file(tname)
                os.rename(tname, dname)
            else:
                parser.parse_file(fname)
    #        break
    finally:
        if pusher.is_started():
            print "abort"
            pusher.abort()
        pusher.disconnect()
    print "done"
