import unittest
from unittest.mock import patch

from luca_memory import LLMConfigurationError, LLMConnector


class LLMConnectorTests(unittest.TestCase):
    def test_resolves_a_role_and_calls_an_openai_compatible_provider(self) -> None:
        config = {
            "llm": {
                "active_runtime": "local",
                "runtimes": {
                    "local": {
                        "providers": {
                            "studio": {"kind": "openai_compatible", "base_url": "http://127.0.0.1:1234/v1"}
                        },
                        "agents": {
                            "orchestrator": {
                                "provider": "studio",
                                "model": "gemma",
                                "timeout_seconds": 12,
                            }
                        },
                    }
                },
            }
        }
        connector = LLMConnector(config)

        with patch("luca_memory.llm.providers.urlopen") as urlopen:
            response = urlopen.return_value
            response.__enter__.return_value.read.return_value = (
                b'{"choices":[{"message":{"content":"risposta"}}]}'
            )
            self.assertEqual(connector.create_chat_model().complete([{"role": "user", "content": "ciao"}]), "risposta")

        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "http://127.0.0.1:1234/v1/chat/completions")

    def test_missing_active_runtime_is_rejected(self) -> None:
        with self.assertRaises(LLMConfigurationError):
            LLMConnector({}).profile_for()

    def test_remote_provider_requires_https_and_an_api_key(self) -> None:
        config = {
            "llm": {
                "active_runtime": "remote",
                "runtimes": {
                    "remote": {
                        "providers": {"remote": {"kind": "deepseek", "base_url": "http://example.test/v1"}},
                        "agents": {"orchestrator": {"provider": "remote", "model": "model"}},
                    }
                },
            }
        }
        with self.assertRaises(LLMConfigurationError):
            LLMConnector(config).create_chat_model()


if __name__ == "__main__":
    unittest.main()
