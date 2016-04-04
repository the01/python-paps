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
__date__ = "2016-04-04"
# Created: 2015-06-28 16:34

from paps.crowd import Plugin


class DummyPlugin(Plugin):
    """
    Simple dummy plugin
    """

    def __init__(self, settings=None):
        if settings is None:
            settings = {}
        super(DummyPlugin, self).__init__(settings)

    def start(self, blocking=False):
        self.debug("()")
        super(DummyPlugin, self).start(blocking)

    def stop(self):
        self.debug("()")
        super(DummyPlugin, self).stop()

    def on_person_new(self, people):
        self.debug(people)

    def on_person_update(self, people):
        self.debug(people)

    def on_person_leave(self, people):
        self.debug(people)
