"""Confirmed local edge regrouping with versioned plans and guarded restoration."""

import json
import threading
import time
from dataclasses import asdict, dataclass

from .maintenance_selection import select_groups
from .node import KnowledgeNode, save_node
from .store import Edge
from .synaptic import StaleRevision


@dataclass(frozen=True)
class EdgeGroup:
    title: str
    direction: str
    members: tuple[int, ...]


@dataclass(frozen=True)
class MaintenancePlan:
    root_id: int
    revision: int
    degree_before: int
    degree_after: int
    groups: tuple[EdgeGroup, ...]

    def payload(self):
        return asdict(self)


class MemoryMaintenance:
    """Separate proposal validation, atomic application and guarded undo."""
    def __init__(self, memory, settings):
        self.memory, self.store, self.settings = memory, memory.store, settings

    def candidates(self):
        """Only over-upper independent identities are eligible for automatic sleep."""
        rows = self.store.connection.execute("""SELECT d.cell_id FROM cell_degrees d
            WHERE d.in_degree+d.out_degree > ?
              AND NOT EXISTS(SELECT 1 FROM family_parts f WHERE f.part_id=d.cell_id)
            ORDER BY d.cell_id""", (self.settings.edge_upper,))
        return tuple(row[0] for row in rows
                     if self.memory.directory(row[0]).external_degree > self.settings.edge_upper)

    def plan(self, node_id, proposed_groups):
        """Calculate degree reduction against a versioned directory without changing memory."""
        with self.store.lock:
            directory = self.memory.directory(node_id)
            degree = directory.external_degree
            if degree <= self.settings.edge_target:
                return MaintenancePlan(directory.focus_id, directory.revision, degree, degree, ())
            if not isinstance(proposed_groups, list):
                # Preserve the existing ValueError contract used by validation callers.
                raise ValueError("A list of directional groups is required.")  # noqa: TRY004
            allowed = {"incoming": {entry.id for entry in directory.incoming},
                       "outgoing": {entry.id for entry in directory.outgoing}}
            seen = set()
            groups = []
            for raw in proposed_groups:
                if not isinstance(raw, dict):
                    # Preserve the existing ValueError contract used by validation callers.
                    raise ValueError("Each group must be an object.")  # noqa: TRY004
                title, direction, members = raw.get("title"), raw.get("direction"), raw.get("members")
                if not isinstance(title, str) or not title.strip() or len(title) > 256:
                    raise ValueError("Groups need a nonempty title of at most 256 characters.")
                if direction not in allowed or not isinstance(members, list) or not 2 <= len(members) <= self.settings.edge_upper - 1:
                    raise ValueError("Groups need a direction and 2..edge_upper-1 members.")
                for member in members:
                    key = direction, member
                    if type(member) is not int or member == directory.focus_id or member not in allowed[direction] or key in seen:
                        raise ValueError("Group members must be distinct existing directional alternatives.")
                    seen.add(key)
                groups.append(EdgeGroup(title.strip(), direction, tuple(members)))
            # Preserve each proposed group intact, but never apply unnecessary regrouping.
            selected = select_groups(groups, degree - self.settings.edge_target)
            after = degree - sum(len(group.members) - 1 for group in selected)
            return MaintenancePlan(directory.focus_id, directory.revision, degree, after, selected)

    def apply(self, plan: MaintenancePlan, *, confirmed=False, automatic=False):
        """Replace local routes and persist their undo record in the same transaction."""
        with self.store.transaction():
            current = self.memory.directory(plan.root_id)
            if current.revision != plan.revision:
                raise StaleRevision("The maintenance plan is stale; prepare it again.")
            if automatic and current.external_degree <= self.settings.edge_upper:
                return None
            if not automatic and confirmed is not True:
                raise ValueError("Manual maintenance requires explicit confirmation.")
            # Revalidate public plan objects rather than trusting client/deserialized fields.
            checked = self.plan(plan.root_id, [{"title": g.title, "direction": g.direction, "members": list(g.members)} for g in plan.groups])
            if checked != plan:
                raise ValueError("Invalid maintenance plan.")
            if not plan.groups:
                return None
            before = []
            added = []
            created = []
            for group in plan.groups:
                node_id = self.store.next_cell_id()
                node = KnowledgeNode(node_id, f"navigation_group_{node_id}", group.title,
                                     f"Navigation index: {group.title}")
                save_node(self.store, node)
                created.append(node_id)
                connector = (plan.root_id, node_id) if group.direction == "outgoing" else (node_id, plan.root_id)
                self.store.add_edge(Edge(*connector))
                added.append(connector)
                for member in group.members:
                    original = (plan.root_id, member) if group.direction == "outgoing" else (member, plan.root_id)
                    row = self.store.connection.execute("SELECT last_used_at,use_count FROM edges WHERE source_id=? AND target_id=?", original).fetchone()
                    before.append([*original, row[0], row[1]])
                    self.store.remove_edge(*original)
                    replacement = (node_id, member) if group.direction == "outgoing" else (member, node_id)
                    self.store.add_edge(Edge(*replacement))
                    self.store.connection.execute("UPDATE edges SET last_used_at=?,use_count=? WHERE source_id=? AND target_id=?",
                                                  (row[0], row[1], *replacement))
                    added.append(replacement)
            if self.memory.directory(plan.root_id).external_degree != plan.degree_after:
                raise ValueError("Maintenance did not produce its planned degree.")
            # Restoration must detect edits to generated nodes, aliases and routes, not just degree.
            record = {"plan": plan.payload(), "original_edges": before, "added_edges": added,
                      "created_ids": created,
                      "created_aliases": {str(nid): [row[0] for row in self.store.connection.execute(
                          "SELECT alias FROM cell_aliases WHERE cell_id=? ORDER BY alias", (nid,))] for nid in created},
                      "created_nodes": {str(nid): self.store.cell(nid).content.decode("utf-8") for nid in created}}
            cursor = self.store.connection.execute("INSERT INTO maintenance_operations(payload,active) VALUES (?,1)", (json.dumps(record),))
            operation_id = cursor.lastrowid
            self.memory._event("regroup", {"operation_id": operation_id, "root_id": plan.root_id})
            return operation_id

    def restore(self, operation_id, *, confirmed=False):
        """Undo only an unchanged grouping, preserving usage gained on replacement routes."""
        if confirmed is not True:
            raise ValueError("Restoration requires explicit confirmation.")
        with self.store.transaction():
            row = self.store.connection.execute("SELECT payload,active FROM maintenance_operations WHERE id=?", (operation_id,)).fetchone()
            if row is None or not row[1]:
                raise ValueError("Unknown or already restored maintenance operation.")
            record = json.loads(row[0])
            expected_edges = {tuple(edge) for edge in record["added_edges"]}
            for node_id in record["created_ids"]:
                actual = {(e.source_id, e.target_id) for e in (*self.store.incoming(node_id), *self.store.outgoing(node_id))}
                expected = {edge for edge in expected_edges if node_id in edge}
                cell = self.store.cell(node_id)
                aliases = [row[0] for row in self.store.connection.execute(
                    "SELECT alias FROM cell_aliases WHERE cell_id=? ORDER BY alias", (node_id,))]
                if actual != expected or aliases != record.get("created_aliases", {}).get(str(node_id)) or self.memory.root(node_id) != node_id or self.memory.parts(node_id) or cell is None or cell.content.decode("utf-8") != record["created_nodes"][str(node_id)]:
                    raise StaleRevision("A grouping node changed; restoration requires a new explicit migration.")
            for source, target, _, _ in record["original_edges"]:
                if self.store.edge(source, target):
                    raise StaleRevision("An original route was recreated; refusing to overwrite its state.")
            # Preserve reinforcement accrued on the replacement route during use.
            usage = {}
            for source, target in record["added_edges"]:
                row = self.store.connection.execute("SELECT last_used_at,use_count FROM edges WHERE source_id=? AND target_id=?", (source, target)).fetchone()
                usage[source, target] = tuple(row)
                self.store.remove_edge(source, target)
            for source, target, last_used, count in record["original_edges"]:
                replacement = next(edge for edge in expected_edges
                    if (edge[0] in record["created_ids"] and edge[1] == target and source == record["plan"]["root_id"])
                    or (edge[1] in record["created_ids"] and edge[0] == source and target == record["plan"]["root_id"]))
                last_used, count = max(last_used, usage[replacement][0]), max(count, usage[replacement][1])
                self.store.add_edge(Edge(source, target))
                self.store.connection.execute("UPDATE edges SET last_used_at=?,use_count=? WHERE source_id=? AND target_id=?", (last_used, count, source, target))
            # Remove only unmodified grouping nodes created by this exact operation.
            for node_id in record["created_ids"]:
                self.store.connection.execute("DELETE FROM cell_aliases WHERE cell_id=?", (node_id,))
                self.store.connection.execute("DELETE FROM cell_search WHERE rowid=?", (node_id,))
                self.store.connection.execute("DELETE FROM entry_search WHERE rowid=?", (node_id,))
                self.store.connection.execute("DELETE FROM cells WHERE id=?", (node_id,))
            self.store.connection.execute("UPDATE maintenance_operations SET active=0 WHERE id=?", (operation_id,))
            self.memory._event("restore", {"operation_id": operation_id})


class IdleMaintenance:
    """Owned worker: serialize model calls and cancel idle proposals on renewed input."""

    def __init__(self, maintenance, adapter):
        self.maintenance, self.adapter = maintenance, adapter
        self.settings = maintenance.settings
        self.last_activity = time.monotonic()
        self.last_error = None
        self.last_operation = None
        self._attempted = {}
        self._stop = threading.Event()
        self._thread = None

    def touch(self):
        # Called before waiting for the Core lock so pending user input cancels a plan.
        self.last_activity = time.monotonic()

    def run_once(self, *, now=None):
        """Attempt at most one idle proposal; new input cancels it before any write."""
        if self._stop.is_set() or not self.settings.automatic_sleep or not hasattr(self.adapter, "propose_groups"):
            return None
        now = time.monotonic() if now is None else now
        if now - self.last_activity < self.settings.idle_seconds:
            return None
        with self.maintenance.store.lock:
            activity = self.last_activity
            if self._stop.is_set() or now - activity < self.settings.idle_seconds:
                return None
            for root in self.maintenance.candidates():
                directory = self.maintenance.memory.directory(root)
                # Back off by directory revision: unrelated edits do not restart failed work.
                previous = self._attempted.get(root)
                if previous and previous[0] == directory.revision and now - previous[1] < self.settings.sleep_retry_seconds:
                    continue
                self._attempted[root] = (directory.revision, now)
                try:
                    groups = self.adapter.propose_groups(directory, self.settings)
                    if self._stop.is_set() or self.last_activity != activity:
                        self._attempted.pop(root, None)
                        return None
                    plan = self.maintenance.plan(root, groups)
                    self.last_operation = self.maintenance.apply(plan, automatic=True)
                    self.last_error = None
                    return self.last_operation
                # Keep worker failures visible without terminating idle maintenance.
                except Exception as error:  # noqa: BLE001
                    # Keep the worker alive and expose failure, never invent a grouping.
                    self.last_error = str(error)
                    return None
        return None

    def start(self):
        if self._thread is None and self.settings.automatic_sleep and hasattr(self.adapter, "propose_groups"):
            self._thread = threading.Thread(target=self._run, name="luca-memory-sleep", daemon=True)
            self._thread.start()

    def _run(self):
        while not self._stop.wait(self.settings.sleep_poll_seconds):
            try:
                self.run_once()
            # Keep worker failures visible without terminating idle maintenance.
            except Exception as error:  # noqa: BLE001
                self.last_error = str(error)

    def close(self):
        """Join the owned worker before closing the database or unloading tier storage."""
        self._stop.set()
        if self._thread is not None:
            self._thread.join()
