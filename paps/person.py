# -*- coding: UTF-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
# from __future__ import unicode_literals

__author__ = "d01"
__email__ = "jungflor@gmail.com"
__copyright__ = "Copyright (C) 2015-16, Florian JUNG"
__license__ = "MIT"
__version__ = "1.0.0"
__date__ = "2016-03-31"
# Created: 2015-04-04 14:21
""" Member of audience """


class Person(object):
    """ Class representing a person in the audience participation system  """

    BITS_PER_PERSON = 1
    """ How many bits are necessary to encode one person """

    def __init__(self, id=None, sitting=False):
        """
        Initialize object

        :param id: Unique id of person
        :type id: None | str | unicode | int
        :param sitting: Is this person sitting
        :type sitting: bool
        :rtype: None
        """
        super(Person, self).__init__()
        self.sitting = sitting
        """ Is this person sitting
            :type sitting: bool """
        self.id = id
        """ Id of person
            :type id: None | str | unicode | int """

    def to_dict(self):
        """
        Convert this person to a dict

        :return: Dictionary representing this person
        :rtype: dict
        """
        return {
            'sitting': self.sitting,
            'id': self.id
        }

    def from_dict(self, d):
        """
        Set this person from dict

        :param d: Dictionary representing a person ('sitting'[, 'id'])
        :type d: dict
        :rtype: Person
        :raises KeyError: 'sitting' not set
        """
        self.sitting = d['sitting']
        self.id = d.get('id', None)
        return self

    def to_tuple(self):
        """
        Convert this person to a tuple

        :return: Tuple representing this person
        :rtype: (None | str, bool)
        """
        return self.id, self.sitting,

    def from_tuple(self, t):
        """
        Set this person from tuple

        :param t: Tuple representing a person (sitting[, id])
        :type t: (bool) | (bool, None | str | unicode | int)
        :rtype: Person
        """
        if len(t) > 1:
            self.id = t[0]
            self.sitting = t[1]
        else:
            self.sitting = t[0]
            self.id = None
        return self

    def to_bits(self):
        """
        Convert this person to bits (ignores the id)

        :return: Bits representing this person
        :rtype: bytearray
        """
        # TODO include id
        return bytearray([
            int(self.sitting)
        ])

    def from_bits(self, bits):
        """
        Set this person from bits (ignores the id)

        :param bits: Bits representing a person
        :type bits: bytearray
        :rtype: Person
        :raises ValueError: Bits has an unexpected length
        """
        # TODO include id
        if len(bits) != Person.BITS_PER_PERSON:
            raise ValueError(u"Person requires exactly {} bits".format(
                Person.BITS_PER_PERSON
            ))
        self.sitting = bool(bits[0])
        return self

    @staticmethod
    def from_person(person):
        """
        Copy person

        :param person: Person to copy into new instance
        :type person: Person
        :rtype: Person
        """
        p = Person()
        p.id = person.id
        p.sitting = person.sitting
        return p

    def __cmp__(self, other):
        """
        Compare two people with each other

        If a field is set (not none/empty) that is bigger than an unset one.
        Only compares two fields, if they are set in both articles

        compare hierachy (if present and should be compared):
        - id
        - sitting

        :param other: Other person to compare to
        :type other: Person
        :return: -1: self <  other
                  0: self == other (=False)
                 +1: self >  other
        :rtype: int
        """
        if self.id < other.id:
            return -1
        elif self.id > other.id:
            return 1
        if self.sitting < other.sitting:
            return -1
        elif self.sitting > other.sitting:
            return 1
        return 0

    def __lt__(self, other):
        """
        This smaller than other

        :param other: Other person to compare to
        :type other: Person
        :return: Am I smaller
        :rtype: bool
        """
        return self.__cmp__(other) < 0

    def __eq__(self, other):
        """
        This equal to other

        :param other: Other person to compare to
        :type other: Person
        :return: Am I equal
        :rtype: bool
        """
        return self.__cmp__(other) == 0

    def __str__(self):
        return "<{}>({}; Sitting:{})".format(
            type(self).__name__, self.id, self.sitting
        )

    def __unicode__(self):
        return u"<{}>({}; Sitting:{})".format(
            type(self).__name__, self.id, self.sitting
        )
