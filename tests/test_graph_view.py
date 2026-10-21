"""Graph inspection must never activate memory or infer links from titles."""

import json
import os
from pathlib import Path
import threading
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import urlopen

from luca_memory.api import LucaRuntime, create_server
from luca_memory.graph_view import graph_settings
from luca_memory.node import KnowledgeNode


class GraphViewTests(unittest.TestCase):
    def setUp(self):
        self.server = create_server({
            "storage": {"database": ":memory:", "seed": str(Path(__file__).parents[1] / "seed/knowledge_base_v1.json")},
            "runtime": {"language_adapter": "rules", "api": {"host": "127.0.0.1", "port": 0}},
            "frontend": {"graph": {"node_limit": 500, "edge_limit": 2000}}})
        self.runtime = self.server.runtime
        self.memory = self.runtime.session.carousel.synaptic
        for node_id in range(100, 106):
            self.memory.update_node(KnowledgeNode(node_id, f"graph_{node_id}", "Duplicate title", "PRIVATE BODY"))
        self.memory.attach_part(100, 101)
        self.memory.connect(100, 102)
        self.memory.connect(103, 100)
        self.worker = threading.Thread(target=self.server.serve_forever)
        self.worker.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.worker.join(3)
        self.server.server_close()
        self.runtime.close()

    def get(self, path):
        with urlopen(self.base + path, timeout=5) as response:
            return json.load(response)

    def test_snapshot_has_real_directed_ids_and_no_document_content(self):
        graph = self.get("/api/graph")
        edges = {(e["source"], e["target"]) for e in graph["edges"]}
        self.assertTrue({(100, 101), (100, 102), (103, 100)} <= edges)
        self.assertNotIn((102, 100), edges)
        self.assertNotIn((104, 105), edges)
        self.assertNotIn("PRIVATE BODY", json.dumps(graph))
        root = next(n for n in graph["nodes"] if n["id"] == 100)
        part = next(n for n in graph["nodes"] if n["id"] == 101)
        self.assertEqual(root["part_count"], 1)
        self.assertEqual(part["root_id"], 100)

    def test_inspection_does_not_change_focus_tiers_revision_or_events(self):
        session = self.runtime.session
        self.runtime.recall_node(102)
        def signature():
            return (session.store.revision, session.carousel.focus_id, session.carousel.reading_id,
                    session.carousel.vram.node_ids(), session.carousel.ram.node_ids(),
                    session.store.connection.execute("SELECT COUNT(*) FROM memory_events").fetchone()[0],
                    session.carousel.physical_state())
        before = signature()
        graph = self.get("/api/graph?mode=focus&node_id=101")
        self.assertEqual(graph["center_id"], 100)
        self.assertEqual({n["id"] for n in graph["nodes"]}, {100, 101, 102, 103})
        self.assertEqual(signature(), before)
        self.assertEqual(next(n for n in graph["nodes"] if n["id"] == 102)["tier"], "vram")

    def test_caps_are_explicit_and_edges_do_not_reference_missing_nodes(self):
        self.runtime.graph_settings = {"node_limit": 2, "edge_limit": 1}
        graph = self.get("/api/graph?mode=focus&node_id=100")
        self.assertTrue(graph["nodes_truncated"])
        self.assertEqual(len(graph["nodes"]), 2)
        ids = {n["id"] for n in graph["nodes"]}
        self.assertTrue(all(e["source"] in ids and e["target"] in ids for e in graph["edges"]))
        self.runtime.graph_settings = {"node_limit": 500, "edge_limit": 1}
        graph = self.get("/api/graph")
        self.assertTrue(graph["edges_truncated"])
        self.assertEqual(len(graph["edges"]), 1)

    def test_invalid_queries_and_unknown_ids_are_rejected(self):
        for path, status in (("?mode=invalid", 400), ("?node_id=-1", 400),
                             ("?node_id=no", 400), ("?node_id=999999", 404),
                             ("?mode=global&mode=focus", 400), ("?unused=1", 400)):
            with self.subTest(path=path), self.assertRaises(HTTPError) as error:
                self.get("/api/graph" + path)
            self.assertEqual(error.exception.code, status)

    def test_focus_without_active_memory_is_empty_not_a_fake_graph(self):
        graph = self.get("/api/graph?mode=focus")
        self.assertIsNone(graph["center_id"])
        self.assertEqual(graph["nodes"], [])

    def test_graph_does_not_read_cell_bodies(self):
        with patch.object(self.runtime.session.store, "cell", side_effect=AssertionError("Body read forbidden")):
            self.assertTrue(self.get("/api/graph")["nodes"])

    def test_static_assets_are_served_locally(self):
        for path, marker in (("/graph.js", "projectGraph"), ("/graph.css", "graph-layout"),
                             ("/", "graph-recall")):
            with urlopen(self.base + path, timeout=5) as response:
                self.assertIn(marker, response.read().decode())


class GraphSettingsTests(unittest.TestCase):
    def test_defaults_and_rejection_of_unbounded_or_invalid_values(self):
        self.assertEqual(graph_settings({}), {"node_limit": 500, "edge_limit": 2000})
        for graph in (None, [], {"node_limit": True}, {"node_limit": 2001},
                      {"edge_limit": 0}, {"edge_limit": "100"}):
            with self.subTest(graph=graph), self.assertRaises(ValueError):
                graph_settings({"graph": graph})

    @unittest.skipUnless(os.getenv("LUCA_TEST_CUDA") == "1", "Set LUCA_TEST_CUDA=1 for real GPU inspection")
    def test_graph_inspects_real_gpu_residency_without_transfers(self):
        runtime = LucaRuntime({
            "storage": {"database": ":memory:", "seed": str(Path(__file__).parents[1] / "seed/knowledge_base_v1.json")},
            "runtime": {"language_adapter": "rules", "memory_backend": "cuda",
                        "gpu_device": int(os.getenv("LUCA_TEST_GPU", "1"))}})
        try:
            runtime.recall_node(3)
            before = runtime.session.carousel.physical_state()
            graph = runtime.graph()
            self.assertEqual(graph["backend"], "cuda")
            self.assertEqual(next(n for n in graph["nodes"] if n["id"] == 3)["tier"], "vram")
            self.assertEqual(runtime.session.carousel.physical_state(), before)
        finally:
            runtime.close()
