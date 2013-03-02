#! /usr/bin/env python
# -*- coding: utf-8 -*-
#

import psycopg2, re, datetime, sys, os, os.path, glob

exec file("wowauc.conf", "rt").read()

CURDIR = os.path.dirname(os.path.abspath(__file__)) + "/"

SRCDIR  = CURDIR + dir_fetched + "/"
TMPDIR  = CURDIR + dir_importing + "/"
DSTDIR  = CURDIR + dir_imported + "/"

conn    = None

def conn_open():
    global conn
    conn = psycopg2.connect(host=dbhost, database=dbname,
                            user=dbuser, password=dbpass)

def conn_close():
    global conn
    conn.close()


def push_data(f_region, f_realm, ts, data):
    global conn
    if conn is None:
        conn_open()
    cur = conn.cursor()
    realm = data['realm']['name']
    slug  = data['realm']['slug']

    cur.execute("SELECT auc.check_realm(%s, %s, %s, %s)", (
        f_region, realm, slug, 'en_US'))
    conn.commit()

    for fraction in ('alliance', 'horde', 'neutral'):
        c = fraction[0].upper()
        sid = '%s:%s,%s %s' % (f_region, realm, c, ts)
        cur.execute('SELECT auc.push_need(%s, %s, %s, %s)', (
            f_region, realm, c, ts))
        R = cur.fetchone()
        assert R is not None, "FAILED TO CHECK FINISHED SESSIONS FOR %s" % sid
        if R[0] is None:
            print "... broken %s" % sid
            continue
        elif not R[0]:
            print "... skip %s" % sid
            continue
        print "... import %s ..." % sid

        cur.execute('SELECT auc.push_start(%s, %s, %s, %s)', (
            f_region, realm, c, ts))
        R = cur.fetchone()
        assert R is not None, "FAILED TO START PUSH SESSION FOR %s" % sid

        push_id = R[0]
        print "...... push_session #%d" % push_id;
        for lot in data[fraction]['auctions']:
            cur.execute("SELECT auc.push_lot(%s, %s, %s, %s, %s, %s, %s, %s);",
            (push_id, lot['auc'], lot['item'], lot['owner'],
             lot['bid'], lot['buyout'],
             lot['quantity'], lot['timeLeft']))
            R = cur.fetchone()
            if R is None or not R[0]:
                print "lot %d failed to push" % lot['auc']
        cur.execute('SELECT auc.push_finish(%s)', (push_id,))
        R = cur.fetchone()
        assert R is not None, "FAILED TO FINISH PUSH SESSION FOR %s" % sid
        if not R[0]:
            print "failed to push_finish for #%d" %  push_id
        conn.commit()
        cur.execute('SELECT num_open, num_closed, num_success ' +
                    'FROM auc.push_results WHERE push_id = %s', (push_id,))
        R = cur.fetchone()
        print "....... success. lots opened:%d, closed:%s, bought:%d" % R
    cur.close()
    return


def push_file(fname):
    rx = re.search(r'/(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})(?:_(.+)_(.+)|)\.json', fname)
    assert rx, "fname not match"
    ts = rx.group(1) + "-" + rx.group(2) + "-" + rx.group(3) + " " \
       + rx.group(4) + ":" + rx.group(5) + ":" + rx.group(6)
    region = rx.group(7) or 'eu'
    realm = rx.group(8) or 'Fordragon'
    text = file(fname, 'rt').read()
    assert text, 'empty data from file %s' % fname
    data = eval(text)
    print 'process data for ts=%s' % ts
    push_data(region, realm, ts, data)



if __name__ == '__main__':
    conn_open()
    for fname in sorted(glob.glob(SRCDIR + '*.json')):
        tname = TMPDIR + os.path.basename(fname)
        dname = DSTDIR + os.path.basename(fname)
        os.rename(fname, tname)
        push_file(tname)
        os.rename(tname, dname)
#        break
    conn_close()
    print "done"
