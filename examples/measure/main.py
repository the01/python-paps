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
__date__ = "2016-04-05"
# Created: 2015-07-17 18:50
""" measure request speed execute """

import time

from flotils.runable import StartStopable, SignalStopWrapper

import client
import server


class StartWrapper(StartStopable, SignalStopWrapper):

    def __init__(self, settings=None):
        if settings is None:
            settings = {}
        super(StartWrapper, self).__init__(settings)
        self.modules = settings['modules_run']
        """ Modules to start/stop with this one
            :type : list[client.WrapperClient | server.WrapperServer] """

    def start(self, blocking=False):
        self.debug("()")
        for module in self.modules:
            try:
                module.start(False)
            except:
                self.exception(u"Failed to start {}".format(module.name))
                self.stop()
                return
        super(StartWrapper, self).start(blocking)

    def stop(self):
        self.debug("()")
        if not self._is_running:
            return
        super(StartWrapper, self).stop()
        for module in self.modules:
            try:
                module.stop()
            except:
                self.exception(u"Failed to stop {}".format(module.name))


if __name__ == '__main__':
    import argparse

    import logging
    import logging.config
    from flotils.logable import default_logging_config
    logging.config.dictConfig(default_logging_config)
    logging.getLogger().setLevel(logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--client", action="store_true")
    parser.add_argument("--number", type=int, default=1)
    parser.add_argument("--host", type=str, default="127.0.0.1")
    parser.add_argument("--port", type=int, default=2346)
    parser.add_argument("--people", type=int, default=3)
    parser.add_argument("--throttle", type=int, default=0)

    args = parser.parse_args()
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    modules = []
    if args.client:
        modules, cmd_line = client.create(
            args.number, args.host, args.port, args.people, args.throttle
        )
    else:
        modules, cmd_line = server.create(args.host, args.port)

    ctrl = StartWrapper({
        'modules_run': modules
    })

    try:
        ctrl.start(False)
        while True:
            line = raw_input("> ")
            if callable(cmd_line):
                line = cmd_line(line, ctrl)
            if line == "quit":
                break
    except KeyboardInterrupt:
        pass
    finally:
        ctrl.stop()
