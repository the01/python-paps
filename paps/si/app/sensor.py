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

try:
    import Queue as queue
except ImportError:
    # running python3
    import queue
import select
import socket
import threading
import time
from abc import ABCMeta

from flotils.runable import StartStopable
from flotils.loadable import Loadable

from paps.si.app.message import MsgType, Id, APPHeader, APPMessage, \
    guess_class
from paps.si.sensorInterface import SensorStartException


class Sensor(Loadable, StartStopable):
    """ Base class for communication using the APP """
    __metaclass__ = ABCMeta

    def __init__(self, settings=None):
        if settings is None:
            settings = {}
        super(Sensor, self).__init__(settings)
        self._multicast_group = settings.get(
            "multicast_group",
            "239.255.136.245"
        )
        """ Address of multicast group """
        self._multicast_ip = settings.get(
            "multicast_bind_ip",
            self._get_local_ip()
        )
        """ Ip to send multicast messages """
        self._multicast_port = settings.get("multicast_port", 2345)
        """ Port of multicast group """
        self._multicast_ttl = settings.get("multicast_ttl", 3)
        """ TTL of multicast """
        self._listen_ip = settings.get("listen_bind_ip", self._get_local_ip())
        """ Listen at address for messages """
        self._listen_port = settings.get("listen_port", 2346)
        """ Port of listen socket """
        self._select_timeout = settings.get("select_timeout", 2.5)
        """ Timeout for select statement """
        self._start_block_timeout = self._select_timeout
        """ Timeout in start statement """
        self._retransmit_timeout = settings.get("retransmit_timeout", 1)
        """ Timeout to retransmit packets """
        self._retransmit_max_tries = settings.get("retransmit_max_tries", 3)
        """ Max number of tries to retransmit """
        self._buffer_size = settings.get("receive_buffer_size", 4096)
        """ Size of receiving buffer """

        self._membership_request = None
        """ A membership request """
        self._listen_socket = None
        """ UDP Socket for new connections
            :type : socket.socket """
        self._listening = []
        """ Listen on this sockets (via select()) """

        self._send_seq_num = 0
        """ Sequence number for transmitting packets """
        self.inbox = queue.Queue()
        """ Packet inbox """
        self._to_ack = queue.Queue()
        """ Queue of packets that are waiting to be acked """
        self.new_packet = threading.Event()
        """ Event for waiting for new packet received """
        self._seq_ack = set()
        """ Sequence numbers of packets waiting to be acked """
        self._seq_ack_lock = threading.Lock()
        """ Lock for _seq_ack """

        self._device_id = settings.get('device_id', Id.REQUEST)
        """ Device id of this instance """

    @staticmethod
    def _get_local_ip():
        """
        Get the local ip of this device

        :return: Ip of this computer
        :rtype: str
        """
        return set([x[4][0] for x in socket.getaddrinfo(
            socket.gethostname(),
            80,
            socket.AF_INET
        )]).pop()

    def _init_listen_socket(self):
        """
        Init listen socket

        :rtype: None
        """
        self.debug("()")
        self._listen_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._listen_socket.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            1
        )
        self._listen_socket.bind((self._listen_ip, self._listen_port))
        self._listening.append(self._listen_socket)

    def _shutdown_listen_socket(self):
        """
        Shutdown listening socket

        :rtype: None
        """
        self.debug("()")
        if self._listen_socket in self._listening:
            self._listening.remove(self._listen_socket)
        if self._listen_socket:
            self._listen_socket.close()
        self._listen_socket = None

    def _send(self, ip, port, data):
        """
        Send an UDP message

        :param ip: Ip to send to
        :type ip: str
        :param port: Port to send to
        :type port: int
        :return: Number of bytes sent
        :rtype: int
        """
        return self._listen_socket.sendto(data, (ip, port))

    def _send_packet(
            self, ip, port, packet,
            update_timestamp=True, acknowledge_packet=True
    ):
        """
        Send a packet

        :param ip: Ip to send to
        :type ip: str
        :param port: Port to send to
        :type port: int
        :param packet: Packet to be transmitted
        :type packet: APPMessage
        :param update_timestamp: Should update timestamp to current
        :type update_timestamp: bool
        :param acknowledge_packet: Should packet get acknowledged
        :type acknowledge_packet: bool
        :rtype: None
        """
        if acknowledge_packet:
            packet.header.sequence_number = self._send_seq_num
            self._send_seq_num += 1
        packet.header.device_id = self._device_id
        try:
            packed = packet.pack(update_timestamp=update_timestamp)
        except ValueError:
            self.exception("Failed to pack packet")
            return
        self._send(ip, port, packed)
        # TODO: add to wait for ack list
        if acknowledge_packet:
            with self._seq_ack_lock:
                self._seq_ack.add(packet.header.sequence_number)
            self._to_ack.put(
                (time.time() + self._retransmit_timeout, 1, (ip, port), packet)
            )
        self.debug(u"Send: {}".format(packet))

    def _send_ack(self, ip, port, packet, update_timestamp=True):
        """
        Send an ack packet

        :param ip: Ip to send to
        :type ip: str
        :param port: Port to send to
        :type port: int
        :param packet: Packet to be acknowledged
        :type packet: APPMessage
        :param update_timestamp: Should update timestamp to current
        :type update_timestamp: bool
        :rtype: None
        """
        # TODO: maybe wait a bit, so the ack could get attached to another
        # packet
        ack = APPMessage(message_type=MsgType.ACK)
        ack.header.ack_sequence_number = packet.header.sequence_number
        self._send_packet(
            ip, port, ack,
            update_timestamp=update_timestamp, acknowledge_packet=False
        )

    def _unpack(self, data):
        """
        Unpack data into message

        :param data: Data to be unpacked
        :type data: str | unicode
        :return: Unpacked message
        :rtype: APPMessage | APPUnjoinMessage | APPUpdateMessage """ \
        """ | APPJoinMessage | APPDataMessage | APPConfigMessage
        :raises paps.si.app.message.ProtocolViolation: Failed to decode
        """
        header, _ = APPHeader.unpack(data)
        cls = guess_class(header.message_type)
        if cls is None:
            self.warning(u"Unknown type {}\nHeader: {}".format(
                header.message_type, header
            ))
            cls = APPMessage
        return cls.unpack(data)

    def _get_packet(self, socket):
        """
        Read packet and put it into inbox

        :param socket: Socket to read from
        :type socket: socket.socket
        :return: Read packet
        :rtype: APPMessage
        """
        data, (ip, port) = socket.recvfrom(self._buffer_size)
        packet, remainder = self._unpack(data)
        self.inbox.put((ip, port, packet))
        self.new_packet.set()
        self.debug(u"RX: {}".format(packet))

        if packet.header.sequence_number is not None:
            # Packet needs to be acknowledged
            self._send_ack(ip, port, packet)
        ack_seq = packet.header.ack_sequence_number
        if ack_seq is not None:
            # Packet got acknowledged
            with self._seq_ack_lock:
                if ack_seq in self._seq_ack:
                    self.debug(u"Seq {} got acked".format(ack_seq))
                    self._seq_ack.remove(ack_seq)
        return packet

    def _thread_wrapper(self, function):
        """
        Wrap function for exception handling with threaded calls

        :param function: Function to call
        :type function: callable
        :rtype: None
        """
        try:
            function()
        except:
            self.exception("Threaded execution failed")

    def _receiving(self):
        """
        Receiving loop

        :rtype: None
        """
        while self._is_running:
            try:
                rlist, wlist, xlist = select.select(
                    self._listening, [], [],
                    self._select_timeout
                )
            except:
                self.exception("Failed to select socket")
                continue
            for sock in rlist:
                try:
                    self._get_packet(sock)
                except:
                    self.exception("Failed to receive packet")

    def _acking(self, params=None):
        """
        Packet acknowledge and retry loop

        :param params: Ignore
        :type params: None
        :rtype: None
        """
        while self._is_running:
            try:
                t, num_try, (ip, port), packet = self._to_ack.get(
                    timeout=self._select_timeout
                )
            except queue.Empty:
                # Timed out
                continue

            diff = t - time.time()
            if diff > 0:
                time.sleep(diff)

            with self._seq_ack_lock:
                if packet.header.sequence_number not in self._seq_ack:
                    # Not waiting for this?
                    continue

            if num_try <= self._retransmit_max_tries:
                # Try again
                self._send(ip, port, packet.pack(True))
                self._to_ack.put(
                    (
                        time.time() + self._retransmit_timeout,
                        num_try + 1,
                        (ip, port),
                        packet
                    )
                )
            else:
                # Failed to ack
                with self._seq_ack_lock:
                    try:
                        self._seq_ack.remove(packet.header.sequence_number)
                    except KeyError:
                        pass
                self.warning("Exceeded max tries")

    def start(self, blocking=False):
        """
        Start the interface

        :param blocking: Should the call block until stop() is called
            (default: False)
        :type blocking: bool
        :rtype: None
        :raises SensorStartException: Failed to start
        """
        try:
            self._init_listen_socket()
        except:
            self.exception(u"Failed to init listen socket ({}:{})".format(
                self._listen_ip, self._listen_port
            ))
            self._shutdown_listen_socket()
            raise SensorStartException("Listen socket init failed")
        self.info(u"Listening on {}:{}".format(
            self._listen_ip, self._listen_port
        ))

        super(Sensor, self).start(False)
        try:
            a_thread = threading.Thread(
                target=self._thread_wrapper,
                args=(self._receiving,)
            )
            a_thread.daemon = True
            a_thread.start()
        except:
            self.exception("Failed to run receive loop")
            raise SensorStartException("Packet loop failed")
        super(Sensor, self).start(blocking)

    def stop(self):
        """
        Stop the interface

        :rtype: None
        """
        should_sleep = self._is_running
        super(Sensor, self).stop()
        if should_sleep:
            # Make sure everything has enough time to exit
            time.sleep(max(self._select_timeout, self._retransmit_timeout) + 1)
        if self._listen_socket is not None:
            self._shutdown_listen_socket()
