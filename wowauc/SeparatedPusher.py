#! /usr/bin/env python
# -*- coding: utf-8 -*-
#

import psycopg2

class Pusher (object):
    """
    класс для пополнения базы данными по аукционам
    """

    def __init__ (self, debug=False):
        self.__conn     = None
        self.__csr      = None
        self.__push_id  = None
        self.__sid      = None
        self.__debug    = debug
        return


    def connect(self, dbhost, dbname, dbuser, dbpass):
        """
        соединиться с базой данных
        """
        if self.__debug:
            print "connect to database %s at %s as %s" \
                % (dbname, dbhost, dbuser)
        self.__conn = psycopg2.connect(host=dbhost, database=dbname,
                                       user=dbuser, password=dbpass)
        if self.__debug:
            print "...connected"
        return


    def is_connected(self):
        """
        возвращаем True если соединение с базой данных поизведено
        """
        return self.__conn is not None


    def disconnect(self):
        """
        отсоединиться от базы данных
        """
        if not self.__conn: 
            return
        assert self.__push_id is None, "push session not finished"
        assert self.__csr is None, "cursor still exists"
        if self.__debug:
            print "diconnect from database"
        self.__conn.close()
        self.__conn = None
        if self.__debug:
            print "... diconnected"
        return


    def touch_realm(self, region, realm, slug, locale):
        if self.__debug:
            print "touch realm (%s, %s, %s, %s)" \
                % (region, realm, slug, locale)
        assert self.__conn is not None, "not connected to database"
        cur = self.__conn.cursor()
        cur.execute("SELECT auc.check_realm(%s, %s, %s, %s)", 
            (region, realm, slug, locale))
        self.__conn.commit()
        cur.close()
        return


    def need(self, region, realm, house, wowts):
        """
        проверить, нужно ли добавление данных для данного времени
        """
        assert self.__conn is not None, "not connected to database"
        sid = '%s:%s,%s %s' % (region, realm, house, wowts)
        cur = self.__conn.cursor()
        cur.execute('SELECT auc.push_need(%s, %s, %s, %s)', 
            (region, realm, house, wowts))
        R = cur.fetchone()
        cur.close()
        assert R is not None, "FAILED TO CHECK FINISHED SESSIONS FOR %s" % sid
        if R[0] is None:
            print "... broken %s" % sid
            return False
        elif not R[0]:
            return False
        return True


    def start(self, region, realm, house, wowts):
        """
        начинаем сессию добавления данных для аукциона
        """
        if self.__debug:
            print "start push session for (%s, %s, %s, %s)" \
            % (region, realm, house, wowts)
        assert self.__conn is not None, "not connected to database"
        assert self.__push_id is None, "push session already started"
        assert self.__csr is None, "cursor already exists"
        cur = self.__conn.cursor()
        cur.execute('SELECT auc.push_start(%s, %s, %s, %s)', 
                (region, realm, house, wowts))
        R = cur.fetchone()
        if R is None or R[0] is None:
            cur.close()
            raise Exception("FAILED TO START PUSH SESSION FOR %s" % sid)
        self.__sid = '%s:%s,%s %s' % (region, realm, house, wowts)
        self.__csr = cur
        self.__push_id = R[0]
        # с этого момента надо иметь ввиду, 
        # что у нас может быть активна сессия загрузки данных
        return self.__push_id


    def is_started(self):
        """
        возвращаем True если активен сеанс добавления данных
        """
        return self.__conn is not None and self.__csr is not None 


    def push(self, lot):
        """
        запихнём данные по лоту в базу
        объект лота - словарь
        """
        assert type(lot) is dict, "lof is not a dict but %s" % type(lot)
        assert self.__conn is not None, "not connected to database"
        assert self.__csr is not None, "push session not started"
        assert self.__push_id is not None, "push session not started"
        self.__csr.execute(
            "SELECT auc.push_lot(%s, %s, %s, %s, %s, %s, %s, %s);",
            (self.__push_id, 
                lot['auc'], lot['item'], lot['owner'],
                lot['bid'], lot['buyout'],
                lot['quantity'], lot['timeLeft']))
        R = self.__csr.fetchone()
        if R is None or not R[0]:
            print "lot %d failed to push for %s" % (lot['auc'], self.__sid)
        return


    def abort(self):
        """
        отмена push-сеанса и откат данных
        """
        if self.__debug:
            print "abort push session"
        assert self.__conn is not None, "not connected to database"
        assert self.__csr is not None, "push session not started"
        assert self.__push_id is not None, "push session not started"
        self.__csr.rollback()
        self.__csr.close()
        self.__csr = None
        self.__push_id = None
        self.__sid = None


    def finish(self):
        """
        завершение push-сеанса и коммит данных
        возвращает словарь с краткой статистикой по завершенной сессии
        (количество открытых/закрытых/выкупленных позиций)
        """
        assert self.__conn is not None, "not connected to database"
        assert self.__csr is not None, "push session not started"
        assert self.__push_id is not None, "push session not started"

        if self.__debug:
            print "finish push session"

        pid = self.__push_id # сохраним потому что в abort-е поля сбросятся
        sid = self.__sid
        self.__csr.execute('SELECT auc.push_finish(%s)', (self.__push_id,))
        R = self.__csr.fetchone()
        if R is None or not R[0]:
            self.abort();
            raise Exception("FAILED TO FINISH PUSH SESSION %d FOR %s" % 
                (pid, sid))
        self.__csr.execute('SELECT num_open, num_closed, num_success ' +
            'FROM auc.push_results WHERE push_id = %s', (self.__push_id,))
        R = self.__csr.fetchone()
        self.__conn.commit()
        self.__csr.close()
        self.__csr = None
        self.__push_id = None
        self.__sid = None

        ret = {'push_id':pid, 'opened': R[0], 'closed': R[1], 'success': R[2]}
        if self.__debug:
            print "... session finished, results: %s" % ret
        return ret

### EOF ###
