#! /usr/bin/env python
# -*- coding: utf-8 -*-
#

import pycurl
import cStringIO
import time
import os.path
import sys


exec file("wowauc.conf", "rt").read()

CURDIR = os.path.dirname(os.path.abspath(__file__)) + "/"

TMPDIR  = CURDIR + dir_fetching + "/"
SAVEDIR = CURDIR + dir_fetched + "/"

QUIET   = '-q' in sys.argv

def dumphdr(hdr):
    if QUIET: return
    print "%% got headers: %s" % repr(hdr)
    return


class Writer(object):

    def __init__(self, fname):
        object.__init__(self)
        self._fname = fname
        if not QUIET:
            print "+ open %s" % self._fname
        self._file = open(self._fname, "wt")
        self._count = 0
        self._gzipped = False
        self._data = ''
        return

    def header(self, s):
        if not QUIET:
            print "+ got header: {%s}" % repr(s)
        k = [x.strip() for x in s.split(':')]
        if len(k) < 2:
            return
        if k[0] == 'Content-Encoding':
            self._gzipped = (k[1] == 'gzip')
            if not QUIET:
                print "+ encoding: %s" % k[1]
        return

    def write(self, data):
        n = len(data)
        self._count += n
#        if not QUIET:
#            s = "+ %d bytes received " % self._count
            # sys.stdout.write("%s%s" % (s, '\b' * len(s)))
#            sys.stdout.write("%s  \r" % s)
        self._file.write(data)
        self._data += data
        return

    def close(self):
        if not QUIET:
            print "\n+ close stream. %d octets wrote" % self._count
        self._file.close()
        return

    def getData(self):
        return self._data

def fetch(region, realm):
    if not QUIET:
        print "* fetch for region=%s, realm=%s" % (region, realm)
    buf = cStringIO.StringIO()
    c = pycurl.Curl()

    c.setopt(c.WRITEFUNCTION, buf.write)
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

    if not QUIET:
        print "* retrieve auction url"
    c.setopt(c.URL, "http://%s.battle.net/api/wow/auction/data/%s" % (region, realm))
    c.perform()

    s = buf.getvalue()
    buf.close()

    if not QUIET:
        print "got data"
        print s
        print "--------------------"

    M   = eval(s)
    if M.get('status') == 'nok':
        if not QUIET:
            print "* wowapi does not known about %s:%s" % (region, realm)
        return
    url = M['files'][0]['url']
    t_s = M['files'][0]['lastModified'] / 1000.0
    t_gm = time.gmtime(t_s)
    t_lo = time.localtime(t_s)

    name  = "%s_%s_%s.json" \
        % (time.strftime(r"%Y%m%d_%H%M%S", t_gm), region, realm)
    tname = TMPDIR + name
    sname = SAVEDIR + name
    ts_gm = time.strftime(r"%Y-%m-%d %H:%M:%S", t_gm)
    ts_lo = time.strftime(r"%Y-%m-%d %H:%M:%S", t_lo)

    if not QUIET:
        d_h = int(time.time() - t_s)
        d_s = d_h % 60
        d_h /= 60
        d_m = d_h % 60
        d_h /= 60
        print "* timestamp: %s" % ts_gm
        print "* tocaltime: %s" % ts_lo
        print "*       age: %d:%02d:%02d" % (d_h, d_m, d_s)

    if not (os.path.exists(tname) or os.path.exists(sname)):
        if not QUIET:
            print "* save to %s" % tname
            print "* retrieve aution data"
        c.setopt(c.URL, url)
        c.setopt(c.CONNECTTIMEOUT, 15)
        c.setopt(c.TIMEOUT, 300)
        c.setopt(c.ENCODING, 'gzip')
        c.setopt(c.FOLLOWLOCATION, True)
        f = Writer(tname)
        c.setopt(c.WRITEFUNCTION, f.write)
        c.setopt(c.HEADERFUNCTION, f.header)
        c.perform()
        retcode = c.getinfo(pycurl.HTTP_CODE)
        c.close()
        f.close()
        if not QUIET:
            print "* retcode=%d" % retcode
        if retcode == 200:
            if not QUIET:
                print "* good retcode. rename results to %s" % sname
            os.rename(tname, sname)
            if not QUIET:
                print "* ...moved"
        else:
            if not QUIET:
                print "* retrieved data:"
                print file(tname).read()
                print "* erase results"
            os.remove(tname)
    else:
        if not QUIET:
            print "* skip"

    if not QUIET:
        print "* done"

if __name__ == '__main__':
    for item in watchlist.split():
        (region, realm) = item.split(':')
        fetch(region, realm)