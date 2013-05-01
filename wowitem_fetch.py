#! /usr/bin/env python
# -*- coding: utf-8 -*-
#

import pycurl
import cStringIO
import time
import os.path
import sys

exec file("wowauc.conf", "rt").read()

#if ("item_locales" not in dir()):
#    item_locales = "en_US ru_RU"

ids = file(items_ids, "rt").read().split()
locales = items_locales.split()


CURDIR = os.path.dirname(os.path.abspath(__file__)) + "/"
SAVEDIR = CURDIR + dir_fetched_items + "/"

QUIET   = '-q' in sys.argv

def dumphdr(hdr):
    if QUIET: return
    print "%% got headers: %s" % repr(hdr)
    return


def fetch(region):
    left = items_fetch_per_session
    if not QUIET:
        print "* fetching for %d unfetched items" % left
    c = pycurl.Curl()

    c.setopt(c.CONNECTTIMEOUT, 15)
    c.setopt(c.TIMEOUT, 15)
    if "http_proxy" in dir():
        PXY = http_proxy
    else:
        PXY = os.getenv("http_proxy")
    if PXY:    
        c.setopt(c.PROXY, PXY)
    c.setopt(c.ENCODING, 'gzip')
    c.setopt(c.FOLLOWLOCATION, True)
    c.setopt(c.HEADERFUNCTION, dumphdr)
    c.setopt(c.HTTPHEADER, ['Pragma: no-cache', 'Cache-Control: no-cache'])

    for id in ids:
        if left <= 0:
            print "limit reached"
            break
        iid = int(id)
        showed = False
        for loc in locales:
            fname = "%s/%06d-%s.json" % (SAVEDIR, iid, loc)
            if os.path.exists(fname):
                continue
            buf = cStringIO.StringIO()
            c.setopt(c.WRITEFUNCTION, buf.write)
            
            url = "http://%s.battle.net/api/wow/item/%d?locale=%s" % (region, iid, loc)
            c.setopt(c.URL, url)
            if not QUIET:
                if not showed:
                    print "* get item %d" % iid
                    showed = True               
                print "* retrieve url %s" % url
            c.perform()
            left -= 1

            s = buf.getvalue()
            buf.close()

            if not QUIET:
                print "got data"
                print s
                print "--------------------"
            
            file(fname, "wt").write(s)
#            r = s.replace(':false', ':False').replace(':true', ':True')
#            V = eval(r)
            
    if not QUIET:
        print "* done"
    return
    

if __name__ == '__main__':
    fetch(items_realms)