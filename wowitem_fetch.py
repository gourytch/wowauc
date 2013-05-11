#! /usr/bin/env python
# -*- coding: utf-8 -*-
#

import pycurl
import cStringIO
import time
import os.path
import sys
import anydbm
import re
import glob
import shutil

exec file("wowauc.conf", "rt").read()

#if ("item_locales" not in dir()):
#    item_locales = "en_US ru_RU"

ids = file(items_ids, "rt").read().split()
locales = items_locales.split()


CURDIR = os.path.dirname(os.path.abspath(__file__)) + "/"
SAVEDIR = CURDIR + dir_fetched_items + "/"
DBFILE = re.sub(r"/+$", "", os.path.abspath(SAVEDIR)) + ".anydbm"

QUIET   = '-q' in sys.argv

db = None # value will initialized in init_d()

class FS_Base:
    
    def __init__(self, basedir):
        self.open(basedir)
        return
        
    def open(self, basedir):
        self.basedir = basedir
        return
        
        
    def close(self):
        return
    
        
    def has_item(self, id, loc):
        if type(id) not in (int, long): id = int(id)
        fname = "%s/%06d-%s.json" % (self.basedir, id, loc)
        return os.path.exists(fname)


    def put(self, id, loc, json):
        if type(id) not in (int, long): id = int(id)
        fname = "%s/%06d-%s.json" % (self.basedir, id, loc)
        file(fname, "wt").write(json)


    def get(self, id, loc):
        if not self.has_item(id, loc): return None
        if type(id) not in (int, long): id = int(id)
        fname = "%s/%06d-%s.json" % (self.basedir, id, loc)
        return file(fname, "rt").read()


    def keys(self):
        x = re.compile(r".*/(\d+)-(\w+)\.json$")
        R = []
        for k in glob.glob("%s/*.json" % self.basedir):
            rx = x.search(k)
            if not rx:
                print "BAD KEY: {%s}" % k
                continue
            R.append({'id': int(rx.group(1)), 'loc': rx.group(2)})
        return R

###
   
class D_Base:
    
    
    def __init__(self, dbfile):
        self.open(dbfile)
        return
        

    def backup_file(self):
        S = ('.5','.4','.3','.2','.1', '')
        for i in range(len(S) - 1):
            dst = self.fname + S[i]
            src = self.fname + S[i + 1]
            if os.path.exists(src):
                if os.path.exists(dst):
                    remove(dst)
                if src == self.fname:
                    shutil.copy2(src, dst)
                else:
                    shutil.move(src, dst)
        return
    
    
    def open(self, fname):
        self.fname = fname
        self.backup_file()
        self.db = anydbm.open(self.fname, "c", 0666)
        return


    def close(self):
        self.db.sync()
        self.db.close()
        return
    
    
    def has_item(self, id, loc):
        if type(id) not in (int, long): id = int(id)
        key ="%06d-%s" % (id, loc)
        return self.db.has_key(key)


    def put(self, id, loc, json):
        if type(id) not in (int, long): id = int(id)
        key ="%06d-%s" % (id, loc)
        self.db[key] = json
#        self.db.sync()
        return


    def get(self, id, loc):
        if type(id) not in (int, long): id = int(id)
        key ="%06d-%s" % (id, loc)
        return self.db.get(key, None)


    def keys():
        x = re.compile(r"^(\d{6})-(\w+)$")
        R = []
        for k in self.db.keys():
            rx = x.search(k)
            if not rx:
                print "BAD KEY: {%s}" % k
                continue
            R.append({'id': int(rx.group(1)), 'loc': rx.group(2)})
        return R
    
####################################################################


def baseUpdate(src, dst):
    n_copied = 0
    n_processed = 0
    for R in src.keys():
        id = R['id']
        loc = R['loc']
        if dst.has_item(id, loc):
            print "%06d-%-6s skipped" % (id, loc)
        else:
            print "%06d-%-6s stored" % (id, loc)
            dst.put(id, loc, src.get(id, loc))
            n_copied += 1
        n_processed += 1
    print "done. processed: %d, copied: %d" % (n_processed, n_copied)
    return


def dumphdr(hdr):
    if QUIET: return
    print "%% got headers: %s" % repr(hdr)
    return


def fetch(region, db):
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
            if db.has_item(iid, loc):
                #fname = "%s/%06d-%s.json" % (SAVEDIR, iid, loc)
                #if os.path.exists(fname):
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
            
            db.put(iid, loc, s)
            #file(fname, "wt").write(s)
#            r = s.replace(':false', ':False').replace(':true', ':True')
#            V = eval(r)
            
    if not QUIET:
        print "* done"
    return
    

if __name__ == '__main__':
    if False:
        print "open old base"
        db_old= FS_Base(SAVEDIR)
        print "open new base"
        db = D_Base(DBFILE)
        print "update new base"
        baseUpdate(db_old, db)
        db_old.close()
        db.close()
        sys.exit(0)
    
    db = D_Base(DBFILE)
    print "fetch new items to new base"
    fetch(items_realms, db)
    db.close()
    print "done"
