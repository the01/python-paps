# -*- coding: UTF-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

__author__ = "d01"
__email__ = "jungflor@gmail.com"
__copyright__ = "Copyright (C) 2015-16, Florian JUNG"
__license__ = "All rights reserved"
__version__ = "0.1.1"
__date__ = "2016-03-31"
# Created: 2015-05-05 17:10

from flotils.runable import SignalStopWrapper

from paps import Person
from paps.si.app.sensorClient import SensorClient


class Testclient(SensorClient, SignalStopWrapper):
    pass


if __name__ == '__main__':
    import time
    import logging
    import logging.config
    from flotils.logable import default_logging_config
    logging.config.dictConfig(default_logging_config)
    logging.getLogger().setLevel(logging.DEBUG)

    people = [
        Person(id=0, sitting=True),
        Person(id=1, sitting=True)
    ]
    t = Testclient({
        'listen_bind_ip': "0.0.0.0",
        'listen_port': 2347
    })

    try:
        t.start()
        time.sleep(5)
        t.join(people)
        time.sleep(10)
        people[0].sitting = True
        people[1].sitting = False
        t.info("CHANGE")
        t.person_update(people)
        time.sleep(6)
        people[0].sitting = False
        people[1].sitting = True
        t.info("CHANGE")
        t.person_update(people)
        time.sleep(6)
        people[0].sitting = True
        people[1].sitting = True
        t.info("CHANGE")
        t.person_update(people)
        time.sleep(2)
        # raw_input("Press enter/Ctrl+C to stop")
    except KeyboardInterrupt:
        t.debug("Caught KeyboardInterrupt")
    finally:
        t.stop()
