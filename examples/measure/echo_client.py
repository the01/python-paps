# -*- coding: UTF-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

__author__ = "d01"
__email__ = "jungflor@gmail.com"
__copyright__ = "Copyright (C) 2016, Florian JUNG"
__license__ = "MIT"
__version__ = "0.1.0"
__date__ = "2016-04-19"
# Created: 2016-03-14 15:30
""" measure request speed echo client """

import datetime
import time
import Queue

import pytz

from paps.si.app.message import MsgType
from paps import Person
from paps.si.app.sensorClient import SensorClient

from client import WrapperClient


class EchoClient(SensorClient):

    def __init__(self, settings=None):
        super(EchoClient, self).__init__(settings)

    def _packet_loop(self):
        """
        Packet processing loop

        :rtype: None
        """
        while self._is_running:
            # Only wait if there are no more packets in the inbox
            if self.inbox.empty() \
                    and not self.new_packet.wait(self._packet_timeout):
                continue
            ip, port, packet = self.inbox.get()
            if self.inbox.empty():
                self.new_packet.clear()
            self.debug(u"{}".format(packet))

            if packet.header.message_type == MsgType.CONFIG:
                self._do_config_packet(packet, ip, port)
            elif packet.header.message_type == MsgType.UPDATE:
                self._do_update_packet(packet)

    def _do_update_packet(self, packet):
        pass


class WrapperEchoClient(WrapperClient):

    def __init__(self, settings=None):
        super(WrapperEchoClient, self).__init__(settings)
        self._responses = 0
        self._responses_time = datetime.timedelta()
        self._responses_time = 0.0
        self._q = Queue.Queue()
        self._old = None

    def _add_time(self, people):
        self._q.put(time.time())
        self._old(people)

    def _get_person_update(self, packet):
        if self._is_updating:
            try:
                self._responses_time += time.time() - self._q.get(False, 0.1)
                self._responses += 1
            except Queue.Empty:
                pass

    def start(self, blocking=False):
        self.info("()")
        self._client._do_update_packet = self._get_person_update
        self._old = self._client.person_update
        self._client.person_update = self._add_time
        super(WrapperEchoClient, self).start(blocking)

    def stop(self):
        super(WrapperEchoClient, self).stop()
        tot = self._responses_time

        perc = 0.0
        if self._responses:
            perc = tot / self._responses
        self.info(
            u"Received {} echos over {} ({})".format(
                self._responses, tot, perc
            )
        )


def cmd_line(line, ctrl):
    clients = ctrl.modules
    """ :type: list[WrapperEchoClient] """
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
        sc = EchoClient({
            'id': number,
            'listen_bind_ip': clients_host,
            #'multicast_bind_ip': "127.0.0.1",
            'listen_port': clients_port + number
        })
        people = []
        for person_number in range(people_num):
            people.append(Person(id=person_number))
        wrapper = WrapperEchoClient({
            'client': sc,
            'people': people,
            'throttle': throttle
        })
        res.append(wrapper)

    return res, cmd_line
