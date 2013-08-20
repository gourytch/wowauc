#! /usr/bin/env python
# -*- coding: utf-8 -*-
#

import psycopg2

class Pusher (object):
    """
    абстрактный класс для пополнения базы данными по аукционам
    """

    def touch_realm(self, region, realm, slug, locale):
        return True


    def need(self, region, realm, house, wowts):
        """
        проверить, нужно ли добавление данных для данного времени
        """
        return True


    def start(self, region, realm, house, wowts):
        """
        начинаем сессию добавления данных для аукциона
        """
        return Null


    def push(self, lot):
        """
        запихнём данные по лоту в базу
        объект лота - словарь
        """
        return


    def abort(self):
        """
        отмена push-сеанса и откат данных
        """
        return


    def finish(self):
        """
        завершение push-сеанса и коммит данных
        возвращает словарь с краткой статистикой по завершенной сессии
        (количество открытых/закрытых/выкупленных позиций)
        """
        ret = {'push_id':0, 'opened': 0, 'closed': 0, 'success': 0}
        return ret

### EOF ###
