"""Model-native token counting through LM Studio's narrowly scoped SDK RPCs.

No inference, model download, tokenizer copy or third-party runtime is required.
The wire schemas follow lmstudio-ai/lmstudio-python (countTokens and
applyPromptTemplate). Each operation closes its WebSocket deterministically.
"""

import base64
import hashlib
import json
import os
import socket
import ssl
import struct
import uuid
from collections import OrderedDict
from threading import Lock
from urllib.parse import urlsplit

from .models import LLMConfigurationError


class _RPCSocket:
    """Bounded synchronous RFC 6455 transport for request/response RPC only."""

    MAX_MESSAGE = 16 * 1024 * 1024

    def __init__(self, url, timeout):
        address = urlsplit(url)
        self.socket = socket.create_connection((address.hostname, address.port or (443 if address.scheme == "https" else 80)), timeout)
        self.buffer = b""
        try:
            if address.scheme == "https":
                self.socket = ssl.create_default_context().wrap_socket(self.socket, server_hostname=address.hostname)
            key = base64.b64encode(os.urandom(16)).decode()
            request = (f"GET {address.path.rstrip('/')}/llm HTTP/1.1\r\nHost: {address.netloc}\r\n"
                       f"Upgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: {key}\r\n"
                       "Sec-WebSocket-Version: 13\r\n\r\n")
            self.socket.sendall(request.encode("ascii"))
            while b"\r\n\r\n" not in self.buffer:
                self.buffer += self._receive()
                if len(self.buffer) > 65536:
                    raise ValueError("Oversized WebSocket handshake")
            header, self.buffer = self.buffer.split(b"\r\n\r\n", 1)
            expected = base64.b64encode(hashlib.sha1((key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode()).digest()).decode()
            lines = header.decode("ascii").split("\r\n")
            headers = {name.lower(): value.strip() for name, value in (line.split(":", 1) for line in lines[1:] if ":" in line)}
            if " 101 " not in lines[0] or headers.get("sec-websocket-accept", "") != expected:
                raise ValueError("Invalid WebSocket handshake")
        except BaseException:
            self.socket.close()
            raise

    def _receive(self):
        data = self.socket.recv(65536)
        if not data:
            raise ConnectionError("Tokenizer connection closed")
        return data

    def _read(self, length):
        while len(self.buffer) < length:
            self.buffer += self._receive()
        value, self.buffer = self.buffer[:length], self.buffer[length:]
        return value

    def send(self, payload, opcode=1):
        body = json.dumps(payload, ensure_ascii=False).encode() if opcode == 1 else payload
        if len(body) > self.MAX_MESSAGE:
            raise ValueError("Tokenizer request exceeds transport limit")
        length = len(body)
        prefix = bytes([0x80 | opcode, 0x80 | (length if length < 126 else 126 if length < 65536 else 127)])
        if length >= 126:
            prefix += struct.pack("!H" if length < 65536 else "!Q", length)
        mask = os.urandom(4)
        self.socket.sendall(prefix + mask + bytes(value ^ mask[index % 4] for index, value in enumerate(body)))

    def receive(self):
        chunks, total = [], 0
        while True:
            first, second = self._read(2)
            length = second & 127
            if second & 128 or first & 0x70:
                raise ValueError("Unexpected masked or compressed server frame")
            if length >= 126:
                length = struct.unpack("!H" if length == 126 else "!Q", self._read(2 if length == 126 else 8))[0]
            if length + total > self.MAX_MESSAGE:
                raise ValueError("Tokenizer response exceeds transport limit")
            body = self._read(length)
            opcode = first & 15
            if opcode == 8:
                raise ConnectionError("Tokenizer closed its WebSocket")
            if opcode == 9:
                self.send(body, 10)
                continue
            if opcode == 10:
                continue
            if opcode not in (0, 1) or (not chunks and opcode != 1) or (chunks and opcode != 0):
                raise ValueError("Invalid tokenizer message frame")
            chunks.append(body)
            total += length
            if first & 128:
                return json.loads(b"".join(chunks))

    def close(self):
        try:
            self.send(b"", 8)
        except OSError:
            pass
        finally:
            self.socket.close()


class LMStudioTokenCounter:
    accounting = "model_tokens"

    def __init__(self, manager, model):
        self.manager, self.model = manager, model
        self.cache = OrderedDict()
        self.cache_lock = Lock()

    def _rpc(self, endpoint, parameter):
        connection = None
        try:
            connection = _RPCSocket(self.manager.management_url, self.manager.timeout_seconds)
            auth = {"authVersion": 1, "clientIdentifier": "guest:" + str(uuid.uuid4()), "clientPasskey": str(uuid.uuid4())}
            if self.manager.api_key:
                identifier, passkey = self.manager.api_key.removeprefix("sk-lm-").split(":", 1)
                auth.update(clientIdentifier=identifier, clientPasskey=passkey)
            connection.send(auth)
            authentication = connection.receive()
            if not isinstance(authentication, dict) or authentication.get("success") is not True:
                raise ValueError("Tokenizer authentication failed")
            connection.send({"type": "rpcCall", "endpoint": endpoint, "callId": 1, "parameter": parameter})
            response = connection.receive()
            if not isinstance(response, dict) or response.get("type") != "rpcResult" or response.get("callId") != 1:
                raise ValueError("Tokenizer RPC failed")
            result = response["result"]
            if not isinstance(result, dict):
                # Preserve the existing ValueError contract used by validation callers.
                raise ValueError("Invalid tokenizer RPC result")  # noqa: TRY004
            return result
        except (OSError, ValueError, KeyError, TypeError) as error:
            raise LLMConfigurationError("Conteggio token LM Studio non disponibile; nessuna stima in byte viene usata al suo posto.") from error
        finally:
            if connection is not None:
                connection.close()

    def _parameters(self):
        return {"specifier": {"type": "query", "query": {"identifier": self.model}}}

    def count(self, text):
        if not text:
            return 0
        key = hashlib.sha256(text.encode()).digest()
        with self.cache_lock:
            if key in self.cache:
                self.cache.move_to_end(key)
                return self.cache[key]
        value = self._rpc("countTokens", {**self._parameters(), "inputString": text})["tokenCount"]
        if type(value) is not int or value < 0:
            raise LLMConfigurationError("LM Studio ha restituito un conteggio token non valido.")
        with self.cache_lock:
            self.cache[key] = value
            if len(self.cache) > 256:
                self.cache.popitem(last=False)
        return value

    def messages(self, messages):
        history = {"messages": [{"role": item["role"], "content": [{"type": "text", "text": item["content"]}]} for item in messages]}
        formatted = self._rpc("applyPromptTemplate", {**self._parameters(), "history": history,
                              "predictionConfigStack": {"layers": []}, "opts": {}})["formatted"]
        if not isinstance(formatted, str) or not formatted:
            raise LLMConfigurationError("LM Studio non ha restituito il template del prompt.")
        return self.count(formatted)
