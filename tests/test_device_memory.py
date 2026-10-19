"""Deterministic failure tests and explicitly enabled hardware integration tests."""

from dataclasses import replace
from pathlib import Path
import os
import tempfile
import threading
import unittest
from unittest.mock import patch

from luca_memory.node import KnowledgeNode, KnowledgeSection, load_node, save_node
from luca_memory.store import Edge, MemoryStore
from luca_memory.tiers import SynapticCarousel
from luca_memory.tiers.cuda import CudaMemory, DeviceMemoryError
from luca_memory.tiers.device_slot import DeviceSlot, encode_node, decode_node


class FakeDevice:
    """Fault injection only; never selected by the application."""

    def __init__(self):
        self.buffers = {}
        self.next_id = 0
        self.fail_after = None
        self.corrupt = False

    def upload(self, payload):
        if self.fail_after is not None and self.next_id >= self.fail_after:
            raise DeviceMemoryError("Injected allocation failure")
        self.next_id += 1
        self.buffers[self.next_id] = payload
        return self.next_id

    def download(self, pointer):
        return b"corrupt" if self.corrupt else self.buffers[pointer]

    def free(self, pointer):
        del self.buffers[pointer]

    def close(self):
        self.buffers.clear()


class DeviceSlotTests(unittest.TestCase):
    def setUp(self):
        self.memory = FakeDevice()
        self.slot = DeviceSlot(2, 10000, memory=self.memory)
        self.nodes = [KnowledgeNode(i, f"n{i}", f"Node {i}", f"Nero → carbone {i} 🧠", created_at=1) for i in range(1, 5)]

    def tearDown(self):
        self.slot.close()

    def test_complete_node_round_trip_including_sections_and_cache_flags(self):
        node = replace(self.nodes[0], sections=(KnowledgeSection("a", "Capitolo", "Testo è"),),
                       keywords=("nero",), summary="Sintesi", content_complete=False, full_content_bytes=999)
        self.assertEqual(decode_node(encode_node(node)), node)
        self.slot.promote(node)
        self.assertEqual(self.slot.get(node.id), node)
        self.assertTrue(all(isinstance(entry[0], int) for entry in self.slot._entries.values()))

    def test_eviction_recall_update_and_no_shadow_payload(self):
        self.slot.promote_many(self.nodes[:2])
        self.assertEqual(self.slot.node_ids(), (1, 2))
        self.assertEqual(self.slot.promote(self.nodes[2]), [self.nodes[1]])
        self.assertEqual(self.slot.node_ids(), (3, 1))
        changed = replace(self.nodes[0], content="Updated")
        self.slot.promote(changed)
        self.assertEqual(self.slot.get(1), changed)
        self.assertEqual(len(self.memory.buffers), 2)
        self.assertEqual(self.slot.remove(1), changed)
        self.assertIsNone(self.slot.get(1))

    def test_failed_batch_preserves_previous_contents_and_frees_staged_allocations(self):
        self.slot.promote(self.nodes[0])
        self.memory.fail_after = 2
        with self.assertRaises(DeviceMemoryError):
            self.slot.promote_many(self.nodes[1:3])
        self.assertEqual(self.slot.node_ids(), (1,))
        self.assertEqual(self.slot.get(1), self.nodes[0])
        self.assertEqual(len(self.memory.buffers), 1)

    def test_identical_payload_reuses_allocation_and_preserves_pointer(self):
        self.slot.promote_many(self.nodes[:2])
        old = self.slot._entries[1][0]
        uploads = self.memory.next_id
        self.slot.promote(self.nodes[0])
        self.assertEqual(self.slot._entries[1][0], old)
        self.assertEqual(self.memory.next_id, uploads)
        self.assertEqual(self.slot.get(1), self.nodes[0])
        self.assertIn(old, self.memory.buffers)
        self.slot.promote(replace(self.nodes[0], recall_count=1))
        self.assertNotEqual(self.slot._entries[1][0], old)
        self.assertNotIn(old, self.memory.buffers)

    def test_reused_entry_survives_failure_of_another_batch_upload(self):
        self.slot.promote_many(self.nodes[:2])
        pointers = dict(self.slot._entries)
        self.memory.fail_after = self.memory.next_id
        with self.assertRaises(DeviceMemoryError):
            self.slot.promote_many([self.nodes[0], self.nodes[2]])
        self.assertEqual(self.slot._entries, pointers)
        self.assertEqual(self.slot.get(1), self.nodes[0])
        self.assertEqual(len(self.memory.buffers), 2)

    def test_component_traversal_never_reads_payload_and_prompt_reads_open_nodes_only(self):
        from luca_memory.context_builder import active_vram_component_ids, build_vram_context
        with MemoryStore(":memory:") as store:
            carousel = SynapticCarousel(store)
            carousel.vram.close()
            carousel.vram = self.slot
            self.slot.promote_many(self.nodes[:2])
            carousel.vram_graph.add_edges([Edge(1, 2)])
            carousel.expanded_in_vram.add(1)
            with patch.object(self.memory, "download", wraps=self.memory.download) as reads:
                self.assertEqual(active_vram_component_ids(carousel), {1, 2})
                self.assertEqual(reads.call_count, 0)
                context = build_vram_context(carousel)
                self.assertIn(self.nodes[0].content, context)
                self.assertEqual(reads.call_count, 1)

    def test_corrupt_upload_is_rejected_and_released(self):
        self.memory.corrupt = True
        with self.assertRaises(DeviceMemoryError):
            self.slot.promote(self.nodes[0])
        self.assertEqual(len(self.memory.buffers), 0)
        self.assertEqual(len(self.slot), 0)

    def test_oversized_complete_node_is_rejected_not_truncated(self):
        self.slot.promote(self.nodes[0])
        with self.assertRaises(DeviceMemoryError):
            self.slot.promote(replace(self.nodes[1], content="x" * 20000))
        self.assertEqual(self.slot.node_ids(), (1,))

    def test_byte_limit_and_batch_overflow_return_complete_nodes(self):
        self.slot.max_bytes = 2048
        nodes = [replace(n, content="x" * 1000) for n in self.nodes]
        evicted = self.slot.promote_many(nodes)
        self.assertEqual(self.slot.node_ids(), (1,))
        self.assertEqual({n.id for n in evicted}, {2, 3, 4})
        self.assertTrue(all(len(n.content) == 1000 for n in evicted))
        self.assertLessEqual(self.slot.used_bytes, 2048)

    def test_explicit_host_mode_is_not_reported_as_physical_vram(self):
        with MemoryStore(":memory:") as store:
            carousel = SynapticCarousel(store)
            self.assertFalse(carousel.physical_state()["physical_vram"])
            carousel.close()

    def test_missing_driver_does_not_construct_a_host_slot(self):
        with MemoryStore(":memory:") as store:
            with patch("luca_memory.tiers.device_slot.CudaMemory", side_effect=DeviceMemoryError("No driver")):
                with self.assertRaises(DeviceMemoryError):
                    SynapticCarousel(store, memory_backend="cuda")

    def test_ram_copy_survives_failed_device_promotion(self):
        with MemoryStore(":memory:") as store:
            with store.transaction():
                for node in self.nodes:
                    save_node(store, node)
            carousel = SynapticCarousel(store, vram_capacity=1, ram_capacity=1)
            carousel.vram.close()
            carousel.vram = DeviceSlot(1, 10000, memory=self.memory)
            carousel.memory_backend = "cuda"
            try:
                carousel.recall(1)
                carousel.recall(2)
                self.memory.fail_after = self.memory.next_id
                with self.assertRaises(DeviceMemoryError):
                    carousel.recall(1)
                self.assertEqual(carousel.ram.node_ids(), (1,))
                self.assertEqual(carousel.vram.node_ids(), (2,))
            finally:
                carousel.close()


@unittest.skipUnless(os.getenv("LUCA_TEST_CUDA") == "1", "Set LUCA_TEST_CUDA=1 for real NVIDIA hardware tests")
class PhysicalCudaTests(unittest.TestCase):
    def test_http_worker_reset_and_shutdown_release_context_and_buffers(self):
        from urllib.request import Request, urlopen
        import json
        from luca_memory.api import create_server
        root = Path(os.getenv("LUCA_TEST_DIRECTORY", "D:/Test/Luca"))
        root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="hardware-http-", dir=root) as directory:
            config = {"storage": {"database": str(Path(directory) / "synthetic.sqlite"),
                                   "seed": str(Path(__file__).parents[1] / "seed/knowledge_base_v1.json")},
                      "runtime": {"language_adapter": "rules", "memory_backend": "cuda",
                                  "gpu_device": int(os.getenv("LUCA_TEST_GPU", "1")),
                                  "api": {"host": "127.0.0.1", "port": 0}}}
            server = create_server(config)
            thread = threading.Thread(target=server.serve_forever)
            thread.start()
            old = server.runtime.session.carousel.vram.memory
            base = f"http://127.0.0.1:{server.server_port}"
            def post(route, payload):
                with urlopen(Request(base + route, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"}), timeout=15) as response:
                    return json.load(response)
            try:
                state = post("/api/recall", {"node_id": 3})["state"]
                self.assertTrue(state["physical_memory"]["physical_vram"])
                self.assertGreater(state["physical_memory"]["allocated_bytes"], 0)
                self.assertGreater(state["physical_memory"]["disk_loads"], 0)
                post("/api/reset", {})
                self.assertTrue(old.closed)
                self.assertEqual(old._buffers, {})
                current = server.runtime.session.carousel.vram.memory
                self.assertIsNot(current, old)
                post("/api/recall", {"node_id": 7})
                post("/api/shutdown", {})
                thread.join(10)
                self.assertFalse(thread.is_alive())
            finally:
                server.shutdown()
                server.server_close()
                server.runtime.close()
            self.assertTrue(current.closed)
            self.assertEqual(current._buffers, {})

    def test_ssd_ram_gpu_eviction_restart_integrity_and_cleanup(self):
        root = Path(os.getenv("LUCA_TEST_DIRECTORY", "D:/Test/Luca"))
        root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="hardware-test-", dir=root) as directory:
            database = Path(directory) / "synthetic.sqlite"
            with MemoryStore(database) as store:
                nodes = [KnowledgeNode(i, f"synthetic{i}", f"Synthetic {i}", ("Capitolo è 🧠\n" * 40000) if i == 2 else f"Nodo {i}", created_at=1) for i in range(1, 5)]
                with store.transaction():
                    for node in nodes:
                        save_node(store, node)
                carousel = SynapticCarousel(store, vram_capacity=1, ram_capacity=1, memory_backend="cuda",
                                             gpu_device=int(os.getenv("LUCA_TEST_GPU", "1")), vram_bytes=2_000_000, ram_bytes=2_000_000)
                memory = carousel.vram.memory
                try:
                    carousel.recall(1)
                    self.assertEqual(carousel.vram.get(1).content, nodes[0].content)
                    carousel.recall(2)
                    self.assertEqual(carousel.ram.get(1).content, nodes[0].content)
                    self.assertEqual(carousel.vram.get(2).content, nodes[1].content)
                    carousel.recall(3)
                    self.assertEqual(carousel.ram.get(2).content, nodes[1].content)
                    carousel.recall(4)
                    self.assertNotIn(2, carousel.ram)
                    self.assertNotIn(2, carousel.vram)
                    self.assertEqual(load_node(store, 2).content, nodes[1].content)
                    carousel.recall(2)
                    self.assertEqual(carousel.vram.get(2).content, nodes[1].content)
                    stats = carousel.physical_state()
                    self.assertGreater(stats["upload_bytes"], 1_000_000)
                    self.assertGreater(stats["download_bytes"], 1_000_000)
                    self.assertEqual(stats["allocations"], 1)
                    errors = []
                    def worker():
                        try:
                            self.assertEqual(carousel.vram.get(2).content, nodes[1].content)
                        except BaseException as error:
                            errors.append(error)
                    thread = threading.Thread(target=worker)
                    thread.start()
                    thread.join(10)
                    self.assertFalse(thread.is_alive())
                    self.assertEqual(errors, [])
                    with self.assertRaises(DeviceMemoryError):
                        carousel.vram.promote(replace(nodes[0], content="x" * 2_100_000))
                    self.assertEqual(carousel.vram.node_ids(), (2,))
                finally:
                    carousel.close()
                    carousel.close()
                self.assertTrue(memory.closed)
                self.assertEqual(memory._buffers, {})
            with MemoryStore(database) as reopened:
                self.assertEqual(load_node(reopened, 2).content, nodes[1].content)

    def test_unavailable_gpu_fails_without_host_fallback(self):
        with self.assertRaises(DeviceMemoryError):
            CudaMemory(999999)
