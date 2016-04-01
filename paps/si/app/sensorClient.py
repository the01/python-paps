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
__date__ = "2016-03-29"
# Created: 2015-03-21 24:00

import time
import threading

from .sensor import Sensor
from ..sensorInterface import SensorClientInterface, \
    SensorUpdateException, SensorJoinException, SensorStartException
from .message import MsgType, Id, \
    APPJoinMessage, APPUnjoinMessage, APPUpdateMessage, \
    format_data


class SensorClient(Sensor, SensorClientInterface):
    """ APP sensor client """

    def __init__(self, settings=None):
        if settings is None:
            settings = {}
        super(SensorClient, self).__init__(settings)
        self._packet_timeout = settings.get('packet_wait_timeout', 1.5)
        """ Time to wait for new packet event """
        self._start_block_timeout = max(
            self._packet_timeout, self._select_timeout
        )
        """ Time to block in start """
        self._join_retry_timeout = settings.get('join_retry_timeout', 5.0)
        """ Time to wait before resending join packet """
        self._join_retry_count = settings.get('join_retry_number', 3)
        """ Number of times to try to join before failing """

        self._server_ip = None
        """ Ip of server
            :type : None | str """
        self._server_port = None
        """ Port of server
            :type : None | int """
        self._joined = threading.Event()
        """ If set, currently joined the audience """

    def join(self, people):
        """
        Join the local audience
        (a config message should be received on success)
        Validates that there are people to join and that each of them
        has a valid unique id

        :param people: Which people does this sensor have
        :type people: list[paps.person.Person]
        :rtype: None
        :raises SensorJoinException: Failed to join
        """
        tries = 0
        if not people:
            raise SensorJoinException("No people given")
        ids = set()
        for person in people:
            if not person.id and person.id != 0:
                raise SensorJoinException("Invalid id for one or more people")
            if person.id in ids:
                raise SensorJoinException(
                    u"Id {} not unique".format(person.id)
                )
            ids.add(person.id)

        while self._is_running and tries < self._join_retry_count:
            packet = APPJoinMessage(
                payload={'people': [person.to_dict() for person in people]}
            )
            self._send_packet(self._multicast_group, self._multicast_port,
                              packet)
            if self._joined.wait(self._join_retry_timeout):
                break
            with self._seq_ack_lock:
                # Got ack for packet?
                packet_ackd = packet.header.sequence_number \
                    not in self._seq_ack
            if packet_ackd and self._joined.wait(1.0):
                # Packet already got acked
                # -> wait another second for ._joined to clear
                break
            tries += 1
            self.warning(
                u"Unsuccessful attempt joining audience # {}".format(tries)
            )

        if not self._joined.is_set() or tries >= self._join_retry_count:
            # Failed to join (no config packet received)
            raise SensorJoinException("No config packet received")
        self.info("Joined the audience")

    def unjoin(self):
        """
        Leave the local audience

        :rtype: None
        :raises SensorJoinException: Failed to leave
        """
        self.debug("()")
        if self._joined.is_set():
            packet = APPUnjoinMessage(device_id=Id.NOT_SET)
            self._send_packet(self._server_ip, self._server_port, packet)
            self._joined.clear()
            self.info("Left the audience")

    def config(self, settings):
        """
        Configuration has changed - config this module and lower layers
        (calls on_config - if set)

        :param settings: New configuration
        :type settings: dict
        :rtype: None
        :raises SensorUpdateException: Failed to update
        """
        self.debug("()")
        # TODO synchronize access to vars
        try:
            self._device_id = settings['device_id']

            self._packet_timeout = settings.get(
                'packet_wait_timeout',
                self._packet_timeout
            )
            self._server_ip = settings.get('server_ip', self._server_ip)
            self._server_port = settings.get('server_port', self._server_port)
        except KeyError:
            raise SensorUpdateException("Key not in settings")

        if callable(self.on_config):
            try:
                self.on_config(settings)
            except:
                self.exception("Failed to update remote config")
                raise SensorUpdateException("Remote config failed")

    def person_update(self, people):
        """
        Update the status of people

        :param people: All people of this sensor
        :type people: list[paps.person.Person]
        :rtype: None
        :raises SensorUpdateException: Failed to update
        """

        packet = APPUpdateMessage(device_id=Id.NOT_SET, people=people)
        self._send_packet(
            self._server_ip, self._server_port, packet,
            acknowledge_packet=False
        )

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

    def _do_config_packet(self, packet, ip, port):
        """
        Apply config to this instance

        :param packet: Packet with config
        :type packet: paps.si.app.message.APPMessage
        :param ip: Ip of server
        :type ip: str
        :param port: Port of server
        :type port: int
        :rtype: None
        """
        self.debug("()")
        if packet.header.device_id != Id.SERVER:
            # Only allow config packets from server
            self.warning("Config packets only allowed from server")
            return

        try:
            config = packet.payload
            self.debug(u"{}".format(config))

            if not isinstance(config, dict):
                self.error("Wrong payload type")
                raise RuntimeError("Wrong type")
            config.setdefault("server_ip", ip)
            config.setdefault("server_port", port)
            self.config(config)
            self._joined.set()
        except:
            self.exception("Failed to configure")
            self.error(u"Faulty packet {}".format(format_data(packet.payload)))
            return

    def start(self, blocking=False):
        """
        Start the interface

        :param blocking: Should the call block until stop() is called
            (default: False)
        :type blocking: bool
        :rtype: None
        :raises SensorStartException: Failed to start
        """
        self.debug("()")
        super(SensorClient, self).start(blocking=False)
        try:
            a_thread = threading.Thread(
                target=self._thread_wrapper,
                args=(self._packet_loop,)
            )
            a_thread.daemon = True
            a_thread.start()
        except:
            self.exception("Failed to run packet loop")
            raise SensorStartException("Packet loop failed")
        self.info("Started")
        # Blocking - call StartStopable.start
        super(Sensor, self).start(blocking)

    def stop(self):
        """
        Stop the interface

        :rtype: None
        """
        self.debug("()")
        try:
            self.unjoin()
            time.sleep(2)
        except:
            self.exception("Failed to leave audience")
        super(SensorClient, self).stop()
