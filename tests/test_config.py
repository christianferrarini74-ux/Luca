from pathlib import Path
import tempfile
import unittest

from luca_memory.config import ConfigurationError, load_config


class ConfigurationTests(unittest.TestCase):
    def test_synaptic_settings_are_validated_without_hardcoded_runtime_limits(self):
        from luca_memory.synaptic_settings import SynapticSettings
        settings = SynapticSettings.from_config({"synaptic": {"edge_upper": 12, "edge_target": 9}})
        self.assertEqual((settings.edge_upper, settings.edge_target), (12, 9))
        for options in ({"edge_upper": 45}, {"edge_target": 1}, {"navigation_steps": True},
                        {"automatic_sleep": "true"}, {"idle_seconds": 0}):
            with self.assertRaises(ValueError):
                SynapticSettings.from_config({"synaptic": options})

    def test_invalid_memory_backend_and_device_are_rejected(self) -> None:
        for options in ("memory_backend: automatic", "gpu_device: -1", "gpu_device: true", "gpu_device: abc"):
            with self.subTest(options=options), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "config.yaml"
                path.write_text("runtime:\n  " + options + "\n", encoding="utf-8")
                with self.assertRaises(ConfigurationError):
                    load_config(path)

    def test_load_config_resolves_paths_and_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config_path = root / "config.yaml"
            config_path.write_text(
                "storage:\n  database: data/luca.sqlite\nruntime:\n  language_adapter: rules\n",
                encoding="utf-8",
            )

            config = load_config(config_path)

            self.assertEqual(config["storage"]["database"], str((root / "data" / "luca.sqlite").resolve()))
            self.assertEqual(config["storage"]["seed"], str((root / "seed" / "italian_base_v0.json").resolve()))
            self.assertEqual(config["runtime"]["api"]["port"], 8765)
            self.assertNotIn("directory", config["frontend"])
            self.assertEqual(config["runtime"]["memory_backend"], "host")

    def test_invalid_adapter_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / "config.yaml"
            config_path.write_text("runtime:\n  language_adapter: unknown\n", encoding="utf-8")

            with self.assertRaises(ConfigurationError):
                load_config(config_path)

    def test_database_can_be_resolved_inside_a_separate_storage_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config_path = root / "config.yaml"
            config_path.write_text(
                "storage:\n  directory: memory\n  database: luca.sqlite\n",
                encoding="utf-8",
            )

            config = load_config(config_path)

            self.assertEqual(config["storage"]["directory"], str((root / "memory").resolve()))
            self.assertEqual(config["storage"]["database"], str((root / "memory" / "luca.sqlite").resolve()))


if __name__ == "__main__":
    unittest.main()
