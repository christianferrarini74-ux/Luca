"""Real HTTP integration for the new memory and maintenance boundaries."""

import json
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from luca_memory.api import create_server
from luca_memory.node import KnowledgeNode


class Phase11HTTPTests(unittest.TestCase):
    def setUp(self):
        self.server = create_server({
            "storage": {"database": ":memory:", "seed": str(Path(__file__).parents[1] / "seed/knowledge_base_v1.json")},
            "runtime": {"language_adapter": "rules", "synaptic": {"edge_upper": 6, "edge_target": 4},
                        "api": {"host": "127.0.0.1", "port": 0}}})
        self.worker = threading.Thread(target=self.server.serve_forever)
        self.worker.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"
        self.memory = self.server.runtime.session.carousel.synaptic
        for index in range(100, 109):
            self.memory.update_node(KnowledgeNode(index, f"test_{index}", f"Test {index}", f"Payload {index}"))

    def tearDown(self):
        self.server.shutdown()
        self.worker.join(3)
        self.server.server_close()
        self.server.runtime.close()

    def post(self, route, payload, origin=None):
        headers = {"Content-Type": "application/json"}
        if origin:
            headers["Origin"] = origin
        with urlopen(Request(self.base + route, data=json.dumps(payload).encode(), headers=headers), timeout=5) as response:
            return json.load(response)

    def test_atomic_node_mutation_search_family_navigation_and_stale_revision(self):
        revision = self.memory.store.revision
        state = self.post("/api/memory/node", {"node_id": 100, "title": "Python test", "content": "Updated payload",
                         "expected_revision": revision})["state"]
        self.assertGreater(state["synaptic"]["revision"], revision)
        with self.assertRaises(HTTPError) as error:
            self.post("/api/memory/node", {"node_id": 100, "title": "Stale", "content": "Wrong", "expected_revision": revision})
        self.assertEqual(error.exception.code, 400)
        results = self.post("/api/memory/search", {"query": "Python test"})
        self.assertEqual(results["candidates"][0]["id"], 100)
        self.post("/api/memory/family", {"root": 100, "part": 101, "expected_revision": self.memory.store.revision})
        self.post("/api/memory/edge", {"source": 101, "target": 102, "expected_revision": self.memory.store.revision})
        state = self.post("/api/recall", {"node_id": 101})["state"]
        self.assertEqual(state["synaptic"]["focus_id"], 100)
        self.assertEqual(state["synaptic"]["reading_id"], 101)
        directory = state["synaptic"]["directory"]
        self.assertEqual([entry["id"] for entry in directory["outgoing"]], [102])
        state = self.post("/api/memory/navigate", {"target_id": 102, "directory_revision": directory["revision"]})["state"]
        self.assertEqual(state["synaptic"]["focus_id"], 102)

    def test_manual_preview_confirmation_regroup_and_restore_over_http(self):
        for index in range(101, 108):
            self.memory.connect(100, index)
        preview = self.post("/api/maintenance/preview", {"node_id": 100, "groups": [
            {"title": "Related pages", "direction": "outgoing", "members": [101, 102, 103, 104]}]})
        self.assertEqual(preview["plan"]["degree_after"], 4)
        with self.assertRaises(HTTPError) as error:
            self.post("/api/maintenance/apply", {"plan_id": preview["plan_id"]})
        self.assertEqual(error.exception.code, 400)
        result = self.post("/api/maintenance/apply", {"plan_id": preview["plan_id"], "confirmed": True})
        self.assertEqual(self.memory.directory(100).external_degree, 4)
        self.post("/api/maintenance/restore", {"operation_id": result["operation_id"], "confirmed": True})
        self.assertEqual(self.memory.directory(100).external_degree, 7)
        self.assertIsNotNone(self.memory.store.edge(100, 101))

    def test_cross_origin_mutation_is_rejected(self):
        with self.assertRaises(HTTPError) as error:
            self.post("/api/memory/edge", {"source": 100, "target": 101, "expected_revision": self.memory.store.revision},
                      origin="https://unrelated.invalid")
        self.assertEqual(error.exception.code, 403)
        self.assertIsNone(self.memory.store.edge(100, 101))

    def test_cockpit_contains_complete_directory_and_confirmed_maintenance_controls(self):
        with urlopen(self.base, timeout=5) as response:
            html = response.read().decode("utf-8")
        for element in ("synaptic-directory", "maintenance-preview", "maintenance-apply", "global-search-form"):
            self.assertIn(element, html)
