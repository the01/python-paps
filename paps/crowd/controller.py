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
# Created: 2015-06-10 23:54

import threading

from .pluginInterface import Plugin, PluginStartException
from paps.person import Person


class CrowdController(Plugin):
    """
    Manages the audience state and the plugins
    """

    def __init__(self, settings=None):
        """
        Initialize object

        :param settings: Settings to be passed to init (default: None)
        :type settings: dict | None
        :rtype: None
        :raises ValueError: No plugins given
        """
        if settings is None:
            settings = {}
        super(CrowdController, self).__init__(settings)

        self.plugins = settings.get('plugins')
        """ :type plugins: list[paps.crowd.pluginInterface.Plugin] """
        if not self.plugins:
            raise ValueError("No plugins registered")
        self._people = {}
        """ Current state of audience - person.id: Person()
            :type _people: dict[str, paps.person.Person] """
        self._people_lock = threading.Lock()
        """ Lock to control access to ._people """

    def on_person_new(self, people):
        """
        New people joined the audience

        :param people: People that just joined the audience
        :type people: list[paps.person.Person]
        :rtype: None
        """
        self.debug("()")
        changed = []
        with self._people_lock:
            for p in people:
                person = Person.from_person(p)
                if person.id in self._people:
                    self.warning(
                        u"{} already in audience".format(person.id)
                    )
                self._people[person.id] = person
                changed.append(person)
        for plugin in self.plugins:
            try:
                plugin.on_person_new(changed)
            except:
                self.exception(
                    u"Failed to send new people to {}".format(plugin.name)
                )

    def on_person_leave(self, people):
        """
        People left the audience

        :param people: People that left
        :type people: list[paps.person.Person]
        :rtype: None
        """
        self.debug("()")
        changed = []
        with self._people_lock:
            for p in people:
                person = Person.from_person(p)
                if person.id not in self._people:
                    self.warning(u"{} not in audience".format(person.id))
                else:
                    del self._people[person.id]
                changed.append(person)
        for plugin in self.plugins:
            try:
                plugin.on_person_leave(changed)
            except:
                self.exception(
                    u"Failed to send leaving people to {}".format(plugin.name)
                )

    def on_person_update(self, people):
        """
        People have changed (e.g. a sensor value)

        :param people: People whos state changed (may include unchanged)
        :type people: list[paps.person.Person]
        :rtype: None
        """
        self.debug("()")
        changed = []
        with self._people_lock:
            for p in people:
                person = Person.from_person(p)
                if person.id not in self._people:
                    self.warning(u"{} not in audience".format(person.id))
                self._people[person.id] = person
                # Check if really changed? - trust source for now
                changed.append(person)
        for plugin in self.plugins:
            try:
                plugin.on_person_update(changed)
            except:
                self.exception(
                    u"Failed to send updated people to {}".format(plugin.name)
                )

    @property
    def people(self):
        """
        Get people of current audience

        :return: Current people
        :rtype: list[paps.people.People]
        """
        with self._people_lock:
            return self._people.values()

    def start(self, blocking=False):
        """
        Start the interface

        :param blocking: Should the call block until stop() is called
            (default: False)
        :type blocking: bool
        :rtype: None
        """
        self.debug("()")
        # Start the plugins
        for plugin in self.plugins:
            try:
                # Inject self into plugin
                plugin.controller = self
                plugin.start(blocking=False)
            except:
                self.exception(
                    u"Failed to start plugin {}".format(plugin.name)
                )
                raise PluginStartException(
                    "Starting one or more plugins failed"
                )
        super(CrowdController, self).start(blocking=blocking)

    def stop(self):
        """
        Stop the interface

        :rtype: None
        """
        self.debug("()")
        # Stop the plugins
        for plugin in self.plugins:
            try:
                plugin.stop()
            except:
                self.exception(u"Failed to stop plugin {}".format(plugin.name))
        super(CrowdController, self).stop()
