"""Canonical families, complete metadata directories and atomic Core mutations."""

from dataclasses import asdict, dataclass
import json
import time

from .node import KnowledgeNode, save_node
from .search import MemorySearch
from .store import Edge, MemoryStore


class StaleRevision(ValueError):
    """The caller must refresh its directory or mutation plan."""


@dataclass(frozen=True, slots=True)
class DirectoryEntry:
    id: int
    title: str


@dataclass(frozen=True, slots=True)
class Directory:
    focus_id: int
    revision: int
    incoming: tuple[DirectoryEntry, ...]
    outgoing: tuple[DirectoryEntry, ...]
    parts: tuple[DirectoryEntry, ...]

    @property
    def external_degree(self):
        return len(self.incoming) + len(self.outgoing)

    def payload(self):
        return asdict(self)

    def render(self):
        return json.dumps(self.payload(), ensure_ascii=False)


class SynapticMemory:
    """One reusable memory boundary; no GUI, model provider or content distiller."""

    def __init__(self, store: MemoryStore):
        self.store = store
        self.search = MemorySearch(store)
        self._fast: Directory | None = None

    def root(self, node_id: int) -> int:
        row = self.store.connection.execute("SELECT root_id FROM family_parts WHERE part_id=?", (node_id,)).fetchone()
        return int(row[0]) if row else node_id

    def parts(self, root_id: int) -> tuple[int, ...]:
        return tuple(row[0] for row in self.store.connection.execute(
            "SELECT part_id FROM family_parts WHERE root_id=? ORDER BY part_id", (root_id,)))

    def _entries(self, query, node_id):
        return tuple(DirectoryEntry(int(row[0]), row[1]) for row in self.store.connection.execute(query, (node_id,)))

    def directory(self, node_id: int) -> Directory:
        with self.store.lock:
            root = self.root(node_id)
            revision = self.store.node_revision(root)[1]
            if revision < 0:
                raise KeyError(f"Unknown node ID: {node_id}")
            if self._fast is not None and (self._fast.focus_id, self._fast.revision) == (root, revision):
                return self._fast
            incoming = self._entries("""SELECT n.node_id,n.title FROM edges e
                JOIN node_catalog n ON n.node_id=e.source_id
                WHERE e.target_id=? AND NOT EXISTS(SELECT 1 FROM family_parts f
                    WHERE f.part_id=e.source_id AND f.root_id=e.target_id)
                ORDER BY n.node_id""", root)
            outgoing = self._entries("""SELECT n.node_id,n.title FROM edges e
                JOIN node_catalog n ON n.node_id=e.target_id
                WHERE e.source_id=? AND NOT EXISTS(SELECT 1 FROM family_parts f
                    WHERE f.part_id=e.target_id AND f.root_id=e.source_id)
                ORDER BY n.node_id""", root)
            parts = self._entries("""SELECT n.node_id,n.title FROM family_parts f
                JOIN node_catalog n ON n.node_id=f.part_id WHERE f.root_id=? ORDER BY n.node_id""", root)
            self._fast = Directory(root, revision, incoming, outgoing, parts)
            return self._fast

    def global_lookup(self, query: str, limit: int = 20) -> tuple[DirectoryEntry, ...]:
        with self.store.lock:
            exact = self.store.cells_by_alias(query.lower().strip(), limit)
            found = {cell.id: cell for cell in exact}
            for result in self.search.cells_by_text(query, limit=limit):
                found.setdefault(result.cell.id, result.cell)
            return tuple(DirectoryEntry(cell.id, KnowledgeNode.from_cell(cell).title)
                         for cell in list(found.values())[:limit])

    def _check(self, expected_revision):
        if expected_revision is not None and expected_revision != self.store.revision:
            raise StaleRevision("Memory changed; refresh the operation before retrying.")

    def _event(self, operation, data):
        self.store.record_event("synaptic_mutation", json.dumps({
            "operation": operation, "revision": self.store.revision, **data}, ensure_ascii=False).encode(), int(time.time()))

    def update_node(self, node: KnowledgeNode, *, expected_revision=None):
        with self.store.transaction():
            self._check(expected_revision)
            save_node(self.store, node)
            self._event("update_node", {"node_id": node.id})

    def connect(self, source: int, target: int, *, remove=False, expected_revision=None):
        with self.store.transaction():
            self._check(expected_revision)
            source, target = self.root(source), self.root(target)
            if remove:
                self.store.remove_edge(source, target)
            else:
                self.store.add_edge(Edge(source, target))
            self._event("disconnect" if remove else "connect", {"source": source, "target": target})

    def attach_part(self, root: int, part: int, *, expected_revision=None):
        """Explicit membership, never inferred from a hub's ordinary neighbors."""
        with self.store.transaction():
            self._check(expected_revision)
            if root == part or self.root(root) != root or self.root(part) != part or self.parts(part):
                raise ValueError("A part must be independent and families cannot be nested.")
            if self.store.cell(root) is None or self.store.cell(part) is None:
                raise ValueError("Both family nodes must exist.")
            edges = (*self.store.incoming(part), *self.store.outgoing(part))
            for edge in edges:
                self.store.remove_edge(edge.source_id, edge.target_id)
            self.store.connection.execute("INSERT INTO family_parts VALUES (?, ?)", (part, root))
            for edge in edges:
                source = root if edge.source_id == part else edge.source_id
                target = root if edge.target_id == part else edge.target_id
                if source != target:
                    self.store.add_edge(Edge(source, target))
            self.store.add_edge(Edge(root, part))
            self._event("attach_part", {"root": root, "part": part})

    def validate_step(self, reading_id: int, target: int, revision: int):
        directory = self.directory(reading_id)
        if directory.revision != revision:
            raise StaleRevision("The focus directory changed; request a fresh directory.")
        allowed = {directory.focus_id, *(entry.id for entry in (*directory.incoming, *directory.outgoing, *directory.parts))}
        if target not in allowed:
            raise ValueError("The target is not in the complete focus directory.")
        return directory.focus_id, self.root(target)
