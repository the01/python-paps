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
# Created: 2015-06-05 11:13

from flotils.runable import StartStopable
from flotils.logable import Logable

from .sensorInterface import SensorClientInterface
from paps.changeInterface import ChangeInterface


class SensorServerClientAdapter(
    Logable, ChangeInterface, StartStopable
):
    """ Class to connect a plugin directly to a sensor """

    def __init__(self, settings=None):
        """
        Intialize object

        :param settings: Settings for object (default: None)
        :type settings: dict | None
        :rtype: None
        """
        if settings is None:
            settings = {}
        super(SensorServerClientAdapter, self).__init__(settings)
        self.sensor_client = settings['sensor_client']
        if not isinstance(self.sensor_client, SensorClientInterface):
            raise TypeError(
                "'sensor_client' needs to be of class SensorClientInterface"
            )
        self._on_config = settings.get('on_config', None)
        """ The config has changed - for modules on a higher layer
            :type on_config: (dict) -> None | None """
        self._original_on_config = self.sensor_client.on_config

    def on_person_new(self, people):
        """
        Add new people

        All people supported need to be added simultaneously,
        since on every call a unjoin() followed by a join() is issued

        :param people: People to add
        :type people: list[paps.people.People]
        :rtype: None
        :raises Exception: On error (for now just an exception)
        """
        try:
            self.on_person_leave([])
        except:
            # Already caught and logged
            pass

        try:
            self.sensor_client.join(people)
        except:
            self.exception("Failed to join audience")
            raise Exception("Joining audience failed")

    def on_person_leave(self, people):
        """
        Remove people from audience

        Does not check which people should leave, but leaves the audience
        all together

        :param people: People to leave - not checked
        :type people: list[paps.people.People]
        :rtype: None
        :raises Exception: On error (for now just an exception)
        """
        try:
            self.sensor_client.unjoin()
        except:
            self.exception("Failed to leave audience")
            raise Exception("Leaving audience failed")

    def on_person_update(self, people):
        """
        People have changed

        Should always include all people
        (all that were added via on_person_new)

        :param people: People to update
        :type people: list[paps.people.People]
        :rtype: None
        :raises Exception: On error (for now just an exception)
        """
        try:
            self.sensor_client.person_update(people)
        except:
            self.exception("Failed to update people")
            raise Exception("Updating people failed")

    def on_config(self, settings):
        if callable(self._original_on_config):
            try:
                self._original_on_config(settings)
            except:
                self.exception("Failed to update remote config on original")
                raise Exception("Original config failed")
        if callable(self._on_config):
            try:
                self._on_config(settings)
            except:
                self.exception("Failed to update remote config on local")
                raise Exception("Local config failed")

    def start(self, blocking=False):
        self.debug("()")
        # since this class only forwards and translates input from a server
        # to the client interface, no 'running' is required here
        super(SensorServerClientAdapter, self).start(blocking=False)
        self.sensor_client.start(blocking)

    def stop(self):
        self.debug("()")
        self.sensor_client.stop()
        super(SensorServerClientAdapter, self).stop()
