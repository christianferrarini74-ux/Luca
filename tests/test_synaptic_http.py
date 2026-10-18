"""Exercise the complete synaptic dashboard contract over local HTTP."""

import json
from pathlib import Path
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from luca_memory.api import create_server


class SynapticHTTPTests(unittest.TestCase):
    def test_alternatives_archived_diagnostics_and_shutdown(self) -> None:
        server = create_server({
            "storage": {"database": ":memory:", "seed": str(Path(__file__).parents[1] / "seed/knowledge_base_v1.json")},
            "runtime": {"language_adapter": "rules", "memory_search_policy": "complete",
                        "api": {"host": "127.0.0.1", "port": 0}},
        })
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        base = f"http://127.0.0.1:{server.server_address[1]}"

        def post(path, payload):
            request = Request(base + path, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
            with urlopen(request, timeout=5) as response:
                return json.load(response)

        try:
            with urlopen(base, timeout=5) as response:
                self.assertIn(b"convergence-alternatives", response.read())
            state = post("/api/chat", {"text": "I sommergibili dei cani e dei pinguini"})["state"]
            self.assertEqual(state["memory_search_policy"], "complete")
            self.assertEqual(state["convergence"]["opened_ids"], [])
            self.assertIn(19, [m["id"] for m in state["convergence"]["alternatives"]])
            state = post("/api/chat", {"text": "Quanto fa due più due?"})["state"]
            self.assertIsNone(state["convergence"])
            self.assertTrue(state["previous_convergence"]["historical"])
            with self.assertRaises(HTTPError) as error:
                post("/api/alternative", {"node_id": 999999})
            self.assertEqual(error.exception.code, 400)
            state = post("/api/alternative", {"node_id": 19})["state"]
            self.assertEqual(state["tiers"]["vram"]["nodes"][0]["id"], 19)
            self.assertEqual(server.runtime.session.current_subject_id, 19)
            self.assertNotIn(19, [m["id"] for m in state["previous_convergence"]["alternatives"]])
            self.assertIsNone(post("/api/reset", {})["state"]["previous_convergence"])
            post("/api/shutdown", {})
            worker.join(timeout=3)
            self.assertFalse(worker.is_alive())
        finally:
            server.shutdown()
            server.server_close()
            server.runtime.close()
