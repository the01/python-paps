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
__date__ = "2016-03-31"
# Created: 2015-03-21 24:00

import socket
import platform
import threading

from ..sensorInterface import SensorServerInterface, \
    SensorStartException
from .sensor import Sensor
from .message import Id, MsgType, \
    ProtocolViolation, APPConfigMessage, APPMessage
from ...person import Person


class SensorServer(Sensor, SensorServerInterface):
    """ APP sensor server """

    def __init__(self, settings=None):
        if settings is None:
            settings = {}
        super(SensorServer, self).__init__(settings)
        self._device_id = Id.SERVER
        self._packet_wait = settings.get("packet_wait_timeout", 1.5)
        """ Wait for a packet wait time
        :type _packet_wait: float """
        self._multicast_bind_port = settings.get(
            "multicast_bind_port",
            self._multicast_port
        )
        """ Listen at port for multicast messages
            :type : int """
        self._clients = {}
        """ Map of registered clients """
        self._key2deviceId = {}
        """ key (ip:port) -> device_id lookup
        :type : dict[unicode, unicode] """
        # TODO sync access to clients

        self._multicast_socket = None
        """ Socket listening for multicast messages
            :type : socket.socket """
        # Use event additionally to is_running to wait on it
        self._is_stopped = threading.Event()
        """ Class is stopping event """

    def _packet_loop(self):
        """
        Loop (while running) the inbox and handle incoming packages

        :rtype: None
        """
        while not self._is_stopped.is_set():
            if self.inbox.empty() and \
                    not self.new_packet.wait(self._packet_wait):
                continue
            ip, port, packet = self.inbox.get()

            if self.inbox.empty():
                self.new_packet.clear()

            self._do_packet(packet, ip, port)

    def _do_packet(self, packet, ip, port):
        """
        React to incoming packet

        :param packet: Packet to handle
        :type packet: T >= paps.si.app.message.APPMessage
        :param ip: Client ip address
        :type ip: unicode
        :param port: Client port
        :type port: int
        :rtype: None
        """
        msg_type = packet.header.message_type

        if msg_type == MsgType.JOIN:
            self._do_join_packet(packet, ip, port)
        elif msg_type == MsgType.UNJOIN:
            self._do_unjoin_packet(packet, ip, port)
        elif msg_type == MsgType.UPDATE:
            self._do_update_packet(packet, ip, port)

    def _do_join_packet(self, packet, ip, port):
        """
        React to join packet - add a client to this server

        :param packet: Packet from client that wants to join
        :type packet: paps.si.app.message.APPJoinMessage
        :param ip: Client ip address
        :type ip: unicode
        :param port: Client port
        :type port: int
        :rtype: None
        """
        self.debug("()")
        device_id = packet.header.device_id
        key = u"{}:{}".format(ip, port)

        if device_id == Id.REQUEST:
            device_id = self._new_device_id(key)

        client = self._clients.get(device_id, {})
        data = {}

        if packet.payload:
            try:
                data = packet.payload
            except:
                data = {}

        client['device_id'] = device_id
        client['key'] = key
        people = []
        try:
            for index, person_dict in enumerate(data['people']):
                person = Person()
                person.from_dict(person_dict)
                person.id = u"{}.{}".format(device_id, person.id)
                # To get original id -> id.split('.')[0]
                people.append(person)
            self.changer.on_person_new(people)
        except:
            self.exception("Failed to update people")
            return

        # Original ids (without device id)
        client['people'] = people
        # Add config to client data?
        client_dict = dict(client)
        del client_dict['people']

        self._send_packet(ip, port, APPConfigMessage(payload=client_dict))
        self._clients[device_id] = client
        self._key2deviceId[key] = device_id

    def _do_unjoin_packet(self, packet, ip, port):
        """
        React to unjoin packet - remove a client from this server

        :param packet: Packet from client that wants to join
        :type packet: paps.si.app.message.APPJoinMessage
        :param ip: Client ip address
        :type ip: unicode
        :param port: Client port
        :type port: int
        :rtype: None
        """
        self.debug("()")
        device_id = packet.header.device_id

        if device_id <= Id.SERVER:
            self.error("ProtocolViolation: Invalid device id")
            return
        client = self._clients.get(device_id)
        if not client:
            self.error("ProtocolViolation: Client is not registered")
            return
        key = u"{}:{}".format(ip, port)
        if client['key'] != key:
            self.error(
                u"ProtocolViolation: Client key ({}) has changed: {}".format(
                    client['key'], key
                )
            )
            return

        # Packet info seems ok
        try:
            self.changer.on_person_leave(client['people'])
        except:
            self.exception("Failed to remove people")
            return

        # Forget client?
        del self._clients[device_id]
        del self._key2deviceId[key]
        del client

    def _do_update_packet(self, packet, ip, port):
        """
        React to update packet - people/person on a device have changed

        :param packet: Packet from client with changes
        :type packet: paps.si.app.message.APPUpdateMessage
        :param ip: Client ip address
        :type ip: unicode
        :param port: Client port
        :type port: int
        :rtype: None
        """
        self.debug("()")
        device_id = packet.header.device_id
        if device_id <= Id.SERVER:
            self.error("ProtocolViolation: Invalid device id")
            return
        client = self._clients.get(device_id, None)
        if not client:
            self.error("ProtocolViolation: Client is not registered")
            return
        key = u"{}:{}".format(ip, port)
        if client['key'] != key:
            self.error(
                u"ProtocolViolation: Client key ({}) has changed: {}".format(
                    client['key'], key
                )
            )
            return

        # Packet info seems ok
        try:
            people = packet.people()
        except ProtocolViolation:
            self.exception("Failed to decode people from packet")
            return

        # Verify same number of people in update as registered to client
        # (APP specific)
        if len(people) != len(client['people']):
            self.error("ProtocolViolation: Incorrect number of people updated")
        changed = []
        # Add ids to all people
        # Assumes same order here as on the client (e.g from the join())
        for index, person in enumerate(people):
            old = client['people'][index]
            person.id = old.id
            if person != old:
                old.sitting = person.sitting
                # Maybe sent person to protect access to local saved state
                changed.append(old)
        if changed:
            # Only update if there is really a change
            try:
                self.changer.on_person_update(changed)
            except:
                self.exception("Failed to notify people update")
                return
        else:
            self.debug("No people updated")

    def _new_device_id(self, key):
        """
        Generate a new device id or return existing device id for key

        :param key: Key for device
        :type key: unicode
        :return: The device id
        :rtype: int
        """
        device_id = Id.SERVER + 1
        if key in self._key2deviceId:
            return self._key2deviceId[key]
        while device_id in self._clients:
            device_id += 1
        return device_id

    def _init_multicast_socket(self):
        """
        Init multicast socket

        :rtype: None
        """
        self.debug("()")
        # Create a UDP socket
        self._multicast_socket = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM
        )

        # Allow reuse of addresses
        self._multicast_socket.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            1
        )

        # Set multicast interface to local_ip
        self._multicast_socket.setsockopt(
            socket.IPPROTO_IP,
            socket.IP_MULTICAST_IF,
            socket.inet_aton(self._multicast_ip)
        )

        # Set multicast time-to-live
        # Should keep our multicast packets from escaping the local network
        self._multicast_socket.setsockopt(
            socket.IPPROTO_IP,
            socket.IP_MULTICAST_TTL,
            self._multicast_ttl
        )

        self._add_membership_multicast_socket()
        # Bind socket
        if platform.system().lower() == "darwin":
            self._multicast_socket.bind(("0.0.0.0", self._multicast_bind_port))
        else:
            self._multicast_socket.bind(
                (self._multicast_ip, self._multicast_bind_port)
            )
        self._listening.append(self._multicast_socket)

    def _shutdown_multicast_socket(self):
        """
        Shutdown multicast socket

        :rtype: None
        """
        self.debug("()")
        self._drop_membership_multicast_socket()
        self._listening.remove(self._multicast_socket)
        self._multicast_socket.close()
        self._multicast_socket = None

    def _add_membership_multicast_socket(self):
        """
        Make membership request to multicast

        :rtype: None
        """
        self._membership_request = socket.inet_aton(self._multicast_group) \
            + socket.inet_aton(self._multicast_ip)

        # Send add membership request to socket
        # See http://www.tldp.org/HOWTO/Multicast-HOWTO-6.html
        # for explanation of sockopts
        self._multicast_socket.setsockopt(
            socket.IPPROTO_IP,
            socket.IP_ADD_MEMBERSHIP,
            self._membership_request
        )

    def _drop_membership_multicast_socket(self):
        """
        Drop membership to multicast

        :rtype: None
        """
        # Leave group
        self._multicast_socket.setsockopt(
            socket.IPPROTO_IP,
            socket.IP_DROP_MEMBERSHIP,
            self._membership_request
        )
        self._membership_request = None

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
        try:
            self._init_multicast_socket()
        except:
            self._multicast_socket = None
            self.exception("Failed to init multicast socket")
            raise SensorStartException("Multicast socket init failed")

        super(SensorServer, self).start(blocking=False)
        self._is_stopped.clear()
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
        # Blocking
        super(Sensor, self).start(blocking)

    def stop(self):
        """
        Stop the sensor server (soft stop - signal packet loop to stop)
        Warning: Is non blocking (server might still do something after this!)

        :rtype: None
        """
        self.debug("()")
        super(SensorServer, self).stop()
        # No new clients
        if self._multicast_socket is not None:
            self._shutdown_multicast_socket()
        # Signal packet loop to shutdown
        self._is_stopped.set()
