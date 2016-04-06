# -*- coding: UTF-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

__author__ = "d01"
__email__ = "jungflor@gmail.com"
__copyright__ = "Copyright (C) 2015-16, Florian JUNG"
__license__ = "MIT"
__version__ = "0.1.2"
__date__ = "2016-04-06"
# Created: 2015-06-09 15:29

import threading

import RPi.GPIO as GPIO
from flotils.runable import StartStopable, StartException, SignalStopWrapper
from flotils.loadable import Loadable

from paps import Person


class GPIODetector(Loadable, StartStopable):
    """ Listen on gpios and trigger on_person_* events """

    def __init__(self, settings=None):
        """
        Initialize object

        :param settings: Settings for object (default: None)
        :type settings: dict | None
        :rtype: None
        """
        if settings is None:
            settings = {}
        super(GPIODetector, self).__init__(settings)
        self.changer = settings['changer']
        """ Object to receive change events
            :type : paps.changeInterface.ChangeInterface """

        self.gpio_mode = settings.get('gpio_mode', "BCM").upper()
        """ Numbering scheme of gpio pins (default: BCM)
            :type gpio_mode: str """
        self.gpio_bouncetime = settings.get('gpio_bouncetime', 500)
        """ Software debounce time """
        self.gpio_bouncetime_sleep = settings.get('gpio_bouncetime_sleep', 0.1)
        """ Sleep interval between reads for debouncing """
        self.gpios = settings.get('gpios', [])
        """ Gpio pin numbers in use
            :type gpios: list[int] """
        if not self.gpios:
            raise ValueError("No GPIOs given")
        self.people = []
        """ Registered people
            :type : list[paps.person.Person]"""
        self._people_lock = threading.Lock()
        """ Lock to access registered people """
        # Add person for each gpio
        for index, gpio in enumerate(self.gpios):
            p = Person(id=index, sitting=False)
            self.people.append(p)

    def _gpio_callback(self, gpio):
        """
        Gets triggered whenever the the gpio state changes

        :param gpio: Number of gpio that changed
        :type gpio: int
        :rtype: None
        """
        self.debug(u"Triggered #{}".format(gpio))
        try:
            index = self.gpios.index(gpio)
        except ValueError:
            self.error(u"{} not present in GPIO list".format(gpio))
            return
        with self._people_lock:
            person = self.people[index]
            read_val = GPIO.input(gpio)
            if read_val == person.sitting:
                # Nothing changed?
                time.sleep(self.gpio_bouncetime_sleep)
                # Really sure?
                read_val = GPIO.input(gpio)
            if person.sitting != read_val:
                person.sitting = read_val
                self.debug(u"Person is now {}sitting".format(
                    "" if person.sitting else "not ")
                )
                try:
                    self.changer.on_person_update(self.people)
                except:
                    self.exception(
                        u"Failed to update people (Person: {})".format(person)
                    )
            else:
                self.warning(u"Nothing changed on {}".format(gpio))

    def start(self, blocking=False):
        """
        Start the interface

        :param blocking: Should the call block until stop() is called
            (default: False)
        :type blocking: bool
        :rtype: None
        """
        self.debug("()")
        # Init GPIO
        # Enable warnings
        GPIO.setwarnings(True)
        # Careful - numbering between different pi version might differ
        if self.gpio_mode == "BOARD":
            GPIO.setmode(GPIO.BOARD)
        else:
            GPIO.setmode(GPIO.BCM)

        # Register people
        try:
            self.changer.on_person_new(self.people)
        except:
            self.exception("Failed to add people to audience")
            raise StartException("Adding people failed")

        # Setup pins
        for gpio in self.gpios:
            GPIO.setup(gpio, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            GPIO.add_event_detect(
                gpio, GPIO.BOTH,
                callback=self._gpio_callback, bouncetime=self.gpio_bouncetime
            )
        super(GPIODetector, self).start(blocking)

    def stop(self):
        """
        Stop the interface

        :rtype: None
        """
        self.debug("()")
        # Not sure if this is necessary, but good form
        if self._is_running:
            for gpio in self.gpios:
                GPIO.remove_event_detect(gpio)
            # Cleanup - includes used numbering scheme
        GPIO.cleanup()
        # Leave audience
        try:
            self.changer.on_person_leave(self.people)
        except:
            self.exception("Failed to remove people from audience")
        super(GPIODetector, self).stop()


class TestClient(GPIODetector, SignalStopWrapper):

    def __init__(self, settings):
        super(TestClient, self).__init__(settings)


if __name__ == "__main__":
    import time
    import logging
    import logging.config

    from flotils.logable import default_logging_config

    from paps.si.app.sensorClient import SensorClient
    from paps.si.sensorClientAdapter import SensorClientAdapter

    logging.config.dictConfig(default_logging_config)
    logging.getLogger().setLevel(logging.DEBUG)
    logging.captureWarnings(True)
    settings_file = "examples/settings/gpio_sensor_client.json"

    sc = SensorClient({
        'settings_file': settings_file
    })
    gd = SensorClientAdapter({
        'sensor_client': sc
    })
    tc = TestClient({
        'changer': gd,
        'gpio_bouncetime': 100,
        'gpio_bouncetime_sleep': 0.1,
        'gpios': [4, 17, 27]
    })
    try:
        gd.start(blocking=False)
        time.sleep(1)
        tc.start(blocking=True)
    finally:
        # Save changed device_id
        try:
            sett = sc.loadSettings(settings_file)
            sett['device_id'] = sc._device_id
            sc.saveSettings(settings_file, sett)
        except:
            logging.exception("Failed to update settings")
        tc.stop()
        gd.stop()
