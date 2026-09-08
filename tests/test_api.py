from pathlib import Path
import threading
import unittest
import json
from urllib.request import Request, urlopen

from luca_memory.api import LucaRuntime, create_server


class LucaRuntimeApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.database = Path(__file__).parent / "api-runtime.sqlite"
        self.database.unlink(missing_ok=True)
        seed = Path(__file__).parent.parent / "seed" / "italian_base_v0.json"
        self.seed = seed
        self.runtime = LucaRuntime(
            {
                "storage": {"database": str(self.database), "seed": str(seed)},
                "runtime": {"language_adapter": "rules", "adapter_role": "orchestrator"},
            }
        )

    def tearDown(self) -> None:
        self.runtime.close()
        self.database.unlink(missing_ok=True)

    def test_chat_returns_backend_reply_trace_and_memory_snapshot(self) -> None:
        result = self.runtime.chat("Luca, ricorda che il sole produce luce.")

        self.assertEqual(result["reply"]["text"], "Ho registrato la conoscenza.")
        self.assertTrue(result["reply"]["trace"])
        sole = next(item for item in result["state"]["memory"] if item["label"] == "sole")
        self.assertIn({"predicate": "produce", "object": "luce"}, sole["facts"])

    def test_state_reads_real_database_size_and_working_set(self) -> None:
        self.runtime.chat("Parlami del sole.")
        state = self.runtime.state()

        self.assertGreater(state["storage"]["ssd_bytes"], 0)
        self.assertGreater(state["working_set"]["ram_cells"], 0)

    def test_state_can_be_served_from_an_http_worker_thread(self) -> None:
        server = create_server(
            {
                "storage": {"database": str(self.database), "seed": str(self.seed)},
                "runtime": {
                    "language_adapter": "rules",
                    "adapter_role": "orchestrator",
                    "api": {"host": "127.0.0.1", "port": 0},
                },
            }
        )
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with urlopen(f"http://127.0.0.1:{server.server_address[1]}/api/state") as response:
                payload = json.loads(response.read())
            self.assertEqual(payload["status"], "ready")
        finally:
            server.shutdown()
            server.server_close()
            server.runtime.close()

    def test_shutdown_endpoint_stops_the_http_server(self) -> None:
        server = create_server(
            {
                "storage": {"database": str(self.database), "seed": str(self.seed)},
                "runtime": {
                    "language_adapter": "rules",
                    "adapter_role": "orchestrator",
                    "api": {"host": "127.0.0.1", "port": 0},
                },
            }
        )
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            request = Request(
                f"http://127.0.0.1:{server.server_address[1]}/api/shutdown",
                method="POST",
            )
            with urlopen(request) as response:
                self.assertEqual(response.status, 202)
            thread.join(timeout=2)
            self.assertFalse(thread.is_alive())
        finally:
            server.server_close()
            server.runtime.close()


if __name__ == "__main__":
    unittest.main()
