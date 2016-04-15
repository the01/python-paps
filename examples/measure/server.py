# -*- coding: UTF-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

__author__ = "d01"
__email__ = "jungflor@gmail.com"
__copyright__ = "Copyright (C) 2015-16, Florian JUNG"
__license__ = "MIT"
__version__ = "0.1.1"
__date__ = "2016-04-15"
# Created: 2015-09-20 05:59
""" measure request speed server """

import multiprocessing as mp
import threading
import time
from pprint import pformat

from flotils import Logable
from flotils.runable import StartStopable

from paps.si.app.sensorServer import SensorServer
from paps.changeInterface import ChangeInterface


class MeasureServer(SensorServer):

    def __init__(self, settings=None):
        super(MeasureServer, self).__init__(settings)
        self.stat_packet_count = mp.Value('i', 0)
        self.stat_packet_times = []

    def _do_packet(self, packet, ip, port):
        with self.stat_packet_count.get_lock():
            self.stat_packet_count.value += 1
            self.stat_packet_times.append(time.time())
        super(MeasureServer, self)._do_packet(packet, ip, port)


class WrapperServer(Logable, StartStopable, ChangeInterface):

    def __init__(self, settings=None):
        if settings is None:
            settings = {}
        super(WrapperServer, self).__init__(settings)
        self.server = settings['server']
        """ server
            :type server: MeasureServer """
        self._stat_lock = threading.Lock()
        self._stat = {}
        self.stat_gather = False

    def statistic(self):
        with self.server.stat_packet_count.get_lock():
            packets = self.server.stat_packet_count.value
            diffs = []
            ts = self.server.stat_packet_times
            for i in range(len(ts)):
                if i > 0:
                    diffs.append(ts[i] - ts[i - 1])
            if diffs:
                avg = sum(diffs) / len(diffs)
            else:
                avg = None
        with self._stat_lock:
            res = u"Gathering: {}\n{}".format(
                self.stat_gather, pformat(self._stat)
            )
            res += u"\nPackets: {}\n{} Packets/Sec - {} Sec/Packets".format(
                packets,
                round(1 / avg) if avg else "N/A", avg if avg else "N/A"
            )
            res += u"\nInbox: {}".format(self.server.inbox.qsize())
            return res

    def statistic_reset(self):
        with self._stat_lock:
            self._stat = {}
            with self.server.stat_packet_count.get_lock():
                self.server.stat_packet_count.value = 0
                self.server.stat_packet_times = []
            self.info("Statistic reset")

    def _format(self, source, people):
        return u"{}: {}".format(
            source, [u"{}".format(person) for person in people]
        )

    def on_person_new(self, people):
        self.info(self._format("NEW", people))
        with self._stat_lock:
            for person in people:
                device, seat = person.id.split(".")
                self._stat.setdefault(device, {})[seat] = 0

    def on_person_update(self, people):
        if self.stat_gather:
            with self._stat_lock:
                for person in people:
                    device, seat = person.id.split(".")
                    try:
                        self._stat[device][seat] += 1
                    except KeyError:
                        self._stat['after'] = self._stat.get('after', 0) + 1
        else:
            self.info(self._format("UPDATE", people))

    def on_person_leave(self, people):
        self.info(self._format("LEAVE", people))

    def start(self, blocking=False):
        self.server.start(False)
        super(WrapperServer, self).start(blocking)

    def stop(self):
        self.server.stop()
        super(WrapperServer, self).stop()


def cmd_line(line, ctrl):
    server = ctrl.modules[0]
    """ :type : StartServer """
    if line == "statistic start":
        server.stat_gather = True
    elif line == "statistic stop":
        server.stat_gather = False
    elif line == "statistic reset":
        server.statistic_reset()
    elif line == "statistic":
        server.info(u"Statistic: \n{}".format(server.statistic()))
    return line


def create(host, port):
    """
    Prepare server to execute

    :return: Modules to execute, cmd line function
    :rtype: list[WrapperServer], callable | None
    """
    wrapper = WrapperServer({
        'server': None
    })
    d = {
        'listen_port': port,
        'changer': wrapper
    }
    if host:
        d['listen_bind_ip'] = host

    ses = MeasureServer(d)
    wrapper.server = ses
    return [wrapper], cmd_line
