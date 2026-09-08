from pathlib import Path
import unittest

from luca_memory.api import LucaRuntime


class LucaRuntimeApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.database = Path(__file__).parent / "api-runtime.sqlite"
        self.database.unlink(missing_ok=True)
        seed = Path(__file__).parent.parent / "seed" / "italian_base_v0.json"
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


if __name__ == "__main__":
    unittest.main()
