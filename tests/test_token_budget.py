"""Token-budget behavior without requiring a running inference server."""

import json
import os
import unittest
from pathlib import Path
from unittest.mock import patch

from luca_memory.budget import PromptBudget, units
from luca_memory.config import load_config
from luca_memory.llm.lmstudio import LMStudioModelManager
from luca_memory.llm.models import LLMConfigurationError
from luca_memory.llm.tokenization import LMStudioTokenCounter
from luca_memory.store import MemoryStore
from luca_memory.task_state import TaskMemory


class TestCounter:
    """Deterministic test double, never a production tokenizer fallback."""

    def count(self, text):
        return (len(text) + 3) // 4

    def messages(self, messages):
        return sum(self.count(item["content"]) + 8 for item in messages)


class TokenBudgetTests(unittest.TestCase):
    def budget(self, **options):
        return PromptBudget(unit="tokens", counter=TestCounter(), **options)

    def test_project_config_selects_70000_model_tokens(self):
        settings = load_config(Path(__file__).parents[1] / "config.yaml")["runtime"]
        budget = PromptBudget.from_config(settings)
        self.assertEqual((budget.unit, budget.context_window), ("tokens", 70000))
        self.assertEqual(budget.history_limit, 40000)
        self.assertEqual(budget.output_reserve, 4096)

    def test_no_silent_byte_fallback(self):
        with self.assertRaisesRegex(ValueError, "token counter"):
            PromptBudget(unit="tokens").messages("I", "", [], "Q")

    def test_invalid_unit_fails(self):
        with self.assertRaises(ValueError):
            PromptBudget(unit="words")

    def test_unicode_is_not_counted_as_utf8_bytes(self):
        budget = self.budget()
        text = "è🙂" * 100
        self.assertEqual(budget.count(text), 50)
        self.assertGreater(units(text), budget.count(text))
        prefix = budget.truncate(text, 12)
        self.assertTrue(text.startswith(prefix))
        self.assertLessEqual(budget.count(prefix), 12)

    def test_more_than_eight_turns_survive(self):
        budget = self.budget(context_window=70000, history_limit=40000)
        history = [{"role": role, "content": f"Turn {index} {role}"} for index in range(60) for role in ("user", "assistant")]
        messages, report = budget.messages("I", "M", history, "Q")
        self.assertEqual(report["history_messages"], 120)
        self.assertEqual(messages[1:-1], history)
        self.assertEqual(budget.trim_history(history), history)

    def test_complete_formatted_request_is_counted(self):
        budget = self.budget()
        messages, report = budget.messages("I", "M", [], "Q")
        self.assertEqual(report["input_tokens"], budget.counter.messages(messages))
        self.assertEqual(report["accounting"], "model_tokens")
        self.assertLessEqual(report["input_tokens"] + budget.output_reserve + budget.framing_reserve, budget.context_window)
        self.assertEqual(report["memory_bytes"], 1)

    def test_fixed_instructions_are_never_silently_truncated(self):
        budget = self.budget(context_window=4096)
        with self.assertRaises(ValueError):
            budget.messages("R" * 20000, "", [], "original question")

    def test_overflow_keeps_question_and_bounded_memory(self):
        budget = self.budget(context_window=4096, memory_limit=2500, history_limit=1000)
        history = [{"role": role, "content": "H" * 3000} for role in ("user", "assistant")]
        messages, report = budget.messages("I", "M" * 20000, history, "Original question")
        self.assertEqual(messages[-1]["content"], "Original question")
        self.assertTrue(report["memory_truncated"])
        self.assertLessEqual(report["input_tokens"], report["input_limit"])
        self.assertLessEqual(report["history_tokens"], budget.history_limit)

    def test_latest_oversized_pair_is_excerpted_not_mutated(self):
        budget = self.budget(history_limit=128)
        history = [{"role": role, "content": "H" * 5000} for role in ("user", "assistant")]
        original = json.dumps(history)
        messages, report = budget.messages("I", "", history, "Q")
        self.assertTrue(report["history_excerpted"])
        self.assertEqual([item["role"] for item in messages], ["system", "user", "assistant", "user"])
        self.assertEqual(json.dumps(history), original)

    def test_history_storage_is_bounded_by_tokens(self):
        budget = self.budget(history_limit=128)
        history = [{"role": role, "content": str(i) + "H" * 100} for i in range(50) for role in ("user", "assistant")]
        kept = budget.trim_history(history)
        self.assertLess(len(kept), len(history))
        self.assertEqual(len(kept) % 2, 0)
        self.assertEqual(kept[-2:], history[-2:])
        self.assertLessEqual(budget.history_count(kept), 128)

    def test_task_uses_the_same_counter(self):
        with MemoryStore(":memory:") as store:
            task = TaskMemory(store, 64, counter=TestCounter().count)
            task.update({"goal": "è" * 100})
            self.assertLessEqual(task.snapshot()["input_units"], 64)
            with self.assertRaises(ValueError):
                task.update({"goal": "è" * 1000})

    def test_counter_uses_native_rpc_and_bounded_hash_cache(self):
        counter = LMStudioTokenCounter(LMStudioModelManager("http://localhost:1234"), "model")
        with patch.object(counter, "_rpc", return_value={"tokenCount": 7}) as rpc:
            self.assertEqual(counter.count("text"), 7)
            self.assertEqual(counter.count("text"), 7)
            self.assertEqual(rpc.call_count, 1)
            self.assertEqual(rpc.call_args.args[0], "countTokens")
            for i in range(300):
                counter.count(str(i))
            self.assertEqual(len(counter.cache), 256)

    def test_message_count_applies_the_model_template(self):
        counter = LMStudioTokenCounter(LMStudioModelManager("http://localhost:1234"), "model")
        with patch.object(counter, "_rpc", side_effect=[{"formatted": "formatted"}, {"tokenCount": 23}]) as rpc:
            self.assertEqual(counter.messages([{"role": "user", "content": "Ciao"}]), 23)
            self.assertEqual(rpc.call_args_list[0].args[0], "applyPromptTemplate")
            self.assertEqual(rpc.call_args_list[1].args[1]["inputString"], "formatted")

    def test_loaded_context_must_really_support_requested_window(self):
        manager = LMStudioModelManager("http://localhost:1234")
        model = {"key": "model", "max_context_length": 131072,
                 "loaded_instances": [{"id": "model", "config": {"context_length": 8192}}]}
        with patch.object(manager, "_request", return_value={"models": [model]}) as request:
            with self.assertRaisesRegex(LLMConfigurationError, "70000"):
                manager.ensure_loaded("model", context_length=70000)
            self.assertEqual(request.call_count, 1)
            model["loaded_instances"][0]["config"]["context_length"] = 131072
            manager.ensure_loaded("model", context_length=70000)

    def test_loading_requests_configured_context_and_verifies_it(self):
        manager = LMStudioModelManager("http://localhost:1234")
        unloaded = {"key": "model", "max_context_length": 131072, "loaded_instances": []}
        loaded = {**unloaded, "loaded_instances": [{"id": "model", "config": {"context_length": 70000}}]}
        with patch.object(manager, "_request", side_effect=[{"models": [unloaded]}, {"status": "loaded"}, {"models": [loaded]}]) as request:
            manager.ensure_loaded("model", context_length=70000)
            self.assertEqual(request.call_args_list[1].args[2], {"model": "model", "context_length": 70000})

    def test_failed_load_confirmation_does_not_loop(self):
        manager = LMStudioModelManager("http://localhost:1234")
        unloaded = {"key": "model", "max_context_length": 131072, "loaded_instances": []}
        with patch.object(manager, "_request", side_effect=[{"models": [unloaded]}, {"status": "loaded"}, {"models": [unloaded]}]) as request:
            with self.assertRaises(LLMConfigurationError):
                manager.ensure_loaded("model", context_length=70000)
            self.assertEqual(request.call_count, 3)


@unittest.skipUnless(os.environ.get("LUCA_TEST_LMSTUDIO") == "1", "Opt-in native tokenizer checks require running LM Studio")
class NativeTokenBudgetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from luca_memory.adapters import LMStudioAdapter
        cls.adapter = LMStudioAdapter.from_config(load_config(Path(__file__).parents[1] / "config.yaml"))

    def test_native_counter_and_template_are_used(self):
        budget = self.adapter.prompt_budget
        messages, report = budget.messages("Sei Luca.", "", [], "Ciao Christian")
        self.assertEqual(report["input_tokens"], budget.counter.messages(messages))
        self.assertNotEqual(budget.count("Ciao Christian"), units("Ciao Christian"))

    def test_large_prompt_stays_within_70000_tokens(self):
        budget = self.adapter.prompt_budget
        history = [{"role": role, "content": ("Dettaglio del capitolo e struttura della memoria. " * 80)}
                   for _ in range(60) for role in ("user", "assistant")]
        messages, report = budget.messages("Sei Luca.", "Conoscenza verificata: algoritmi e memoria. " * 3000,
                                           history, "La domanda corrente. " * 1200)
        self.assertGreater(report["history_messages"], 16)
        self.assertGreater(report["input_tokens"], 50000)
        self.assertLessEqual(report["input_tokens"] + budget.output_reserve + budget.framing_reserve, 70000)
        self.assertEqual(messages[-1]["content"], "La domanda corrente. " * 1200)
