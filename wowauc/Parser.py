#! /usr/bin/env python
# -*- coding: utf-8 -*-
#

import psycopg2, re, datetime, sys, os, os.path, glob

class Parser(object):

    def __init__(self, pusher, region='eu', locale='en_US', debug=False):
        self.__pusher = pusher
        self.__region = region
        self.__locale = locale
        self.__debug  = debug
        return


    def push_dict(self, ts, data):
        """
        старый простой но многожрущий метод:
        eval-им объект из снапшота, потом пробегаем по нему и пушим
        """
        realm = data['realm']['name']
        slug  = data['realm']['slug']
        self.__pusher.touch_realm(self.__region, realm, slug, self.__locale)
        for fraction in ('alliance', 'horde', 'neutral'):
            c = fraction[0].upper()
            if not self.__pusher.need(self.__region, realm, c, ts):
                continue
            pid = self.__pusher.start(self.__region, realm, c, ts)
            for lot in data[fraction]['auctions']:
                self.__pusher.push(lot)
            self.__pusher.finish()
        return


    def thrifty_push(self, ts, fobj):
        """
        более бережливый до памяти вариант:
        парсим файл построчно, eval-им что нужно
        заливаем в базу
        """

        rx_realm = re.compile(r'^"realm":(\{.*\}),$')
        rx_start_auc = re.compile(r'^"([^"]+)":\{"auctions":\[$')
        rx_lot = re.compile(r'^\s*(\{"auc":.*?"\})(|\]\},?|,)$')
        rx_end = re.compile(r'^\}$')

        realm = None
        slug  = None
        house = None

        while True:
            s = fobj.readline()
            if not len(s):
                break # закончился файл - заканчиваем работу
            s = s.strip()

            if not s: # пустая строчка
                continue 

            if s == '{': # открытие данных
                continue 

            # "realm":{"name":"Fordragon","slug":"fordragon"},
            r = rx_realm.search(s)
            if r:
                v = eval(r.group(1))
                realm = v['name']
                slug  = v['slug']
                self.__pusher.touch_realm(self.__region, realm, slug, self.__locale)
                continue # переходим к следующей строчке

            #"alliance":{"auctions":[
            r = rx_start_auc.search(s)
            if r:
                house = r.group(1)
                c = house[0].upper()
                if self.__pusher.need(self.__region, realm, c, ts):
                    self.__pusher.start(self.__region, realm, c, ts)
                elif self.__debug:
                    print "skip %s @ %s" % (realm, ts)
                continue # следующие строчки - данные аукционного дома


            #{"auc":1649217884,"item":25043,"owner": ... "timeLeft":"VERY_LONG"},
            r = rx_lot.search(s)
            if r:
                if self.__pusher.is_started():
                    v = eval(r.group(1))
                    self.__pusher.push(v)
                if r.group(2) != ',': # последний лот AH
                    if self.__pusher.is_started():
                        self.__pusher.finish()
                    house = None
                continue

            r = rx_end.search(s)
            if r:
                break;

            print "? %s" % s
        return


    def parse_file(self, fname):
        rx = re.search(r'.*/(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})(?:_(.+)_(.+)|)\.json$', fname)
        assert rx, "fname not match: %s" % fname
        ts = rx.group(1) + "-" + rx.group(2) + "-" + rx.group(3) + " " \
           + rx.group(4) + ":" + rx.group(5) + ":" + rx.group(6)
        if rx.group(7):
            self.__region = rx.group(7)
        realm = rx.group(8) or 'Fordragon'
        fobj = open(fname, 'rt')
        print 'process data for ts=%s' % ts
        self.thrifty_push(ts, fobj)
        fobj.close()
