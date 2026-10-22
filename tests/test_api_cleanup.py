"""Regression coverage for dashboard serialization and legacy HTTP contracts."""

import json
import unittest
from dataclasses import replace
from io import BytesIO
from pathlib import Path
from unittest.mock import Mock, patch

from luca_memory.api import ApiHandler, LucaRuntime
from luca_memory.node import KnowledgeNode, load_node
from luca_memory.store import Edge


class DashboardSerializationTests(unittest.TestCase):
    def setUp(self):
        self.runtime = LucaRuntime({
            "storage": {"database": ":memory:", "seed": str(
                Path(__file__).parents[1] / "seed" / "knowledge_base_v1.json")},
            "runtime": {"language_adapter": "rules", "vram_capacity": 2},
        })
        self.addCleanup(self.runtime.close)
        self.store = self.runtime.session.store
        self.carousel = self.runtime.session.carousel
        memory = self.carousel.synaptic
        for node_id in range(100, 112):
            memory.update_node(KnowledgeNode(node_id, f"node_{node_id}", f"Title {node_id}", "Body"))
        for target in range(101, 111):
            memory.connect(100, target)
        memory.connect(101, 100)
        memory.connect(111, 100)

    def test_family_payload_order_and_eight_member_limit(self):
        self.carousel.vram.promote(load_node(self.store, 100))
        with self.store.lock:
            families = self.runtime._serialize_vram_families()
        expected = []
        for direction, members, pattern, slug_pattern in (
            ("prefix", list(range(101, 109)), "100:*", "node_100:*"),
            ("suffix", [101, 111], "*:100", "*:node_100"),
        ):
            expected.append({
                "anchor_id": 100, "anchor_slug": "node_100", "anchor_title": "Title 100",
                "direction": direction, "pattern": pattern, "slug_pattern": slug_pattern,
                "member_ids": members, "member_titles": [f"Title {mid}" for mid in members],
            })
        self.assertEqual(families, expected)
        # Stored family members remain visible even when they are outside VRAM.
        self.assertEqual(self.carousel.vram.node_ids(), (100,))

    def test_missing_member_labels_and_singleton_omission(self):
        self.carousel.vram.promote(load_node(self.store, 100))
        with patch.object(self.store, "prefix_family_ids", return_value=(101, 999999)), \
             patch.object(self.store, "suffix_family_ids", return_value=(111,)):
            families = self.runtime._serialize_vram_families()
        self.assertEqual(len(families), 1)
        self.assertEqual(families[0]["member_titles"], ["Title 101", "999999"])

    def test_title_lookup_loads_each_label_once(self):
        with patch("luca_memory.api.load_node", wraps=load_node) as reads:
            self.assertEqual(self.runtime._node_title(100), "Title 100")
            self.assertEqual(self.runtime._node_title(999999), "999999")
        self.assertEqual(reads.call_count, 2)

    def test_tier_links_and_truncation_keep_residency_semantics(self):
        node = replace(load_node(self.store, 100), content="x" * 2001)
        self.carousel.vram_graph.add_edge(Edge(100, 101))
        self.carousel.expanded_in_vram.add(100)
        vram = self.runtime._serialize_tier_node(node, in_vram=True)
        ram = self.runtime._serialize_tier_node(node, in_vram=False)
        self.assertEqual(vram["incoming_ids"], [])
        self.assertEqual(vram["outgoing_ids"], [101])
        self.assertEqual(ram["incoming_ids"], [101, 111])
        self.assertEqual(ram["outgoing_ids"], list(range(101, 111)))
        self.assertTrue(vram["expanded"])
        self.assertFalse(ram["expanded"])
        self.assertEqual(vram["content"], "x" * 2000)
        self.assertTrue(vram["content_truncated"])
        self.assertTrue(self.runtime._serialize_tier_node(
            replace(node, content="Short", content_complete=False), in_vram=True)["content_truncated"])


class HttpBodyContractTests(unittest.TestCase):
    def handler(self, path, body, *, length=None, origin=None):
        # Dispatch against byte streams to test validation without a running app.
        handler = ApiHandler.__new__(ApiHandler)
        handler.path = path
        handler.headers = {"Content-Length": str(len(body) if length is None else length), "Host": "localhost"}
        if origin is not None:
            handler.headers["Origin"] = origin
        handler.rfile = BytesIO(body)
        handler.runtime = Mock()
        handler._json = Mock()
        return handler

    def test_legacy_routes_forward_the_same_values(self):
        cases = (
            ("/api/chat", {"text": "  Ciao  "}, "chat", ("Ciao",), {}),
            ("/api/task", {"goal": "Study"}, "update_task", ({"goal": "Study"},), {}),
            ("/api/recall", {"node_id": "100"}, "recall_node", (100,), {"alternative": False}),
            ("/api/alternative", {"node_id": 100}, "recall_node", (100,), {"alternative": True}),
            ("/api/section", {"node_id": 100, "key": "details"}, "open_section", (100, "details"), {}),
        )
        for path, payload, method, args, kwargs in cases:
            with self.subTest(path=path):
                handler = self.handler(path, json.dumps(payload).encode())
                handler.do_POST()
                getattr(handler.runtime, method).assert_called_once_with(*args, **kwargs)
                handler._json.assert_called_once_with(getattr(handler.runtime, method).return_value)

    def test_mutation_routes_keep_size_and_object_validation(self):
        for path in ("/api/memory/node", "/api/maintenance/preview"):
            for body, length, message in (
                (b"{}", 0, "Invalid request size."),
                (b"{}", 2_000_001, "Invalid request size."),
                (b"[]", 2, "The request must be an object."),
            ):
                with self.subTest(path=path, length=length, body=body):
                    handler = self.handler(path, body, length=length)
                    handler.do_POST()
                    handler._json.assert_called_once_with({"error": message}, status=400)
                    self.assertEqual(handler.runtime.mock_calls, [])

    def test_legacy_body_rules_and_cross_origin_rejection(self):
        for path, message in (
            ("/api/chat", "text must be a non-empty string"),
            ("/api/recall", "The request body must be an object."),
        ):
            handler = self.handler(path, b"[]")
            handler.do_POST()
            handler._json.assert_called_once_with({"error": message}, status=400)
        handler = self.handler("/api/task", b"[]")
        handler.do_POST()
        handler.runtime.update_task.assert_called_once_with([])
        handler = self.handler("/api/chat", b"invalid", origin="https://unrelated.invalid")
        handler.do_POST()
        handler._json.assert_called_once_with({"error": "Cross-origin mutations are not allowed."}, status=403)
        self.assertEqual(handler.rfile.tell(), 0)

    def test_body_reader_preserves_declared_length_uncapped_reads_and_json_errors(self):
        handler = self.handler("/api/chat", b'"value"trailing', length=7)
        self.assertEqual(handler._read_json(), "value")
        self.assertEqual(handler.rfile.read(), b"trailing")
        handler = self.handler("/api/chat", json.dumps("x" * 2_000_001).encode())
        self.assertEqual(len(handler._read_json()), 2_000_001)
        for body in (b"", b"{"):
            handler = self.handler("/api/chat", body)
            handler.do_POST()
            self.assertEqual(handler._json.call_args.kwargs, {"status": 400})


if __name__ == "__main__":
    unittest.main()
