"""Synaptic Carousel coordinating VRAM <-> RAM <-> SSD and 1st-degree cluster recall."""

from __future__ import annotations

from dataclasses import dataclass
import json
import time
from typing import Iterable, Literal

from ..node import KnowledgeNode, load_node
from ..store import ConvergenceResult, Edge, MemoryStore
from ..activity import MemoryActivity
from ..budget import PromptBudget
from .graph_view import GraphView
from .slot import TierSlot
from .device_slot import DeviceSlot
from .coherent_slot import CoherentSlot
from ..synaptic import SynapticMemory, serialized


@dataclass(frozen=True, slots=True)
class RecallEvent:
    """Record of a synaptic recall into VRAM."""

    center_id: int
    incoming_edges: tuple[Edge, ...]
    outgoing_edges: tuple[Edge, ...]
    first_degree_ids: tuple[int, ...]
    evicted_to_ram: tuple[int, ...]
    evicted_to_ssd: tuple[int, ...]


class SynapticCarousel:
    """Manage VRAM, RAM, and SSD movement with strict 1st-degree prefix:suffix recall."""

    def __init__(
        self,
        store: MemoryStore,
        *,
        vram_capacity: int = 16,
        ram_capacity: int = 64,
        search_policy: str = "fast",
        recent_window: int = 8,
        vram_bytes: int = 8_000_000,
        ram_bytes: int = 32_000_000,
        prompt_budget: PromptBudget | None = None,
        memory_backend: str = "host",
        gpu_device: int = 0,
    ) -> None:
        self.store = store
        self.synaptic = SynapticMemory(store)
        self.focus_id: int | None = None
        self.reading_id: int | None = None
        if search_policy not in {"fast", "complete"}:
            raise ValueError("search_policy must be 'fast' or 'complete'.")
        self.search_policy = search_policy
        if memory_backend not in {"host", "cuda"}:
            raise ValueError("memory_backend must be 'host' or 'cuda'.")
        self.memory_backend, self.gpu_device = memory_backend, gpu_device
        self.ram = CoherentSlot(TierSlot("RAM", ram_capacity, ram_bytes, compact=memory_backend != "cuda"), store)
        self.prompt_budget = prompt_budget or PromptBudget()
        self.context_report: dict = {}
        self.section_focus: tuple[int, str] | None = None
        self.vram_graph = GraphView()
        self.ram_graph = GraphView()
        self.expanded_in_vram: set[int] = set()
        self.opened_in_session: set[int] = set()
        self.activity = MemoryActivity(recent_window)
        self.last_convergence: ConvergenceResult | None = None
        self.previous_convergence: ConvergenceResult | None = None
        self._clock = int(time.time())
        self.disk_loads = 0
        self.disk_payload_bytes = 0
        # Acquire external resources only after validating all host-side state.
        slot = DeviceSlot(vram_capacity, vram_bytes, gpu_device) if memory_backend == "cuda" else TierSlot("HOST", vram_capacity, vram_bytes)
        self.vram = CoherentSlot(slot, store)

    def _next_tick(self) -> int:
        self._clock = max(self._clock + 1, int(time.time()))
        return self._clock

    def begin_turn(self) -> None:
        """Archive query diagnostics without resetting the persistent working memory."""
        if self.last_convergence is not None:
            self.previous_convergence = self.last_convergence
        self.last_convergence = None
        self.context_report = {}
        self.activity.advance()
        self.opened_in_session = set(self.activity.recent)

    def synchronize(self):
        """Refresh topology metadata without downloading resident payloads."""
        valid = set(self.vram.node_ids())
        self.expanded_in_vram.intersection_update(valid)
        if self.reading_id is not None:
            if self.store.cell(self.reading_id) is None:
                self.reading_id = self.focus_id = None
            else:
                self.focus_id = self.synaptic.root(self.reading_id)
        self.vram_graph = GraphView()
        for node_id in valid:
            self.vram_graph.add_edges(edge for edge in self.store.outgoing(node_id)
                                      if edge.target_id in valid)

    def open_alternative(self, node_id: int) -> RecallEvent:
        """Open a registered alternative only after an explicit user selection."""
        convergence = self.last_convergence or self.previous_convergence
        if convergence is None or node_id not in {
            match.node_id for match in convergence.available_alternatives
        }:
            raise ValueError("The node is not an available search alternative.")
        started = time.perf_counter()
        event = self.step_to(node_id)
        opened = tuple(dict.fromkeys((*convergence.opened_ids, node_id)))
        self.previous_convergence = convergence.with_recall_outcome(
            opened, convergence.recall_ms + (time.perf_counter() - started) * 1000
        )
        self.last_convergence = None
        self.context_report = {}
        return event

    @serialized
    def recall(self, node_id: int) -> RecallEvent:
        """Open a reading part and preload bounded contents, never truncate its directory."""

        if self.section_focus is not None and self.section_focus[0] != node_id:
            self.section_focus = None
        center = self._fetch_node(node_id)
        if center is None:
            raise KeyError(f"Unknown node ID: {node_id}")

        self.activity.advance()
        self.opened_in_session = set(self.activity.recent)

        tick = self._next_tick()
        directory = self.synaptic.directory(node_id)
        root = directory.focus_id
        incoming_ids = {entry.id for entry in directory.incoming}
        outgoing_ids = {entry.id for entry in directory.outgoing}
        incoming = tuple(edge for edge in self.store.incoming(root) if edge.source_id in incoming_ids)
        outgoing = tuple(edge for edge in self.store.outgoing(root) if edge.target_id in outgoing_ids)

        neighbour_ids: list[int] = []
        for edge in (*outgoing, *incoming):
            other_id = edge.target_id if edge.source_id == root else edge.source_id
            if other_id != node_id and other_id not in neighbour_ids:
                neighbour_ids.append(other_id)

        with self.store.transaction():
            center = center.with_recall(tick)
            if self._is_knowledge_cell(center.id):
                self.store.record_node_usage(center.id, tick, initial_count=center.recall_count - 1)

        max_neighbours = max(0, self.vram.capacity - 1)
        if len(neighbour_ids) > max_neighbours:
            active_nb = [nid for nid in neighbour_ids if nid in self.opened_in_session]
            cold_nb = [nid for nid in neighbour_ids if nid not in self.opened_in_session]
            selected_neighbour_ids = (active_nb + cold_nb)[:max_neighbours]
        else:
            selected_neighbour_ids = neighbour_ids[:max_neighbours]
        neighbours: list[KnowledgeNode] = []
        for neighbour_id in selected_neighbour_ids:
            node = self._fetch_node(neighbour_id)
            if node is not None:
                neighbours.append(node)

        batch = [center, *neighbours]
        evicted_from_vram = self.vram.promote_many(batch)
        # Do not discard host copies until the device transaction succeeds.
        for node in batch:
            self.ram.remove(node.id)
        self.focus_id, self.reading_id = root, node_id
        self.expanded_in_vram.add(center.id)
        self.activity.record("open", center.id)
        for neighbor in neighbours:
            self.activity.record("preload", neighbor.id)
        self.opened_in_session = set(self.activity.recent)
        self.vram_graph.add_edges((*incoming, *outgoing))
        self.vram_graph.add_edges(Edge(root, entry.id) for entry in directory.parts)

        # Only nodes actually evicted from VRAM slide into RAM; excess unchosen family members stay in SSD.
        to_ram = list(evicted_from_vram)
        for item in to_ram:
            self.expanded_in_vram.discard(item.id)
        self.expanded_in_vram.intersection_update(self.vram.node_ids())

        removed_vram_edges = self.vram_graph.prune_to_nodes(set(self.vram.node_ids()))
        self.ram_graph.add_edges(removed_vram_edges)

        evicted_from_ram = self.ram.promote_many(to_ram) if to_ram else []
        for node in to_ram:
            self.activity.record("demote_ram", node.id)
        for node in evicted_from_ram:
            self.activity.record("demote_ssd", node.id)
        self.ram_graph.prune_to_nodes(set(self.ram.node_ids()) | set(self.vram.node_ids()))

        return RecallEvent(
            center_id=center.id,
            incoming_edges=incoming,
            outgoing_edges=outgoing,
            first_degree_ids=tuple(neighbour_ids),
            evicted_to_ram=tuple(item.id for item in to_ram),
            evicted_to_ssd=tuple(item.id for item in evicted_from_ram),
        )

    @serialized
    def step_to(self, node_id: int, *, reinforce: bool = True) -> RecallEvent:
        """Shift thought focus onto `node_id` (e.g. a 1st-degree neighbour), opening its own cluster."""

        previous = self.focus_id
        event = self.recall(node_id)
        target = self.focus_id
        if previous is not None and previous != target and reinforce:
            edges = [self.store.edge(previous, target), self.store.edge(target, previous)]
            with self.store.transaction():
                for edge in edges:
                    if edge:
                        self.store.touch_edge(edge.source_id, edge.target_id, self._next_tick())
            if any(edges):
                self.activity.record("traverse", node_id, previous)
        return event

    def mark_exposed(self, node_ids: Iterable[int], *, read_ids: Iterable[int] = ()) -> None:
        """Record successful prompt exposure, distinct from verified answer correctness."""
        valid = (set(self.vram.node_ids()) & self.expanded_in_vram) | set(read_ids)
        with self.store.transaction():
            for node_id in set(node_ids) & valid:
                if self.store.connection.execute("SELECT 1 FROM cells WHERE id=?", (node_id,)).fetchone() is None:
                    continue
                self.store.record_node_usage(node_id, self._next_tick(), exposed=True)
                self.activity.record("expose", node_id)
        self.opened_in_session = set(self.activity.recent)

    def reinforce_supports(self, node_id: int, anchors: Iterable[int]) -> None:
        """Reinforce only existing links used to justify this selected recall."""
        with self.store.transaction():
            for anchor in set(anchors) - {node_id}:
                for edge in (self.store.edge(anchor, node_id), self.store.edge(node_id, anchor)):
                    if edge:
                        self.store.touch_edge(edge.source_id, edge.target_id, self._next_tick())
                        self.activity.record("associate", node_id, anchor)

    def recall_with_convergence(
        self,
        seed_ids: Iterable[int],
        *,
        mode: Literal["strict", "associative"] = "strict",
        convergence_threshold: int = 2,
        max_open: int | None = None,
        associative_max_open: int = 1,
    ) -> list[RecallEvent]:
        """Search candidate intersections on the full SSD graph first, then preload clusters and open top candidate(s).

        By default (`max_open=None`), only the single best candidate (`opened_ids[:1]`) is opened with its cluster,
        while the remaining ranked candidates (`unopened_ids`) stay available as alternatives for subsequent steps.
        When multiple candidates are opened (`max_open > 1` or `associative_max_open > 1`), they are opened from
        least relevant to most relevant so that the best candidate always remains the final VRAM focus head.
        """

        t_start = time.perf_counter()
        required_anchors = tuple(dict.fromkeys(int(s) for s in seed_ids))
        prior_expanded = [
            node_id
            for node_id in self.vram.node_ids()
            if node_id in self.expanded_in_vram and node_id not in required_anchors
        ]
        prior_family_hubs: list[int] = []
        for node_id in prior_expanded:
            for edge in self.store.incoming(node_id, limit=16):
                if edge.source_id not in required_anchors and self.store.out_degree(edge.source_id) >= 2:
                    prior_family_hubs.append(edge.source_id)
            for edge in self.store.outgoing(node_id, limit=16):
                if edge.target_id not in required_anchors and self.store.in_degree(edge.target_id) >= 2:
                    prior_family_hubs.append(edge.target_id)
        context_anchors = tuple(dict.fromkeys([*prior_expanded, *prior_family_hubs]))

        # 1. Verify family intersections directly on the full SSD graph (independent of VRAM preload limits)
        convergence = self.store.resolve_convergence(
            required_anchors,
            context_anchors=context_anchors,
            excluded_ids=prior_expanded,
            mode=mode,
            min_degree=convergence_threshold,
            hot_k=256 if self.search_policy == "fast" else 0,
        )

        # 2. Preload the 1st-degree clusters of the required question anchors
        events: list[RecallEvent] = []
        for seed_id in reversed(required_anchors):
            events.append(self.recall(seed_id))

        # 3. Determine how many ranked candidates to open automatically (default: 1, the single best candidate)
        if max_open is not None:
            open_limit = max(0, int(max_open))
        elif mode == "associative":
            open_limit = max(0, int(associative_max_open))
        else:
            open_limit = 1

        ids_to_open = convergence.ranked_ids[:open_limit]
        active_anchors = set(required_anchors) | set(context_anchors)

        # 4. Open from least relevant to most relevant so the best candidate (`ids_to_open[0]`) is opened LAST and stays at focus head
        for candidate_id in reversed(ids_to_open):
            # Family anchors that served to disambiguate `candidate_id` on SSD remain in VRAM as [1° grado]
            # so their generic family description does not pollute the specific converged child node.
            for seed_id in required_anchors:
                if (
                    self.store.edge(seed_id, candidate_id) is not None
                    or self.store.edge(candidate_id, seed_id) is not None
                ):
                    self.expanded_in_vram.discard(seed_id)
            # Reinforce converging edges BEFORE `step_to(candidate_id)` so `recall(candidate_id)` ranks active_anchors first
            # even when VRAM capacity is small or the candidate lay beyond `edge_fetch_limit`.
            tick = self._next_tick()
            converging_edges: list[Edge] = []
            with self.store.transaction():
                for anchor_id in active_anchors:
                    fwd = self.store.edge(anchor_id, candidate_id)
                    if fwd is not None:
                        converging_edges.append(fwd)
                        self.store.touch_edge(fwd.source_id, fwd.target_id, tick)
                    rev = self.store.edge(candidate_id, anchor_id)
                    if rev is not None:
                        converging_edges.append(rev)
                        self.store.touch_edge(rev.source_id, rev.target_id, tick)
            events.append(self.step_to(candidate_id, reinforce=False))
            if converging_edges:
                self.vram_graph.add_edges(converging_edges)
                self.vram_graph.prune_to_nodes(set(self.vram.node_ids()))

        recall_ms = (time.perf_counter() - t_start) * 1000.0
        self.last_convergence = convergence.with_recall_outcome(ids_to_open, recall_ms)
        return events

    def boundary_nodes_in_vram(self) -> tuple[KnowledgeNode, ...]:
        return tuple(node for node in self.vram.nodes() if node.id not in self.expanded_in_vram)

    def expanded_nodes_in_vram(self) -> tuple[KnowledgeNode, ...]:
        return tuple(node for node in self.vram.nodes() if node.id in self.expanded_in_vram)

    def _fetch_node(self, node_id: int) -> KnowledgeNode | None:
        node = self.vram.get(node_id)
        if node is not None:
            self.activity.record("read_gpu" if self.memory_backend == "cuda" else "read_host", node_id)
            return node
        node = self.ram.get(node_id)
        if node is not None:
            self.activity.record("read_ram", node_id)
            return node
        node = load_node(self.store, node_id)
        if node is not None:
            self.disk_loads += 1
            self.disk_payload_bytes += len(node.to_cell().content)
            self.activity.record("load_disk", node_id)
        return node

    def physical_state(self) -> dict:
        if self.memory_backend == "cuda":
            return {**self.vram.memory.stats(), "disk_loads": self.disk_loads,
                    "disk_payload_bytes": self.disk_payload_bytes}
        return {"backend": "host", "physical_vram": False, "allocated_bytes": 0,
                "allocations": 0, "upload_bytes": 0, "download_bytes": 0}

    def close(self) -> None:
        self.vram.close()
        self.ram.close()

    def _is_knowledge_cell(self, cell_id: int) -> bool:
        cell = self.store.cell(cell_id)
        if cell is None:
            return False
        try:
            payload = json.loads(cell.content)
        except (UnicodeDecodeError, json.JSONDecodeError, TypeError):
            return False
        return isinstance(payload, dict) and payload.get("kind") == "knowledge"
