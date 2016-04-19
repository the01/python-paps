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
# Created: 2016-03-14 15:27
""" measure request speed echo server """

from paps.si.app.message import MsgType
from paps.si.app.sensorServer import SensorServer
from paps.changeInterface import ChangeInterface

from server import WrapperServer

class EchoServer(SensorServer):

    def _do_packet(self, packet, ip, port):
        """

        :param packet:
        :type packet: paps.si.app.message.APPMessage
        :param ip:
        :param port:
        :return:
        """
        super(EchoServer, self)._do_packet(packet, ip, port)
        if packet.header.message_type == MsgType.UPDATE:
            # Echo update msg
            self.debug(packet.header.timestamp)
            self._send_packet(
                ip, port, packet,
                update_timestamp=False, acknowledge_packet=False
            )


class WrapperEchoServer(WrapperServer):

    def on_person_update(self, people):
        pass


def cmd_line(line, ctrl):
    server = ctrl.modules[0]
    """ :type : StartServer """

    return line


def create(host, port):
    """
    Prepare server to execute

    :return: Modules to execute, cmd line function
    :rtype: list[WrapperServer], callable | None
    """
    wrapper = WrapperEchoServer({
        'server': None
    })
    d = {
        'listen_port': port,
        'changer': wrapper
    }
    if host:
        d['listen_bind_ip'] = host

    ses = EchoServer(d)
    wrapper.server = ses
    return [wrapper], cmd_line
