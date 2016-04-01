# -*- coding: UTF-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
# from __future__ import unicode_literals

__author__ = "d01"
__email__ = "jungflor@gmail.com"
__copyright__ = "Copyright (C) 2015-16, Florian JUNG"
__license__ = "All rights reserved"
__version__ = "0.1.1"
__date__ = "2016-03-29"
# Created: 2015-01-19 11:38

import logging
import datetime
import time

import pytz
import pytest
import mock

from paps.si.app.message import Id, MsgType, Flag,\
    format_data, format_message_type,\
    guess_class, guess_message_type,\
    APPHeader, APPMessage, APPDataMessage, APPUpdateMessage, APPConfigMessage,\
    APPJoinMessage, APPUnjoinMessage
from paps import Person

logging.basicConfig(level=logging.DEBUG)


class TestModuleLevel(object):
    """ Test paps.si.app.message module functions/const/.. """

    def test_constants_present(self):
        assert MsgType.NOT_SET == MsgType.NOT_SET
        assert MsgType.ACK == MsgType.ACK
        assert MsgType.DATA == MsgType.DATA
        assert MsgType.JOIN == MsgType.JOIN
        assert MsgType.UNJOIN == MsgType.UNJOIN
        assert MsgType.CONFIG == MsgType.CONFIG
        assert MsgType.UPDATE == MsgType.UPDATE
        assert Flag.ACKSEQ == Flag.ACKSEQ
        assert Flag.SEQ == Flag.SEQ
        assert Id.NOT_SET == Id.NOT_SET
        assert Id.REQUEST == Id.REQUEST
        assert Id.SERVER == Id.SERVER

    def test_format_message_type_NOT_SET(self):
        assert format_message_type(MsgType.NOT_SET) == "NOT_SET"

    def test_format_message_type_DATA(self):
        assert format_message_type(MsgType.DATA) == "DATA"

    def test_format_message_type_ACK(self):
        assert format_message_type(MsgType.ACK) == "ACK"

    def test_format_message_type_JOIN(self):
        assert format_message_type(MsgType.JOIN) == "JOIN"

    def test_format_message_type_UNJOIN(self):
        assert format_message_type(MsgType.UNJOIN) == "UNJOIN"

    def test_format_message_type_CONFIG(self):
        assert format_message_type(MsgType.CONFIG) == "CONFIG"

    def test_format_message_type_UPDATE(self):
        assert format_message_type(MsgType.UPDATE) == "UPDATE"

    def test_format_message_type_Unkown(self):
        assert format_message_type(123456) == "123456"

    def test_format_data_simple(self):
        assert format_data("abc") == "61:62:63"

    def test_format_data_none(self):
        assert format_data(None) is None

    def test_guess_class_NOT_SET(self):
        assert guess_class(MsgType.NOT_SET) is None

    def test_guess_class_ACK(self):
        assert guess_class(MsgType.ACK) is APPMessage

    def test_guess_class_JOIN(self):
        assert guess_class(MsgType.JOIN) is APPJoinMessage

    def test_guess_class_CONFIG(self):
        assert guess_class(MsgType.CONFIG) is APPConfigMessage

    def test_guess_class_UNJOIN(self):
        assert guess_class(MsgType.UNJOIN) is APPUnjoinMessage

    def test_guess_class_UPDATE(self):
        assert guess_class(MsgType.UPDATE) is APPUpdateMessage

    def test_guess_class_DATA(self):
        assert guess_class(MsgType.DATA) is APPDataMessage

    def test_guess_class_unknown(self):
        assert guess_class(6) is None

    def test_guess_message_type_unkown(self):
        assert guess_message_type(APPMessage(MsgType.NOT_SET)) is None

    def test_guess_message_type_guess(self):
        assert guess_message_type(APPMessage(MsgType.ACK)) is None

    def test_guess_message_type_JOIN(self):
        assert guess_message_type(APPJoinMessage()) is MsgType.JOIN

    def test_guess_message_type_CONFIG(self):
        assert guess_message_type(APPConfigMessage()) is MsgType.CONFIG

    def test_guess_message_type_UNJOIN(self):
        assert guess_message_type(APPUnjoinMessage()) is MsgType.UNJOIN

    def test_guess_message_type_UPDATE(self):
        assert guess_message_type(
            APPUpdateMessage(Id.NOT_SET, [])
        ) is MsgType.UPDATE

    def test_guess_message_type_DATA(self):
        assert guess_message_type(APPDataMessage()) is MsgType.DATA


class TestAPPHeader:
    """ Test the APPHeader class """

    def setup_class(self):
        """ Setup the class """
        pass

    def teardown_class(self):
        """ Teardown the class """
        pass

    def setup(self):
        """ Setup a test (before function) """
        self.now = datetime.datetime(
            year=2015, month=7, day=13,
            hour=11, minute=23, second=33, microsecond=437988,
            tzinfo=pytz.UTC
        )
        self.now_time = 1436786613.0 + self.now.microsecond / 1e6

    def teardown(self):
        """ Teardown a test (after function) """
        pass

    def test_init_default_values(self):
        """ Test the default values of __init__ """
        with mock.patch("paps.si.app.message.datetime.datetime") \
                as mockutc:
            mockutc.__bases__ = (datetime.datetime,)
            mockutc.utcnow.return_value = self.now.replace(tzinfo=None)
            head = APPHeader()
            mockutc.utcnow.assert_called_once_with()
        assert head.message_type == MsgType.NOT_SET
        assert head.device_id == Id.NOT_SET
        assert head.payload_length == 0
        assert head.flags == 0
        assert head._timestamp == self.now
        assert head.ack_sequence_number is None
        assert head.sequence_number is None
        assert head.version_major == 1
        assert head.version_minor == 0

    def test_init_set_message_type(self):
        """ Test setting message type in __init__ """
        head = APPHeader(message_type=MsgType.DATA)
        assert head.message_type == MsgType.DATA

    def test_init_set_messageType_None(self):
        """ Test setting message type to None in __init__
            --> should raise ValueError """
        with pytest.raises(ValueError):
            APPHeader(message_type=None)

    def test_init_set_device_id(self):
        """ Test setting device_id in __init__ """
        head = APPHeader(device_id=Id.REQUEST)
        assert head.device_id == Id.REQUEST

    def test_init_set_payload_length(self):
        """ Test setting payload_length in __init__ """
        head = APPHeader(payload_length=5)
        assert head.payload_length == 5

    def test_init_set_flags(self):
        """ Test setting flags in __init__ """
        head = APPHeader(flags=5)
        assert head.flags == 5

    def test_init_set_timestamp(self):
        """ Test setting timestamp in __init__ """
        now = time.time()
        head = APPHeader(timestamp=now)
        assert head._timestamp == now

    def test_init_set_ack_sequence_number(self):
        """ Test setting ack_sequence_number in __init__ """
        head = APPHeader(ack_sequence_number=5)
        assert head.ack_sequence_number == 5

    def test_init_set_sequence_number(self):
        """ Test setting sequence number in __init__ """
        head = APPHeader(sequence_number=5)
        assert head.sequence_number == 5

    def test_init_set_version_major(self):
        """ Test setting major version in __init__ """
        head = APPHeader(version_major=5)
        assert head.version_major == 5

    def test_init_set_version_minor(self):
        """ Test setting minor version in __init__ """
        head = APPHeader(version_minor=5)
        assert head.version_minor == 5

    def test_get_version(self):
        """ Check version property """
        head = APPHeader(version_minor=5, version_major=3)
        assert head.version == "3.5"

    def test_set_timestamp_direct(self):
        """ Set timestamp property with non datetime object """
        head = APPHeader()
        head._timestamp = None
        t = "muh"
        head.timestamp = t
        assert head._timestamp is t

    def test_set_timestamp_datetime(self):
        """ Set timestamp property with datetime object """
        head = APPHeader()
        head._timestamp = None
        head.timestamp = self.now
        assert head._timestamp == self.now_time

    def test_get_timestamp_not_set(self):
        """ Timestamp set to None """
        head = APPHeader()
        head._timestamp = None
        assert head.timestamp is None

    def test_get_timestamp_zero(self):
        """ Timestamp set to zero """
        head = APPHeader()
        head._timestamp = 0
        assert head.timestamp is None

    def test_get_timestamp_datetime(self):
        """ Timestamp set to valid time """
        head = APPHeader()
        head._timestamp = self.now_time
        assert head.timestamp == self.now

    def test_timestamp_set_get_datetime(self):
        """ Timestamp set and get datetime """
        head = APPHeader()
        head.timestamp = self.now
        # assert head._timestamp == self.now_time
        assert head.timestamp == self.now

    def test_set_timestamp_to_current(self):
        """ Test setTimestampToCurrent calls datetime.utcnow() """
        head = APPHeader()
        with mock.patch("paps.si.app.message.datetime.datetime") \
                as mockutc:
            mockutc.__bases__ = (datetime.datetime,)
            mockutc.utcnow.return_value = self.now.replace(tzinfo=None)
            head.set_timestamp_to_current()
            mockutc.utcnow.assert_called_once_with()
        # Note: head._timestamp is not a float, because it does not recognize
        #       it as a datetime.datetime when setting it in set_timestamp

    def test_pack_update_timestamp_use_current(self):
        """ Test packing with timestamp update at pack """
        head = APPHeader(
            version_major=3,
            version_minor=2,
            timestamp=5.0,
            message_type=MsgType.JOIN,
            device_id=Id.SERVER
        )
        t = self.now_time

        def mock_set_timestamp_to_current(self):
            self._timestamp = t

        APPHeader.set_timestamp_to_current = mock_set_timestamp_to_current
        res = head.pack(True)
        assert head._timestamp is t
        assert format_data(res) == "32:01:00:00:4e:ab:47:3f:00:01:00:00"

    def test_pack_update_timestamp_no_timestamp(self):
        """
        Test packing with timestamp update at pack via missing timestamp
        """
        t = self.now_time

        def mock_set_timestamp_to_current(self):
            self._timestamp = t

        APPHeader.set_timestamp_to_current = mock_set_timestamp_to_current
        head = APPHeader(
            version_major=3,
            version_minor=2,
            timestamp=30.0,
            message_type=MsgType.JOIN,
            device_id=Id.SERVER
        )
        head._timestamp = None
        res = head.pack(False)
        assert head._timestamp is t
        assert format_data(res) == "32:01:00:00:4e:ab:47:3f:00:01:00:00"

    def test_pack_update_timestamp_no_timestamp_update(self):
        """ Test packing with no timestamp update at pack """
        def mock_set_timestamp_to_current(self):
            self._timestamp = 20.0
        APPHeader.set_timestamp_to_current = mock_set_timestamp_to_current
        head = APPHeader(
            version_major=3,
            version_minor=2,
            timestamp=self.now_time,
            message_type=MsgType.JOIN,
            device_id=Id.SERVER
        )
        res = head.pack(False)
        assert head._timestamp == self.now_time
        assert format_data(res) == "32:01:00:00:4e:ab:47:3f:00:01:00:00"

    def test_pack_update_timestamp_use_datetime_default(self):
        """ Test packing with a datetime object and default for pack() """
        def mock_set_timestamp_to_current(self):
            self._timestamp = 20.0
        APPHeader.set_timestamp_to_current = mock_set_timestamp_to_current
        head = APPHeader(
            version_major=3,
            version_minor=2,
            timestamp=self.now,
            message_type=MsgType.JOIN,
            device_id=Id.SERVER
        )
        res = head.pack()
        assert head._timestamp == self.now_time
        assert format_data(res) == "32:01:00:00:4e:ab:47:3f:00:01:00:00"

    def test_pack_device_id_not_set(self):
        """ Fail because of device id not set """
        head = APPHeader(
            message_type=MsgType.UPDATE,
            device_id=Id.NOT_SET
        )
        with pytest.raises(ValueError):
            head.pack(True)

    def test_pack_device_id_invalid_value(self):
        """ Fail because of device id invalid value """
        head = APPHeader(
            message_type=MsgType.UPDATE,
            device_id=-2
        )
        with pytest.raises(ValueError):
            head.pack(True)

    def test_pack_device_id_invalid_type(self):
        """ Fail because of device id invalid type """
        head = APPHeader(
            message_type=MsgType.UPDATE,
            device_id=1.0
        )
        with pytest.raises(ValueError):
            head.pack(True)

    def test_pack_device_id_valid(self):
        """ Test with first valid device id """
        head = APPHeader(
            message_type=MsgType.UPDATE,
            device_id=0
        )
        head.pack(True)

    def test_pack_message_type_not_set(self):
        """ Fail because of message type not set """
        head = APPHeader(
            message_type=MsgType.NOT_SET,
            device_id=Id.REQUEST
        )
        with pytest.raises(ValueError):
            head.pack(True)

    def test_pack_message_type_invalid_value_too_low(self):
        """ Fail because of message type value too low """
        head = APPHeader(
            message_type=-2,
            device_id=Id.REQUEST
        )
        with pytest.raises(ValueError):
            head.pack()

    def test_pack_message_type_invalid_value_too_high(self):
        """ Fail because of message type value too high """
        head = APPHeader(
            message_type=6,
            device_id=Id.REQUEST
        )
        with pytest.raises(ValueError):
            head.pack()

    def test_pack_message_type_invalid_type(self):
        """ Fail because of message type invalid type """
        head = APPHeader(
            message_type=-1,
            device_id=Id.REQUEST
        )
        with pytest.raises(ValueError):
            head.pack()

    @pytest.mark.parametrize("mt", list(MsgType))
    def test_pack_message_type_valid(self, mt):
        """ Test with valid message types """
        if mt == MsgType.NOT_SET:
            return
        # not how its supposed to be done
        head = APPHeader(
            message_type=mt,
            device_id=Id.REQUEST
        )
        head.pack()

    # TODO: Test unpack


class TestAPPDataMessage:
    """ Test APPDataMessage class """

    def test_guess_msg_type(self):
        p = APPDataMessage()
        assert p.header.message_type == MsgType.DATA

    def test_pack_unpack(self):
        pay = {'people': [0, 2, 4]}
        p = APPDataMessage(device_id=Id.SERVER, payload=pay)
        p.header.sequence_number = 5
        p2, rem = APPDataMessage.unpack(p.pack())
        assert rem == ""
        assert isinstance(p2, APPDataMessage)
        assert p.payload == p2.payload
        assert p.header.sequence_number == p2.header.sequence_number
        assert p.header.device_id == p2.header.device_id


class TestAPPJoinMessage:
    """ Test APPJoinMessage class """

    def test_guess_msg_type(self):
        p = APPJoinMessage()
        assert p.header.message_type == MsgType.JOIN

    def test_pack_unpack(self):
        pay = {'people': [0, 2, 4]}
        p = APPJoinMessage(device_id=Id.SERVER, payload=pay)
        p.header.sequence_number = 5
        p2, rem = APPJoinMessage.unpack(p.pack())
        assert rem == ""
        assert isinstance(p2, APPJoinMessage)
        assert p.payload == p2.payload
        assert p.header.sequence_number == p2.header.sequence_number
        assert p.header.device_id == p2.header.device_id

    def test_default_people_packet(self):
        packet = APPJoinMessage(payload={'people': [0, 0, 0]})
        packet.pack(update_timestamp=True)


class TestAPPUnjoinMessage:
    """ Test APPUnjoinMessage class """

    def test_guess_msg_type(self):
        p = APPUnjoinMessage()
        assert p.header.message_type == MsgType.UNJOIN


class TestAPPUpdateMessage:
    """ Test APPUpdateMessage class """

    def test_to_unicode(self):
        people = [Person(id=0)]
        packet = APPUpdateMessage(device_id=Id.NOT_SET, people=people)
        u"{}".format(packet)

    def test_pack_unpack_people(self):
        people = [Person(id=0)]
        packet = APPUpdateMessage(device_id=2, people=people)
        p2, rem = APPUpdateMessage.unpack(packet.pack(True))
        assert rem == ""

    def test_pack_people_1(self):
        """ Test _pack_people with Person(id=0, not sitting) """
        people = [Person(id=0, sitting=False)]
        packet = APPUpdateMessage(device_id=2, people=people)
        assert format_data(packet.payload) == "02"

    def test_pack_people_2(self):
        """ Test _pack_people with Person(id=0, sitting) """
        people = [Person(id=0, sitting=True)]
        packet = APPUpdateMessage(device_id=2, people=people)
        assert format_data(packet.payload) == "03"

    def test_pack_people_3(self):
        """
        Test _packPeople with Person(id=0, not sitting), Person(id=1, sitting)
        """
        people = [Person(id=0, sitting=False), Person(id=1, sitting=True)]
        packet = APPUpdateMessage(device_id=2, people=people)
        assert format_data(packet.payload) == "05"

    def test_pack_people_4(self):
        """
        Test _packPeople with
            P(id=0, not sitting), P(id=1, not sitting), P(id=2, sitting),
            P(id=3, not sitting), P(id=4, sitting), P(id=5, not sitting),
            P(id=6, sitting)
        """
        people = [
            Person(id=0, sitting=False),
            Person(id=1, sitting=False),
            Person(id=2, sitting=True),
            Person(id=3, sitting=False),
            Person(id=4, sitting=True),
            Person(id=5, sitting=False),
            Person(id=6, sitting=True)
        ]
        packet = APPUpdateMessage(device_id=2, people=people)
        assert format_data(packet.payload) == "95"

    def test_pack_people_5(self):
        """
        Test _packPeople with
            P(id=0, not sitting), P(id=1, not sitting), P(id=2, sitting),
            P(id=3, not sitting), P(id=4, sitting), P(id=5, not sitting),
            P(id=6, sitting), P(id=7, sitting)
        """
        people = [
            Person(id=0, sitting=False),
            Person(id=1, sitting=False),
            Person(id=2, sitting=True),
            Person(id=3, sitting=False),
            Person(id=4, sitting=True),
            Person(id=5, sitting=False),
            Person(id=6, sitting=True),
            Person(id=7, sitting=True)
        ]
        packet = APPUpdateMessage(device_id=2, people=people)
        assert format_data(packet.payload) == "01:2b"

    def test_people_1(self):
        """
        Test people with
            0x02 ->
            P(id=0, sitting)
        """
        packet = APPUpdateMessage(device_id=2, people=[])
        payload = ""
        for hex_str in "02".split(":"):
            payload += chr(int(hex_str, 16))
        packet._payload = payload
        people = packet.people()
        assert not people[0].sitting

    def test_people_2(self):
        """
        Test people with
            0x03 ->
            P(id=0, not sitting)
        """
        packet = APPUpdateMessage(device_id=2, people=[])
        payload = ""
        for hex_str in "03".split(":"):
            payload += chr(int(hex_str, 16))
        packet._payload = payload
        people = packet.people()
        assert people[0].sitting

    def test_people_3(self):
        """
        Test people with
            0x03 ->
            P(id=0, not sitting)
            P(id=1, sitting)
        """
        packet = APPUpdateMessage(device_id=2, people=[])
        payload = ""
        for hex_str in "05".split(":"):
            payload += chr(int(hex_str, 16))
        packet._payload = payload
        people = packet.people()
        assert not people[0].sitting
        assert people[1].sitting

    def test_people_4(self):
        """
        Test people with
            0x95 ->
            P(id=0, not sitting), P(id=1, not sitting), P(id=2, sitting),
            P(id=3, not sitting), P(id=4, sitting), P(id=5, not sitting),
            P(id=6, sitting)
        """
        packet = APPUpdateMessage(device_id=2, people=[])
        payload = ""
        for hex_str in "95".split(":"):
            payload += chr(int(hex_str, 16))
        packet._payload = payload
        people = packet.people()
        assert not people[0].sitting
        assert not people[1].sitting
        assert people[2].sitting
        assert not people[3].sitting
        assert people[4].sitting
        assert not people[5].sitting
        assert people[6].sitting

    def test_people_5(self):
        """
        Test people with
            0x12b ->
            P(id=0, not sitting), P(id=1, not sitting), P(id=2, sitting),
            P(id=3, not sitting), P(id=4, sitting), P(id=5, not sitting),
            P(id=6, sitting), P(id=7, sitting)
        """
        packet = APPUpdateMessage(device_id=2, people=[])
        payload = ""
        for hex_str in "01:2b".split(":"):
            payload += chr(int(hex_str, 16))
        packet._payload = payload
        people = packet.people()
        assert not people[0].sitting
        assert not people[1].sitting
        assert people[2].sitting
        assert not people[3].sitting
        assert people[4].sitting
        assert not people[5].sitting
        assert people[6].sitting
        assert people[7].sitting
