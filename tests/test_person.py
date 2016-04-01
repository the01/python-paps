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
__date__ = "2016-03-26"
# Created: 2015-06-16 17:07

import logging

import pytest

from paps import Person

logging.basicConfig(level=logging.DEBUG)


class TestPerson(object):
    """ Test Person class """

    def setup_class(self):
        self._p1 = Person("p1", True)
        self._p2 = Person("p2", False)

    def test_class_var_present(self):
        assert Person.BITS_PER_PERSON > 0

    def test_init_default(self):
        p = Person()
        assert p.id is None
        assert not p.sitting

    def test_init_var_order(self):
        p = Person("1", True)
        assert p.id == "1"
        assert p.sitting

    def test_init_set_id(self):
        p = Person(id=3)
        assert p.id == 3

    def test_init_set_sitting(self):
        p = Person(sitting=True)
        assert p.sitting

    def test_toDict_1(self):
        assert self._p2.to_dict() == {'id': "p2", 'sitting': False}

    def test_toDict_2(self):
        assert self._p1.to_dict() == {'id': "p1", 'sitting': True}

    def test_fromDict(self):
        p = Person()
        p.from_dict({
            'id': "3",
            'sitting': True
        })
        assert p.id == "3"
        assert p.sitting

    def test_fromDict_id_not_present(self):
        p = Person(id="3")
        p.from_dict({
            'sitting': True
        })
        assert p.id is None
        assert p.sitting

    def test_fromDict_sitting_not_present(self):
        p = Person(id="3")
        with pytest.raises(KeyError):
            p.from_dict({
                'id': "3"
            })

    def test_toTuple_1(self):
        assert self._p2.to_tuple() == ("p2", False)

    def test_toTuple_2(self):
        assert self._p1.to_tuple() == ("p1", True)

    def test_fromTuple(self):
        p = Person()
        p.from_tuple(("1", True))
        assert p.id == "1"
        assert p.sitting

    def test_fromTuple_id_not_present(self):
        p = Person(id="3")
        p.from_tuple((True,))
        assert p.id is None
        assert p.sitting

    def test_toBits_1(self):
        assert self._p2.to_bits() == bytearray([0])

    def test_toBits_2(self):
        assert self._p1.to_bits() == bytearray([1])

    def test_fromBits_1(self):
        p = Person()
        p.from_bits(bytearray([0]))
        assert p.id is None
        assert not p.sitting

    def test_fromBits_2(self):
        p = Person()
        p.from_bits(bytearray([1]))
        assert p.id is None
        assert p.sitting

    def test_fromBits_too_many_bits(self):
        p = Person(id="3")
        with pytest.raises(ValueError):
            p.from_bits(bytearray([0, 1]))

    def test_fromBits_too_few_bits(self):
        p = Person(id="3")
        with pytest.raises(ValueError):
            p.from_bits(bytearray([]))

    def test_fromPerson(self):
        p = Person.from_person(self._p1)
        assert p.id is self._p1.id
        assert p.sitting is self._p1.sitting

    def test__cmp_id_smaller(self):
        p1 = Person(id="a")
        p2 = Person(id="b")
        assert p1 < p2

    def test__cmp_id_bigger(self):
        p1 = Person(id="b")
        p2 = Person(id="a")
        assert not p1 < p2

    def test__cmp_sitting_smaller(self):
        p1 = Person(sitting=False)
        p2 = Person(sitting=True)
        assert p1 < p2

    def test__cmp_sitting_bigger(self):
        p1 = Person(sitting=True)
        p2 = Person(sitting=False)
        assert not p1 < p2

    def test__cmp_equals(self):
        p1 = Person("h", True)
        p2 = Person("h", True)
        assert p1 == p2

    def test__cmp_not_equals(self):
        p1 = Person("h", True)
        p2 = Person("not h", False)
        assert p1 != p2

    def test_str(self):
        p = Person(id="3", sitting=True)
        assert "{}".format(p) == "<Person>(3; Sitting:True)"

    def test_unicode(self):
        p = Person(id=u"3\xA9", sitting=True)
        assert u"{}".format(p) == u"<Person>(3\xA9; Sitting:True)"
