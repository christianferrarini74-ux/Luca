"""Exercise the narrow tokenizer transport without external network services."""

import base64
import hashlib
import json
import struct
import unittest
from unittest.mock import patch

from luca_memory.llm.tokenization import _RPCSocket, LMStudioTokenCounter
from luca_memory.llm.lmstudio import LMStudioModelManager
from luca_memory.llm.models import LLMConfigurationError


def frame(body, opcode=1, final=True):
    if isinstance(body, dict):
        body = json.dumps(body).encode()
    size = len(body)
    header = bytes([(128 if final else 0) | opcode, size if size < 126 else 126 if size < 65536 else 127])
    if size >= 126:
        header += struct.pack("!H" if size < 65536 else "!Q", size)
    return header + body


class FakeSocket:
    def __init__(self, response=b"", valid_handshake=True):
        self.incoming = b""
        self.response = response
        self.sent = []
        self.closed = False
        self.valid_handshake = valid_handshake

    def sendall(self, data):
        self.sent.append(data)
        if data.startswith(b"GET "):
            key = data.split(b"Sec-WebSocket-Key: ")[1].split(b"\r\n")[0]
            accept = base64.b64encode(hashlib.sha1(key + b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11").digest())
            if not self.valid_handshake:
                accept = b"invalid"
            self.incoming = b"HTTP/1.1 101 Switching Protocols\r\nSec-WebSocket-Accept: " + accept + b"\r\n\r\n" + self.response

    def recv(self, length):
        # Deliberately fragment every socket read.
        size = min(length, 17)
        value, self.incoming = self.incoming[:size], self.incoming[size:]
        return value

    def close(self):
        self.closed = True


class TokenTransportTests(unittest.TestCase):
    def test_rpc_authentication_and_result_close_the_connection(self):
        fake = FakeSocket(frame({"success": True}) + frame({"type": "rpcResult", "callId": 1, "result": {"tokenCount": 5}}))
        counter = LMStudioTokenCounter(LMStudioModelManager("http://localhost:1234"), "model")
        with patch("luca_memory.llm.tokenization.socket.create_connection", return_value=fake):
            self.assertEqual(counter.count("Ciao"), 5)
        self.assertTrue(fake.closed)
        self.assertEqual(fake.sent[-1][0] & 15, 8)

    def test_authentication_failure_does_not_fall_back_or_leak(self):
        fake = FakeSocket(frame({"success": False}))
        counter = LMStudioTokenCounter(LMStudioModelManager("http://localhost:1234"), "model")
        with patch("luca_memory.llm.tokenization.socket.create_connection", return_value=fake):
            with self.assertRaises(LLMConfigurationError):
                counter.count("Ciao")
        self.assertTrue(fake.closed)

    def test_invalid_handshake_closes_socket(self):
        fake = FakeSocket(valid_handshake=False)
        with patch("luca_memory.llm.tokenization.socket.create_connection", return_value=fake):
            with self.assertRaises(ValueError):
                _RPCSocket("http://localhost:1234", 2)
        self.assertTrue(fake.closed)

    def test_fragmented_message_with_interleaved_ping(self):
        fake = FakeSocket(frame(b'{"token', final=False) + frame(b"ping", opcode=9) + frame(b'Count": 9}', opcode=0))
        with patch("luca_memory.llm.tokenization.socket.create_connection", return_value=fake):
            connection = _RPCSocket("http://localhost:1234", 2)
            try:
                self.assertEqual(connection.receive(), {"tokenCount": 9})
                self.assertEqual(fake.sent[-1][0] & 15, 10)
            finally:
                connection.close()

    def test_all_client_length_formats_are_masked_and_lossless(self):
        fake = FakeSocket()
        with patch("luca_memory.llm.tokenization.socket.create_connection", return_value=fake):
            connection = _RPCSocket("http://localhost:1234", 2)
            try:
                for size in (2, 1000, 70000):
                    payload = {"text": "x" * size}
                    connection.send(payload)
                    data = fake.sent[-1]
                    self.assertTrue(data[1] & 128)
                    length = data[1] & 127
                    offset = 2 + (2 if length == 126 else 8 if length == 127 else 0)
                    mask, body = data[offset:offset + 4], data[offset + 4:]
                    self.assertEqual(json.loads(bytes(value ^ mask[i % 4] for i, value in enumerate(body))), payload)
            finally:
                connection.close()

    def test_oversized_response_is_rejected_before_reading_payload(self):
        fake = FakeSocket(bytes([129, 127]) + struct.pack("!Q", _RPCSocket.MAX_MESSAGE + 1))
        with patch("luca_memory.llm.tokenization.socket.create_connection", return_value=fake):
            connection = _RPCSocket("http://localhost:1234", 2)
            try:
                with self.assertRaises(ValueError):
                    connection.receive()
            finally:
                connection.close()
