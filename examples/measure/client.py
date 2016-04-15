# -*- coding: UTF-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

__author__ = "d01"
__email__ = "jungflor@gmail.com"
__copyright__ = "Copyright (C) 2015-16, Florian JUNG"
__license__ = "MIT"
__version__ = "0.1.0"
__date__ = "2016-04-15"
# Created: 2015-09-20 05:49
""" measure request speed client """

import thread
import time

from flotils.runable import StartStopable
from flotils import Logable

from paps import Person
from paps.si.app.sensorClient import SensorClient


class MeasureClient(SensorClient):

    def __init__(self, settings=None):
        super(MeasureClient, self).__init__(settings)


class WrapperClient(Logable, StartStopable):

    def __init__(self, settings=None):
        if settings is None:
            settings = {}
        super(WrapperClient, self).__init__(settings)
        self._client = settings['client']
        """ client
            :type : audience.si.app.sensor_client.SensorClient """
        self._people = settings['people']
        self.throttle = settings['throttle']
        """ Number of requests per second (0 -> no throttle)
            :type : int """
        self._id = self._client._id
        self._is_updating = False
        self._requests = 0
        self._thread = None

    def _make_person_update(self):
        start = time.time()
        self._requests = 0
        spr = rps = 0.0
        timeout = 0.0
        diff = 0.0

        while self._is_running and self._is_updating:
            self._people = [
                Person(id=person.id, sitting=not person.sitting)
                for person in self._people
            ]
            self._client.person_update(self._people)
            self._requests += 1
            # time.sleep(0.3)
            diff = time.time() - start
            if diff == 0:
                continue
            spr = round(diff / self._requests, 2)
            rps = round(self._requests / diff, 2)
            if self.throttle and abs(rps - self.throttle) > 5:
                # got a throttle and current speed deviates more than 5 Req/s
                dst_spr = 1 / self.throttle
                t_diff = dst_spr - spr
                timeout = max(0, timeout + t_diff)
                # self.info(u"{}, {}, {}".format(dst_spr, t_diff, timeout))
                time.sleep(timeout)

        self.info(
            u"Made {} updates in ".format(self._requests) +
            u"{} sec ({} Req/Sec - {} Sec/Req (timeout: {})".format(
                round(diff, 2), rps, spr, timeout
            )
        )
        self._thread = None

    def updating_start(self):
        if self._thread is None:
            self.info("Starting thread")
            self._is_updating = True
            try:
                thread.start_new_thread(
                    self._make_person_update, ()
                )
            except:
                self.exception("Failed to start thread")

    def updating_stop(self):
        self._is_updating = False

    def start(self, blocking=False):
        self._client.start(False)
        time.sleep(0.5)
        self._client.join(self._people)
        super(WrapperClient, self).start(blocking)

    def stop(self):
        self.updating_stop()
        try:
            self._client.unjoin()
        finally:
            self._is_running = False
            self._client.stop()
            super(WrapperClient, self).stop()


def cmd_line(line, ctrl):
    clients = ctrl.modules
    """ :type: list[WrapperClient] """
    if line == "update start":
        for client in clients:
            client.updating_start()
    elif line == "update stop":
        for client in clients:
            client.updating_stop()
    return line


def create(clients_num, clients_host, clients_port, people_num, throttle):
    """
    Prepare clients to execute

    :return: Modules to execute, cmd line function
    :rtype: list[WrapperClient], (str, object) -> str | None
    """
    res = []
    for number in range(clients_num):
        sc = MeasureClient({
            'id': number,
            'listen_bind_ip': clients_host,
            #'multicast_bind_ip': "127.0.0.1",
            'listen_port': clients_port + number
        })
        people = []
        for person_number in range(people_num):
            people.append(Person(id=person_number))
        wrapper = WrapperClient({
            'client': sc,
            'people': people,
            'throttle': throttle
        })
        res.append(wrapper)

    return res, cmd_line
