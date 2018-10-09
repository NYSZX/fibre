"""
Provides several standard codecs for several standard data types.
A codec specifies how a certain semantic piece of information is
encoded in raw bytes.
"""

import struct
#import fibre.remote_object
import fibre
#from fibre import StreamStatus

codecs = {}

class StructCodec():
    """
    Generic serializer/deserializer based on struct pack
    """
    def __init__(self, struct_format, target_type):
        self._struct_format = struct_format
        self._target_type = target_type
    def get_length(self):
        return struct.calcsize(self._struct_format)
    def serialize(self, value):
        value = self._target_type(value)
        return struct.pack(self._struct_format, value)
    def deserialize(self, buffer):
        value = struct.unpack(self._struct_format, buffer)
        value = value[0] if len(value) == 1 else value
        return self._target_type(value)

#class EndpointRefCodec():
#    """
#    Serializer/deserializer for an endpoint reference
#    """
#    def get_length(self):
#        return struct.calcsize("<HH")
#    def serialize(self, value):
#        if value is None:
#            (ep_id, ep_crc) = (0, 0)
#        elif isinstance(value, fibre.remote_object.RemoteProperty):
#            (ep_id, ep_crc) = (value._id, value.__channel__._interface_definition_crc)
#        else:
#            raise TypeError("Expected value of type RemoteProperty or None but got '{}'. En example for a RemoteProperty is this expression: odrv0.axis0.controller._remote_attributes['pos_setpoint']".format(type(value).__name__))
#        return struct.pack("<HH", ep_id, ep_crc)
#    def deserialize(self, buffer):
#        return struct.unpack("<HH", buffer)

class StructDecoder(fibre.StreamSink):
    def __init__(self, struct_format, target_type):
        self._struct_format = struct_format
        self._target_type = target_type
        self._size = struct.calcsize(self._struct_format)
        self._buffer = b''
        self._future = fibre.Future()

    def get_future(self):
        return self._future

    def process_bytes(self, buffer):
        remaining_bytes = self._size - len(self._buffer)
        self._buffer += buffer[:remaining_bytes]
        buffer = buffer[remaining_bytes:]

        if len(self._buffer) < self._size:
            return fibre.StreamStatus.OK, buffer
        else:
            value = struct.unpack(self._struct_format, self._buffer)
            value = value[0] if len(value) == 1 else value
            self._future.set_value(self._target_type(value))
            return fibre.StreamStatus.CLOSED, buffer

class StringDecoder(fibre.StreamSink):
    def __init__(self, encoding):
        self._length_known = False
        self._raw_bytes = b''
        self._future = fibre.Future()
        self._length_decoder = StructDecoder("<I", int)

    def get_future(self):
        return self._future

    def process_bytes(self, buffer):
        if not self._length_decoder.get_future().has_value():
            status, buffer = self._length_decoder.process_bytes(buffer)
            if status != fibre.StreamStatus.CLOSED:
                return status, buffer

        if self._length_decoder.get_future().has_value():
            remaining_bytes = self._length_decoder.get_future().get_value() - len(self._raw_bytes)
            self._raw_bytes += buffer[:remaining_bytes]
            buffer = buffer[remaining_bytes:]

            if len(self._raw_bytes) >= self._length_decoder.get_future().get_value():
                self._future.set_value(self._raw_bytes.decode('ascii'))

        if buffer:
            return fibre.StreamStatus.OK, buffer
        else:
            return fibre.StreamStatus.CLOSED, buffer


codecs = {
    'i8le': { int: ((lambda: StructDecoder("<b", int)), (lambda: StructCodec("<b", int))) },
    'u8le': { int: ((lambda: StructDecoder("<B", int)), (lambda: StructCodec("<B", int))) },
    'i16le': { int: ((lambda: StructDecoder("<h", int)), (lambda: StructCodec("<h", int))) },
    'u16le': { int: ((lambda: StructDecoder("<H", int)), (lambda: StructCodec("<H", int))) },
    'i32le': { int: ((lambda: StructDecoder("<i", int)), (lambda: StructCodec("<i", int))) },
    'u32le': { int: ((lambda: StructDecoder("<I", int)), (lambda: StructCodec("<I", int))) },
    'i64le': { int: ((lambda: StructDecoder("<q", int)), (lambda: StructCodec("<q", int))) },
    'u64le': { int: ((lambda: StructDecoder("<Q", int)), (lambda: StructCodec("<Q", int))) },
    'bool': { bool: ((lambda: StructDecoder("<?", bool)), (lambda: StructCodec("<?", bool))) },
    'float': { float: ((lambda: StructDecoder("<f", float)), (lambda: StructCodec("<f", float))) },
    'ascii_string': { str: ((lambda: StringDecoder("ascii")), None) }
}

def get_codec(format_name, python_type):
    """
    Returns a suitable codec for a given (format_name, python_type) pair
    """
    all_codecs = codecs[format_name]
    if python_type is None:
        return list(all_codecs.values())[0]
    else:
        return all_codecs[python_type]

def get_python_type(format_name):
    """
    Selects a python type for which a codec is available for the specified format
    """
    return list(codecs[format_name])[0][0]

# Which codecs should be assumed active if nothing else has been negotiated
canonical_formats = {
    "number": "i32le",
    "json": "ascii_string",
}

#codecs[fibre.remote_object.RemoteProperty] = {
#    'endpoint_ref': EndpointRefCodec()
#}

