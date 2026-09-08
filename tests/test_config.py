from pathlib import Path
import tempfile
import unittest

from luca_memory.config import ConfigurationError, load_config


class ConfigurationTests(unittest.TestCase):
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

    def test_invalid_adapter_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / "config.yaml"
            config_path.write_text("runtime:\n  language_adapter: unknown\n", encoding="utf-8")

            with self.assertRaises(ConfigurationError):
                load_config(config_path)


if __name__ == "__main__":
    unittest.main()
