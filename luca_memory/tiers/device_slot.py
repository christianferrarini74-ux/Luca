"""LRU node payloads resident in device memory, not mirrored in a host cache."""

from collections import OrderedDict
from dataclasses import asdict
import hashlib
import json

from ..node import KnowledgeNode, KnowledgeSection
from .cuda import CudaMemory, DeviceMemoryError


def encode_node(node):
    return json.dumps(asdict(node), ensure_ascii=False, sort_keys=True).encode("utf-8")


def decode_node(payload):
    values = json.loads(payload)
    values["keywords"] = tuple(values["keywords"])
    values["sections"] = tuple(KnowledgeSection(**s) for s in values["sections"])
    return KnowledgeNode(**values)


class DeviceSlot:
    """Keep only IDs, allocation handles, lengths and checksums on the host."""

    def __init__(self, capacity, max_bytes, device_index=0, *, memory=None):
        if capacity < 1 or max_bytes < 2048:
            raise ValueError("Invalid device slot capacity or byte budget.")
        self.name = "VRAM"
        self.capacity, self.max_bytes = capacity, max_bytes
        self.memory = memory if memory is not None else CudaMemory(device_index)
        self._entries = OrderedDict()
        self.closed = False

    def __len__(self):
        return len(self._entries)

    def __contains__(self, node_id):
        return node_id in self._entries

    @property
    def used_bytes(self):
        return sum(entry[1] for entry in self._entries.values())

    def node_ids(self):
        return tuple(self._entries)

    def get(self, node_id):
        entry = self._entries.get(node_id)
        if entry is None:
            return None
        payload = self.memory.download(entry[0])
        if hashlib.sha256(payload).digest() != entry[2]:
            raise DeviceMemoryError(f"Device payload integrity failure for node {node_id}.")
        return decode_node(payload)

    def nodes(self):
        # Returned host objects are transient consumers, not another retained cache.
        return tuple(self.get(node_id) for node_id in self._entries)

    def promote(self, node):
        return self.promote_many([node])

    def promote_many(self, nodes):
        if self.closed:
            raise DeviceMemoryError("Device slot is closed.")
        incoming = OrderedDict((n.id, n) for n in nodes)
        payloads = {key: encode_node(n) for key, n in incoming.items()}
        if any(len(p) > self.max_bytes for p in payloads.values()):
            raise DeviceMemoryError("A complete node exceeds vram_bytes; increase the budget. No node was truncated.")
        order = [*incoming, *(key for key in self._entries if key not in incoming)]
        sizes = {key: len(payloads[key]) if key in payloads else self._entries[key][1] for key in order}
        kept = []
        used = 0
        for key in order:
            if len(kept) >= self.capacity or used + sizes[key] > self.max_bytes:
                break
            kept.append(key)
            used += sizes[key]
        removed = [key for key in reversed(self._entries) if key not in kept and key not in incoming]
        evicted = [self.get(key) for key in removed]
        evicted.extend(incoming[key] for key in reversed(incoming) if key not in kept)
        staged = {}
        try:
            for key in kept:
                if key in incoming:
                    payload = payloads[key]
                    checksum = hashlib.sha256(payload).digest()
                    previous = self._entries.get(key)
                    if previous is not None and previous[1] == len(payload) and previous[2] == checksum:
                        continue
                    pointer = self.memory.upload(payload)
                    staged[key] = (pointer, len(payload), checksum)
                    # Verify the actual round trip before replacing any existing entry.
                    if self.memory.download(pointer) != payload:
                        raise DeviceMemoryError(f"Upload verification failed for node {key}.")
        except BaseException:
            for pointer, _, _ in staged.values():
                self.memory.free(pointer)
            raise
        old = self._entries
        self._entries = OrderedDict((key, staged[key] if key in staged else old[key]) for key in kept)
        for key, entry in old.items():
            if key not in self._entries or key in staged:
                self.memory.free(entry[0])
        return evicted

    def remove(self, node_id):
        node = self.get(node_id)
        if node is not None:
            self.memory.free(self._entries[node_id][0])
            del self._entries[node_id]
        return node

    def close(self):
        if not self.closed:
            self.memory.close()
            self._entries.clear()
            self.closed = True

    def discard(self, node_id):
        """Invalidate a payload without downloading obsolete bytes."""
        entry = self._entries.pop(node_id, None)
        if entry is not None:
            self.memory.free(entry[0])
