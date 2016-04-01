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
__date__ = "2016-03-31"
# Created: 2015-05-05 16:58

from flotils.logable import ModuleLogable
from flotils.runable import SignalStopWrapper

from paps.si.app.sensorServer import SensorServer


class ModuleLogger(ModuleLogable):
    pass


logger = ModuleLogger()


class Testserver(SensorServer, SignalStopWrapper):
    pass


def show_people(source, people):
    logger.info(
        u"{}: {}".format(source, [u"{}".format(person) for person in people])
    )
    return people


def on_person_new(people):
    show_people("new", people)
    return people


def on_person_update(people):
    show_people("updated", people)
    return people


def on_person_leave(people):
    show_people("leave", people)
    return people


if __name__ == '__main__':
    import logging
    import logging.config
    from flotils.logable import default_logging_config
    logging.config.dictConfig(default_logging_config)
    logging.getLogger().setLevel(logging.DEBUG)

    t = Testserver({
        'on_person_new': on_person_new,
        'on_person_update': on_person_update,
        'on_person_leave': on_person_leave
    })
    try:
        t.start(blocking=True)
    except KeyboardInterrupt:
        t.debug("Caught KeyboardInterrupt")
    finally:
        t.stop()
