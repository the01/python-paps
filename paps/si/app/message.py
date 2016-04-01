# -*- coding: UTF-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
# from __future__ import unicode_literals

__author__ = "d01"
__email__ = "jungflor@gmail.com"
__copyright__ = "Copyright (C) 2015-16, Florian JUNG"
__license__ = "MIT"
__version__ = "0.2.0"
__date__ = "2016-03-29"
# Created: 2015-03-21 24:00

import logging
import calendar
import datetime
import tzlocal
import struct

from enum import IntEnum, unique
import pytz
from flotils.loadable import loadJSON, saveJSON

from ...papsException import PapsException
from ...person import Person


BYTE_ORDER = ">"
local_tz = tzlocal.get_localzone()
logger = logging.getLogger(__name__)


@unique
class MsgType(IntEnum):
    """ Packet message types """

    NOT_SET = -1
    """ Unset message type """
    ACK = 0
    """ Empty package (only for ack/round trip timing) - no ack for this """
    JOIN = 1
    """ Client request to join system """
    CONFIG = 2
    """ Server sets client config """
    UNJOIN = 3
    """ Client leaves system """
    UPDATE = 4
    """ Client changed """
    DATA = 5
    """ Transmit data (json) object """


@unique
class Flag(IntEnum):
    """ Message header flags """

    SEQ = 1
    """ Is sequence number present for pack """
    ACKSEQ = 2
    """ Is sequence number present for an ack """


@unique
class Id(IntEnum):
    """ Message device ids """

    NOT_SET = -1
    """ Id to be set by framework """
    REQUEST = 0
    """ Request id from server """
    SERVER = 1
    """ Id of server """


class ProtocolViolation(PapsException):
    pass


def format_message_type(message_type):
    """
    Get printable version for message type

    :param message_type: Message type
    :type message_type: int
    :return: Printable version
    :rtype: str
    """
    if message_type == MsgType.NOT_SET:
        return "NOT_SET"
    elif message_type == MsgType.ACK:
        return "ACK"
    elif message_type == MsgType.JOIN:
        return "JOIN"
    elif message_type == MsgType.UNJOIN:
        return "UNJOIN"
    elif message_type == MsgType.CONFIG:
        return "CONFIG"
    elif message_type == MsgType.UPDATE:
        return "UPDATE"
    elif message_type == MsgType.DATA:
        return "DATA"
    else:
        return u"{}".format(message_type)


def format_data(data):
    """
    Format bytes for printing

    :param data: Bytes
    :type data: None | bytearray | str
    :return: Printable version
    :rtype: unicode
    """
    if data is None:
        return None
    return u":".join([u"{:02x}".format(ord(c)) for c in data])


def guess_class(message_type):
    """
    Guess the class based on a message type

    :param message_type: Message type (MsgType)
    :type message_type: int
    :return: The corresponding class or None if not found
    :rtype: None | APPUnjoinMessage | APPUpdateMessage """\
    """ | APPJoinMessage | APPDataMessage | APPConfigMessage  """
    if message_type == MsgType.UNJOIN:
        return APPUnjoinMessage
    elif message_type == MsgType.UPDATE:
        return APPUpdateMessage
    elif message_type == MsgType.JOIN:
        return APPJoinMessage
    elif message_type == MsgType.DATA:
        return APPDataMessage
    elif message_type == MsgType.CONFIG:
        return APPConfigMessage
    elif message_type == MsgType.ACK:
        return APPMessage
    return None


def guess_message_type(message):
    """
    Guess the message type based on the class of message

    :param message: Message to guess the type for
    :type message: APPMessage
    :return: The corresponding message  type (MsgType) or None if not found
    :rtype: None | int
    """
    if isinstance(message, APPConfigMessage):
        return MsgType.CONFIG
    elif isinstance(message, APPJoinMessage):
        return MsgType.JOIN
    elif isinstance(message, APPDataMessage):
        # All inheriting from this first !!
        return MsgType.DATA
    elif isinstance(message, APPUpdateMessage):
        return MsgType.UPDATE
    elif isinstance(message, APPUnjoinMessage):
        return MsgType.UNJOIN
    # APPMessage -> ACK?
    return None


class APPHeader(object):
    """ Header for message """

    fmt_header = BYTE_ORDER + "BBHfHH"
    fmt_seq = BYTE_ORDER + "I"
    fmt_seq_ack = BYTE_ORDER + "I"

    def __init__(
        self, message_type=MsgType.NOT_SET, device_id=Id.NOT_SET,
        payload_length=0, flags=0,
        timestamp=None, sequence_number=None, ack_sequence_number=None,
        version_major=1, version_minor=0
    ):
        """
        Initialize object

        :param message_type: Type of message (MsgType) (default: NOT_SET)
        :type message_type: int
        :param device_id: Device id of sender (Id) (default: NOT_SET)
        :type device_id: int
        :param payload_length: Length of payload (default: 0)
        :type payload_length: int
        :param flags: Transmit flags (default: 0)
        :type flags: int
        :param timestamp: Message timestamp (default: None)
            None sets it automatically to current time
            Preferred: utc and datetime
        :type timestamp: None | float | datetime.datetime
        :param sequence_number: Sequence number of package (default: None)
            if it is None -> no sequence number
        :type sequence_number: None | int
        :param ack_sequence_number: Sequence number to be acked (default: None)
            if it is None -> no ack
        :type ack_sequence_number: None | int
        :param version_major: Major of used protocol version (default: 1)
        :type version_major: int
        :param version_minor: Minor of used protocol version (default: 0)
        :type version_minor: int
        :rtype: None
        :raises ValueError: Message type not set
        """
        super(APPHeader, self).__init__()
        if message_type is None:
            raise ValueError("Message type has to be set")
        self.message_type = message_type
        """ Type of message
            :type message_type: int """
        self.device_id = device_id
        """ Device id of sender
            :type device_id: int """
        self.payload_length = payload_length
        """ Length of payload
            :type payload_length: int """
        self.flags = flags
        """ Transmit flags
            :type flags: int """
        self._timestamp = None
        """ Timestamp of the header
            :type _timestamp: float """
        if timestamp is None:
            self.set_timestamp_to_current()
        else:
            self.timestamp = timestamp

        self.sequence_number = sequence_number
        """ Sequence number of packet - if it is None -> no number
            :type sequence_number: None | int """
        self.ack_sequence_number = ack_sequence_number
        """ Sequence number to be acked - if it is None -> no ack
            :type ack_sequence_number: None | int """
        self.version_major = version_major
        """ Major of used protocol version
            :type version_major: int """
        self.version_minor = version_minor
        """ Minor of used protocol version
            :type version_minor: int """

    @property
    def version(self):
        """
        Get readable version of used protocol version

        :return: <Major>.<Minor>
        :rtype: unicode
        """
        return u"{}.{}".format(self.version_major, self.version_minor)

    @staticmethod
    def timestamp_localize(value):
        """
        Save timestamp as utc

        :param value: Timestamp (in UTC or with tz_info)
        :type value: float | datetime.datetime
        :return: Localized timestamp
        :rtype: float
        """
        if isinstance(value, datetime.datetime):
            if not value.tzinfo:
                value = pytz.UTC.localize(value)
            else:
                value = value.astimezone(pytz.UTC)
            # Assumes utc (and add the microsecond part)
            value = calendar.timegm(value.timetuple()) + \
                value.microsecond / 1e6
        return value

    @staticmethod
    def timestamp_to_datetime(value):
        """
        Transform timestamp to datetime

        :param value: Timestamp in utc
        :type value: float
        :return: Datetime int utc
        :rtype: datetime.datetime
        """
        return pytz.UTC.localize(datetime.datetime.utcfromtimestamp(value))

    def timestamp_set(self, value):
        """
        Set the timestamp

        :param value: Timestamp (in UTC or with tz_info)
        :type value: float | datetime.datetime
        :rtype: None
        """
        self._timestamp = self.timestamp_localize(value)

    def timestamp_get(self):
        """
        Get the timestamp

        :return: If not set None, else timestamp in utc datetime object
        :rtype: None | datetime.datetime
        """
        if not self._timestamp:
            return None
        return self.timestamp_to_datetime(self._timestamp)

    timestamp = property(timestamp_get, timestamp_set)
    """ Timestamp of the header
        :type timestamp: None | datetime.datetime """

    def set_timestamp_to_current(self):
        """
        Set timestamp to current time utc

        :rtype: None
        """
        # Good form to add tzinfo
        self.timestamp = pytz.UTC.localize(datetime.datetime.utcnow())

    def pack(self, update_timestamp=False):
        """
        Pack this object into a transmittable format

        :param update_timestamp:
            Should the timestamp be updated to current (default: False)
        :type update_timestamp: bool
        :return: Packed data
        :rtype: bytearray
        :raises ValueError: Invalid device id/message type
        """
        if self.device_id <= Id.NOT_SET or not isinstance(self.device_id, int):
            raise ValueError("Invalid device id")
        if self.message_type <= MsgType.NOT_SET \
                or not isinstance(self.message_type, int) \
                or self.message_type not in list(MsgType):
            raise ValueError("Invalid message type")
        if update_timestamp or not self._timestamp:
            self.set_timestamp_to_current()
        append = b""

        if self.sequence_number is not None:
            self.flags |= Flag.SEQ
            append += struct.pack(self.fmt_seq, self.sequence_number)
        if self.ack_sequence_number is not None:
            self.flags |= Flag.ACKSEQ
            append += struct.pack(self.fmt_seq_ack, self.ack_sequence_number)

        packed = struct.pack(
            self.fmt_header,
            (self.version_major << 4) + self.version_minor,
            self.message_type,
            self.payload_length,
            self._timestamp,
            self.device_id,
            self.flags
        )
        return packed + append

    @classmethod
    def unpack(cls, data):
        """
        Unpack packed data into an instance

        :param data: Packed data
        :type data: str
        :return: Object instance and remaining data
        :rtype: (APPHeader, str)
        """
        size = struct.calcsize(APPHeader.fmt_header)
        (
            version, msg_type, payload_len,
            timestamp, device_id, flags,
        ), payload = struct.unpack(
            APPHeader.fmt_header, data[:size]
        ), data[size:]
        ack_sequence_number = None
        sequence_number = None

        if flags & Flag.ACKSEQ:
            size = struct.calcsize(APPHeader.fmt_seq_ack)
            (ack_sequence_number,), payload = struct.unpack(
                APPHeader.fmt_seq_ack, payload[:size]
            ), payload[size:]
        if flags & Flag.SEQ:
            size = struct.calcsize(APPHeader.fmt_seq)
            (sequence_number,), payload = struct.unpack(
                APPHeader.fmt_seq, payload[:size]
            ), payload[size:]
        return cls(
            message_type=msg_type,
            version_major=version >> 4,
            version_minor=version & 0xf,
            payload_length=payload_len,
            device_id=device_id,
            sequence_number=sequence_number,
            flags=flags,
            timestamp=timestamp,
            ack_sequence_number=ack_sequence_number
        ), payload

    def __str__(self):
        """
        String representation

        :return: Representation
        :rtype: str
        """
        return "<{}> ".format(type(self).__name__) + \
            "(mt:{};did:{};seq:{};pl:{};f:{};ts:{};aS:{};V:{})".format(
                format_message_type(self.message_type),
                self.device_id,
                self.sequence_number,
                self.payload_length,
                self.flags,
                self.timestamp,
                self.ack_sequence_number,
                self.version
        )

    def __unicode__(self):
        """
        Unicode representation

        :return: Representation
        :rtype: unicode
        """
        return u"<{}> ".format(type(self).__name__) + \
            u"(mt:{};did:{};seq:{};pl:{};f:{};ts:{};aS:{};V:{})".format(
                format_message_type(self.message_type),
                self.device_id,
                self.sequence_number,
                self.payload_length,
                self.flags,
                self.timestamp,
                self.ack_sequence_number,
                self.version
        )


class APPMessage(object):
    """ Base class for all messages  """

    def __init__(
            self, message_type=MsgType.NOT_SET,
            device_id=Id.REQUEST, payload=""
    ):
        """
        Initialize object

        :param message_type: Type of message (MsgType) (default: None)
            if None -> try to auto detect message type
        :type message_type: None | int
        :param device_id: Device id of sender (Id) (default: Id.REQUEST)
        :type device_id: int
        :param payload: Payload of message (default: "")
        :type payload: str
        :rtype: None
        :raises ValueError: Message type not settable
        """
        super(APPMessage, self).__init__()
        if message_type is None:
            message_type = guess_message_type(self)
        if message_type is None:
            raise ValueError("Message type not guessed")
        self._header = APPHeader(message_type, device_id)
        """ Message header
            :type _header: APPHeader """
        self._payload = b""
        """ Message payload
            :type _payload: bytearray """
        self.payload = payload
        """ Message payload
            :type payload: str """

    def update(self, obj):
        """
        Set this instance up based on another instance

        :param obj: Instance to copy from
        :type obj: APPMessage
        :rtype: None
        """
        if isinstance(obj, APPMessage):
            self._header = obj._header
            self._payload = obj._payload

    def payload_get(self):
        """
        Get the message payload

        :return: Payload
        :rtype: str
        """
        return self._payload

    def payload_set(self, value):
        """
        Set the message payload (and update header)

        :param value: New payload value
        :type value: unicode
        :rtype: None
        """
        self._payload = value
        self._header.payload_length = len(self._payload)

    payload = property(payload_get, payload_set)
    """ Message payload
        :type payload: str """

    @property
    def header(self):
        """
        Get message header

        :return: Header
        :rtype: APPHeader
        """
        return self._header

    def pack(self, update_timestamp=False, insert_before_payload=""):
        """
        Pack this object into a transmittable format

        :param update_timestamp:
            Should the timestamp be updated to current (default: False)
        :type update_timestamp: bool
        :param insert_before_payload: Insert this after this data, but before
            payload (default: "")
        :type insert_before_payload: str
        :return: Packed data
        :rtype: str
        :raises ValueError: Invalid deviceId
        """
        return self._header.pack(update_timestamp) \
            + insert_before_payload \
            + self._payload

    @classmethod
    def unpack(cls, data):
        """
        Unpack packed data into an instance

        :param data: Packed data
        :type data: str
        :return: Object instance and remaining data
        :rtype: (APPMessage, str)
        :raises ProtocolViolation: Data length smaller than payload length
        """
        header, data = APPHeader.unpack(data)

        if len(data) < header.payload_length:
            raise ProtocolViolation("Payload too small")
        payload = data[:header.payload_length]
        body = cls()
        body._header = header
        body._payload = payload
        return body, data[header.payload_length:]

    def __str__(self):
        """
        String representation

        :return: Representation
        :rtype: str
        """
        return "<{}> ({}; P:{})".format(
            type(self).__name__,
            self.header,
            format_data(self.payload)
        )

    def __unicode__(self):
        """
        Unicode representation

        :return: Representation
        :rtype: unicode
        """
        return u"<{}> ({}; P:{})".format(
            type(self).__name__,
            self.header,
            format_data(self.payload)
        )


class APPGuessMessage(APPMessage):
    """
    Same as APPMessage, but tries to automatically guess
    the message type
    """

    def __init__(self, device_id=Id.REQUEST, payload=None):
        """
        Initialize object

        :param device_id: Device id of sender (Id) (default: Id.REQUEST)
        :type device_id: int
        :param payload: Payload of message (default: "")
        :type payload: None | str | unicode
        :rtype: None
        :raises ValueError: Message type not settable
        """
        if payload is None:
            payload = ""
        super(APPGuessMessage, self).__init__(
            message_type=None,
            device_id=device_id,
            payload=payload
        )


class APPDataMessage(APPGuessMessage):
    """ Message to transmit json encoded data """

    def __init__(self, device_id=Id.REQUEST, payload=None):
        """
        Initialize object

        :param device_id: Device id of sender (Id) (default: Id.REQUEST)
        :type device_id: int
        :param payload: Payload of message (default: None)
        :type payload: None | dict
        :rtype: None
        :raises ValueError: Message type not settable
        """
        super(APPDataMessage, self).__init__(
            device_id=device_id,
            payload=""
        )
        self.payload = payload

    def payload_get(self):
        """
        Get the message payload

        :return: Payload
        :rtype: str
        """
        payload = super(APPDataMessage, self).payload_get()
        return loadJSON(payload)

    def payload_set(self, value):
        """
        Set the message payload (and update header)

        :param value: New payload value
        :type value: str
        :rtype: None
        """
        payload = saveJSON(value, pretty=False)
        super(APPDataMessage, self).payload_set(payload)

    payload = property(payload_get, payload_set)

    def __str__(self):
        """
        String representation

        :return: Representation
        :rtype: str
        """
        return "<{}> ({}; P:{})".format(
            type(self).__name__,
            self.header,
            self.payload
        )

    def __unicode__(self):
        """
        Unicode representation

        :return: Representation
        :rtype: unicode
        """
        return u"<{}> ({}; P:{})".format(
            type(self).__name__,
            self.header,
            self.payload
        )


class APPJoinMessage(APPDataMessage):
    """ Message to join audience  """
    pass


class APPConfigMessage(APPDataMessage):
    """ Message to change configuration """
    pass


class APPUnjoinMessage(APPGuessMessage):
    """ Message to leave audience  """
    pass


class APPUpdateMessage(APPMessage):
    """ Message to update people """

    fmt = BYTE_ORDER + "{}B"

    def __init__(self, device_id=Id.REQUEST, people=None):
        """
        Initialize object

        :param device_id: Device id of sender (Id) (default: REQUEST)
        :type device_id: int
        :param people: People to be transmitted (default: None)
        :type people: None | list[paps.people.People]
        :rtype: None
        :raises ValueError: Message type not settable
        """
        if people is None:
            people = []
        super(APPUpdateMessage, self).__init__(
            None, device_id, payload=self._pack_people(people)
        )

    @staticmethod
    def _pack_people(people):
        """
        Pack people into a network transmittable format

        :param people: People to pack
        :type people: list[paps.people.People]
        :return: The packed people
        :rtype: str
        """
        res = bytearray()
        bits = bytearray([1])

        for person in people:
            bits.extend(person.to_bits())
        aByte = 0

        for i, bit in enumerate(bits[::-1]):
            mod = i % 8
            aByte |= bit << mod
            if mod == 7 or i == len(bits) - 1:
                res.append(aByte)
                aByte = 0
        return struct.pack(APPUpdateMessage.fmt.format(len(res)), *res[::-1])

    def people(self):
        """
        The people list stored in payload (decoded upon every call())

        :return: The people
        :rtype: list[paps.people.People]
        :raises ProtocolViolation:
            Failed to find marker
            Wrong number of bits in payload -> cannot decode into people
        """
        people = []
        bits = bytearray()
        byts = struct.unpack(
            APPUpdateMessage.fmt.format(len(self.payload)), self.payload
        )[::-1]
        # indices = range(7, -1, -1)
        indices = range(8)
        for aByte in byts[:-1]:
            for i in indices:
                bit = aByte >> i & 1
                bits.append(bit)
        # find marker
        mark = 7
        aByte = byts[-1]
        while aByte >> mark == 0 and mark > 0:
            mark -= 1
        if aByte >> mark != 1:
            raise ProtocolViolation(u"Failed to find marker ({})".format(
                format_data(self.payload)
            ))
        # remove marker and add the rest
        for i in range(mark):
            bit = aByte >> i & 1
            bits.append(bit)

        if len(bits) % Person.BITS_PER_PERSON != 0:
            raise ProtocolViolation(
                u"Payload seems to be malformed"
                u" - Can not decode into people ({})".format(
                    format_data(self.payload)
                )
            )
        # reverse
        i = len(bits)
        while i > 0:
            p = Person()
            # select the bits for this person and bring them in the right order
            # bits is currently in reverse order
            p.from_bits(bits[i - Person.BITS_PER_PERSON:i][::-1])
            people.append(p)
            i -= Person.BITS_PER_PERSON
        return people

    def __str__(self):
        """
        String representation

        :return: Representation
        :rtype: str
        """
        return "<{}> ({}; Peps:{})".format(
            type(self).__name__,
            self.header,
            ["{}".format(person) for person in self.people()]
        )

    def __unicode__(self):
        """
        Unicode representation

        :return: Representation
        :rtype: unicode
        """
        return u"<{}> ({}; Peps:{})".format(
            type(self).__name__,
            self.header,
            [u"{}".format(person) for person in self.people()]
        )
