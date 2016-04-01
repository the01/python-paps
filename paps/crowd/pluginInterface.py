# -*- coding: UTF-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

__author__ = "d01"
__email__ = "jungflor@gmail.com"
__copyright__ = "Copyright (C) 2015-16, Florian JUNG"
__license__ = "MIT"
__version__ = "0.2.0"
__date__ = "2016-03-29"
# Created: 2015-06-07 15:13

from abc import ABCMeta

from flotils.runable import StartStopable, StartException
from flotils.loadable import Loadable

from ..papsException import PapsException
from ..changeInterface import ChangeInterface


class PluginException(PapsException):
    """
    Class for plugin exceptions
    """
    pass


class PluginStartException(PapsException, StartException):
    """
    Class for plugin start exceptions
    """
    pass


class Plugin(Loadable, StartStopable, ChangeInterface):
    """
    Abstract interface for plugin
    """
    __metaclass__ = ABCMeta

    def __init__(self, settings=None):
        """
        Initialize object

        :param settings: Settings to be passed for init (default: None)
        :type settings: dict | None
        :rtype: None
        :raises TypeError: Controller missing
        """
        if settings is None:
            settings = {}
        super(Plugin, self).__init__(settings)
        self.controller = settings.get('controller')
        """ Plugin controller reference
            :type controller: paps.crowd.controller.CrowdController """
        # TODO: check against attribute/instance
