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
# Created: 2015-03-21 06:18
""" Interfaces and exceptions for sensors """

from abc import ABCMeta, abstractmethod

from flotils.logable import Logable
from flotils.runable import StartStopable, StartException

from ..changeInterface import ChangeInterface
from ..papsException import PapsException


class SensorException(PapsException):
    """ Base class for all exceptions of a sensor interface class """
    pass


class SensorStartException(SensorException, StartException):
    """ Failed to start """
    pass


class SensorJoinException(SensorException):
    """ Failed to join audience """
    pass


class SensorUpdateException(SensorException):
    """ Failed to update """
    pass


class SensorServerInterface(Logable, StartStopable):
    """ Interface for sensor servers """
    __metaclass__ = ABCMeta

    def __init__(self, settings=None):
        """
        Initialize object

        :param settings: Settings for object (default: None)
        :type settings: dict | None
        :rtype: None
        """
        if settings is None:
            settings = {}
        super(SensorServerInterface, self).__init__(settings)
        self.changer = settings['changer']
        """ Send person events to this class
            :type : paps.changeInterface.ChangeInterface """
        if not isinstance(self.changer, ChangeInterface):
            raise TypeError("Expected changer to be of ChangeInterface")


class SensorClientInterface(Logable, StartStopable):
    """ Interface for sensor clients """
    __metaclass__ = ABCMeta

    def __init__(self, settings=None):
        """
        Initialize object

        :param settings: Settings for object (default: None)
        :type settings: dict | None
        :rtype: None
        """
        if settings is None:
            settings = {}
        super(SensorClientInterface, self).__init__(settings)
        self.on_config = settings.get('on_config', None)
        """ The config has changed - for modules on a higher layer
            :type on_config: (dict) -> None | None """

    @abstractmethod
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
        raise NotImplementedError("Please implement")

    @abstractmethod
    def unjoin(self):
        """
        Leave the local audience

        :rtype: None
        :raises SensorJoinException: Failed to leave
        """
        raise NotImplementedError("Please implement")

    @abstractmethod
    def person_update(self, people):
        """
        Update the status of people

        :param people: All people of this sensor
        :type people: list[paps.person.Person]
        :rtype: None
        :raises SensorUpdateException: Failed to update
        """
        raise NotImplementedError("Please implement")

    @abstractmethod
    def config(self, settings):
        """
        Configuration has changed - config this module and lower layers
        (calls on_config - if set)

        :param settings: New configuration
        :type settings: dict
        :rtype: None
        :raises SensorUpdateException: Failed to update
        """
        raise NotImplementedError("Please implement")
