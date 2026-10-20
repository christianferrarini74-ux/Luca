"""Revision-aware access without retaining another host payload copy."""


class CoherentSlot:
    def __init__(self, slot, store):
        self.slot, self.store = slot, store
        self._revisions = {}

    def __getattr__(self, name):
        return getattr(self.slot, name)

    def _purge(self):
        for node_id in self.slot.node_ids():
            if self._revisions.get(node_id) != self.store.node_revision(node_id)[0]:
                self.slot.discard(node_id)
                self._revisions.pop(node_id, None)

    def __len__(self):
        return len(self.node_ids())

    def __contains__(self, node_id):
        return node_id in self.node_ids()

    @property
    def used_bytes(self):
        with self.store.lock:
            self._purge()
            return self.slot.used_bytes

    def node_ids(self):
        with self.store.lock:
            self._purge()
            return self.slot.node_ids()

    def get(self, node_id):
        with self.store.lock:
            self._purge()
            return self.slot.get(node_id)

    def nodes(self):
        with self.store.lock:
            self._purge()
            return self.slot.nodes()

    def promote_many(self, nodes):
        with self.store.lock:
            self._purge()
            nodes = list(nodes)
            evicted = self.slot.promote_many(nodes)
            for node in nodes:
                if node.id in self.slot:
                    self._revisions[node.id] = self.store.node_revision(node.id)[0]
            self._revisions = {key: value for key, value in self._revisions.items() if key in self.slot}
            return evicted

    def promote(self, node):
        return self.promote_many([node])

    def remove(self, node_id):
        with self.store.lock:
            self._purge()
            self._revisions.pop(node_id, None)
            return self.slot.remove(node_id)

    def close(self):
        self.slot.close()
        self._revisions.clear()
