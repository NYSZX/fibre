
import struct
import threading

import fibre
from fibre import StreamSink

class InputChannelDecoder(StreamSink):
    def __init__(self, remote_node):
        self._remote_node = remote_node
        self._logger = remote_node.get_logger()
        self._header_buf = b''
        self._in_header = True
        self._pipe_id = 0
        self._chunk_offset = 0
        self._chunk_length = 0
        self._chunk_crc = 0
    
    def process_bytes(self, buffer, timeout=None, cancellation_token=None):
        self._logger.debug("input channel decoder processing {} bytes".format(len(buffer)))
        while buffer:
            if self._in_header:
                remaining_header_length = 8 - len(self._header_buf)
                self._header_buf += buffer[:remaining_header_length]
                buffer = buffer[remaining_header_length:]
                if len(self._header_buf) >= 8:
                    (self._pipe_id, self._chunk_offset, self._chunk_crc, self._chunk_length) = struct.unpack('<HHHH', self._header_buf)
                    self._logger.debug("received chunk header: pipe {}, offset {} - {}, crc {:04X}".format(self._pipe_id, self._chunk_offset, self._chunk_offset + self._chunk_length - 1, self._chunk_crc))

                    if (self._pipe_id & 1):
                        pipe_pair = self._remote_node.get_client_pipe_pair(self._pipe_id >> 1)
                    else:
                        pipe_pair = self._remote_node.get_server_pipe_pair(self._pipe_id >> 1)
                    self._input_pipe = pipe_pair[0]
                    self._in_header = False
                    self._header_buf = b''
            else:
                actual_length = min(self._chunk_length, len(buffer))
                self._input_pipe.process_chunk(buffer[:actual_length], self._chunk_offset, self._chunk_crc)
                self._chunk_crc = fibre.calc_crc16(self._chunk_crc, buffer[:actual_length])
                buffer = buffer[actual_length:]
                self._chunk_offset += actual_length
                self._chunk_length -= actual_length

                if not self._chunk_length:
                    self._in_header = True
                    self._header_buf = b''

    def get_min_useful_bytes(self):
        if self._in_header:
            return 8 - len(self._header_buf)
        else:
            return 1
