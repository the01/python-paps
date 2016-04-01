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
# Created: 2015-06-11 00:49
""" change in audience """
from abc import ABCMeta, abstractmethod


class ChangeInterface(object):
    """ Interface supports person changed """
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
        super(ChangeInterface, self).__init__()

    @abstractmethod
    def on_person_new(self, people):
        """
        New people joined the audience

        :param people: People that just joined the audience
        :type people: list[paps.person.Person]
        :rtype: None
        """
        raise NotImplementedError("Please implement")

    @abstractmethod
    def on_person_update(self, people):
        """
        People have changed (e.g. a sensor value)

        :param people: People whos state changed (may include unchanged)
        :type people: list[paps.person.Person]
        :rtype: None
        """
        raise NotImplementedError("Please implement")

    @abstractmethod
    def on_person_leave(self, people):
        """
        People left the audience

        :param people: People that left
        :type people: list[paps.person.Person]
        :rtype: None
        """
        raise NotImplementedError("Please implement")
