"""Behavioral freedom, explicit protocols and bounded multi-node readings."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from luca_memory.adapters import LMStudioAdapter
from luca_memory.bible import read_bible
from luca_memory.budget import PromptBudget
from luca_memory.llm.models import LLMConfigurationError
from luca_memory.navigation_schema import navigation_schema
from luca_memory.node import KnowledgeNode
from luca_memory.reading_workspace import ReadingWorkspace
from luca_memory.session import LucaSession
from luca_memory.store import MemoryStore
from luca_memory.synaptic import Directory, DirectoryEntry, SynapticMemory
from luca_memory.synaptic_settings import SynapticSettings


class BibleContractTests(unittest.TestCase):
    def setUp(self):
        self.connector = Mock()
        self.model = self.connector.create_chat_model.return_value
        self.adapter = LMStudioAdapter(connector=self.connector)
        self.adapter.prompt_budget = PromptBudget(context_window=30000)

    def assert_bible_only(self, operation):
        messages = self.model.complete.call_args.args[0]
        self.assertEqual(messages[0], {"role": "system", "content": read_bible()})
        self.assertEqual(sum(item["role"] == "system" for item in messages), 1)
        self.assertEqual(json.loads(messages[-1]["content"])["operation"], operation)

    def test_response_has_only_bible_instructions_and_unchanged_output(self):
        text = "Sono Luca. La memoria locale collega questi eventi.\nLegami diretti: A → B."
        self.model.complete.return_value = text
        self.assertEqual(self.adapter.respond("Domanda", "Ricordo", [], task_context="Compito"), text)
        self.assert_bible_only("respond")
        data = json.loads(self.model.complete.call_args.args[0][-1]["content"])
        self.assertEqual((data["task"], data["memory"]), ("Compito", "Ricordo"))

    def test_navigation_has_no_extra_system_instructions(self):
        self.model.complete.return_value = '{"action":"answer","use_memory":false,"response":"Ciao"}'
        result = self.adapter.navigate_memory("Ciao", {}, [])
        self.assertEqual(result["response"], "Ciao")
        self.assert_bible_only("navigate")

    def test_grouping_has_only_bible_and_numeric_constraints(self):
        self.model.complete.return_value = '{"groups":[]}'
        directory = Directory(1, 1, (), (DirectoryEntry(2, "A"), DirectoryEntry(3, "B")), ())
        self.adapter.propose_groups(directory, SynapticSettings())
        self.assert_bible_only("group")
        data = json.loads(self.model.complete.call_args.args[0][-1]["content"])
        self.assertEqual(data["constraints"]["edge_upper"], 50)
        self.assertEqual(data["constraints"]["edge_target"], 45)
        self.assertTrue(data["constraints"]["unique_members_per_direction"])

    def test_recall_no_longer_silently_clips_question(self):
        self.model.complete.return_value = '{"target_id":null}'
        question = "x" * 5000
        self.adapter.propose_recall(question, None, [], "global")
        self.assert_bible_only("recall")
        self.assertEqual(json.loads(self.model.complete.call_args.args[0][-1]["content"])["question"], question)
        self.assertEqual(self.model.complete.call_args.kwargs["max_tokens"], self.adapter.synaptic_settings.recall_output_tokens)

    def test_interpretation_uses_bible_and_configurable_budget(self):
        self.model.complete.return_value = '{"kind":"greet"}'
        self.adapter.interpret("Ciao")
        self.assert_bible_only("interpret")
        self.assertEqual(self.model.complete.call_args.kwargs["max_tokens"], self.adapter.synaptic_settings.interpretation_output_tokens)

    def test_custom_bible_is_used_without_hidden_fallback(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bible.md"
            path.write_text("Custom contract.", encoding="utf-8")
            self.adapter.bible_path = path
            messages, _ = self.adapter._request("respond", "Q", {})
            self.assertEqual(messages[0]["content"], "Custom contract.")
            path.write_text("Updated contract.", encoding="utf-8")
            messages, _ = self.adapter._request("respond", "Q", {})
            self.assertEqual(messages[0]["content"], "Updated contract.")
            path.unlink()
            with self.assertRaises(LLMConfigurationError):
                self.adapter._request("respond", "Q", {})

    def test_empty_bible_is_an_error(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "empty.md"
            path.write_text(" ", encoding="utf-8")
            with self.assertRaises(LLMConfigurationError):
                read_bible(path)


class GenerationContractTests(unittest.TestCase):
    def payload(self, generation):
        adapter = LMStudioAdapter()
        adapter.connector.config["llm"]["runtimes"]["local"]["agents"]["orchestrator"]["generation"] = generation
        response = Mock()
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        response.read.return_value = b'{"choices":[{"message":{"content":"Ciao"}}]}'
        with patch("luca_memory.llm.providers.urlopen", return_value=response) as request:
            adapter.connector.create_chat_model().complete([{"role": "user", "content": "Ciao"}], max_tokens=100)
            return json.loads(request.call_args.args[0].data)

    def test_reasoning_is_not_silently_disabled(self):
        payload = self.payload({})
        self.assertNotIn("reasoning_effort", payload)
        self.assertNotIn("chat_template_kwargs", payload)

    def test_provider_options_are_explicit_and_configurable(self):
        payload = self.payload({"reasoning_effort": "high", "chat_template_kwargs": {"enable_thinking": True}})
        self.assertEqual(payload["reasoning_effort"], "high")
        self.assertEqual(payload["chat_template_kwargs"], {"enable_thinking": True})

    def test_generation_cannot_overwrite_addresses_or_budgets(self):
        for key in ("model", "messages", "max_tokens", "response_format"):
            with self.subTest(key=key), self.assertRaises(LLMConfigurationError):
                self.payload({key: "invalid"})


class NavigationProtocolTests(unittest.TestCase):
    def test_family_index_check_accepts_part_cursor_only_with_actual_root_read(self):
        from luca_memory.live_memory_check import family_index_read
        session = Mock()
        session.carousel.focus_id = 1
        session.carousel.reading_id = 2
        session.carousel.synaptic.root.return_value = 1
        session.navigator.workspace.nodes = {1: {}, 2: {}}
        self.assertTrue(family_index_read(session, 1))
        session.navigator.workspace.nodes = {2: {}}
        self.assertFalse(family_index_read(session, 1))

    def test_family_index_check_rejects_unrelated_cursor_or_missing_focus(self):
        from luca_memory.live_memory_check import family_index_read
        session = Mock()
        session.carousel.focus_id = 1
        session.carousel.reading_id = 3
        session.carousel.synaptic.root.return_value = 3
        session.navigator.workspace.nodes = {1: {}}
        self.assertFalse(family_index_read(session, 1))
        session.carousel.focus_id = None
        self.assertFalse(family_index_read(session, 1))

    def test_open_requires_source_and_valid_ids_per_source(self):
        schema = navigation_schema({"reading_id": 1, "local_target_ids": [2],
                                    "global_candidates": [{"id": 3, "title": "Global"}]})
        opens = [variant for variant in schema["anyOf"] if variant["properties"]["action"]["const"] == "open"]
        self.assertEqual(len(opens), 2)
        for variant in opens:
            self.assertEqual(set(variant["required"]), {"action", "source", "target_id"})
        self.assertEqual(opens[0]["properties"]["target_id"]["enum"], [2])
        self.assertEqual(opens[1]["properties"]["target_id"]["enum"], [3])

    def test_final_action_requires_a_response_and_memory_decision(self):
        answer = navigation_schema({})["anyOf"][-1]
        self.assertEqual(set(answer["required"]), {"action", "use_memory", "response"})

    def test_address_already_in_fast_directory_does_not_need_global_lookup(self):
        schema = navigation_schema({"local_target_ids": [2], "global_candidates": [{"id": 2}]})
        opens = [variant for variant in schema["anyOf"] if variant["properties"]["action"]["const"] == "open"]
        self.assertEqual(len(opens), 1)
        self.assertEqual(opens[0]["properties"]["source"]["const"], "local")


class ReadingWorkspaceTests(unittest.TestCase):
    def payload(self, identity, content):
        return {"reading_id": identity, "focus_id": identity, "title": str(identity),
                "content": content, "directory": {"incoming": [], "outgoing": []}}

    def test_only_actual_reads_are_available_and_bound_is_enforced(self):
        budget = PromptBudget(memory_limit=700)
        workspace = ReadingWorkspace(budget)
        workspace.remember(self.payload(1, "a" * 150))
        workspace.remember(self.payload(2, "b" * 150))
        self.assertEqual(set(workspace.nodes), {1, 2})
        workspace.remember(self.payload(3, "c" * 150))
        self.assertNotIn(1, workspace.nodes)
        self.assertIn(1, workspace.omitted_ids)
        self.assertLessEqual(budget.count(workspace._text("step_limit")), budget.memory_limit)

    def test_session_can_answer_from_multiple_reads_without_another_generation(self):
        with MemoryStore(":memory:") as store:
            memory = SynapticMemory(store)
            memory.update_node(KnowledgeNode(1, "alpha", "Alpha", "Alpha causes beta."))
            memory.update_node(KnowledgeNode(2, "beta", "Beta", "Beta reaches gamma."))
            memory.connect(1, 2)
            adapter = Mock(spec=["navigate_memory", "respond"])
            adapter.navigate_memory.side_effect = [
                {"action": "open", "source": "global", "target_id": 1},
                {"action": "open", "source": "local", "target_id": 2},
                {"action": "answer", "use_memory": True, "response": "Alpha links to gamma through beta."}]
            seed = Path(__file__).parents[1] / "seed/knowledge_base_v1.json"
            session = LucaSession(store, seed, adapter, planner_mode="llm", vram_capacity=1)
            try:
                result = session.handle("Alpha")
                self.assertEqual(result.text, "Alpha links to gamma through beta.")
                adapter.respond.assert_not_called()
                final_state = adapter.navigate_memory.call_args.args[1]
                self.assertEqual([node["reading_id"] for node in final_state["read_nodes"]], [1, 2])
                self.assertEqual(session.carousel.context_report["node_ids"], [1, 2])
                self.assertEqual(session.carousel.vram.node_ids(), (2,))
                self.assertTrue(session.carousel.context_report["directory_in_answer"])
                for identity in (1, 2):
                    exposure = store.connection.execute("SELECT exposure_count FROM node_usage WHERE node_id=?", (identity,)).fetchone()
                    self.assertGreater(exposure[0], 0)
                session.reset()
                self.assertEqual(session.navigator.workspace.nodes, {})
                self.assertIsNone(session.navigator.response)
            finally:
                session.close()

    def test_reopened_node_is_no_longer_listed_as_omitted(self):
        workspace = ReadingWorkspace(PromptBudget(memory_limit=700))
        for identity in (1, 2, 3, 1):
            workspace.remember(self.payload(identity, "a" * 150))
        self.assertIn(1, workspace.nodes)
        self.assertNotIn(1, workspace.omitted_ids)

    def test_missing_directory_content_does_not_produce_an_unbounded_workspace(self):
        workspace = ReadingWorkspace(PromptBudget(memory_limit=200))
        with self.assertRaises(ValueError):
            workspace.remember(self.payload(1, "a" * 1000))

    def test_workspace_span_offsets_are_bytes_and_render_is_bounded(self):
        workspace = ReadingWorkspace(PromptBudget(memory_limit=1000))
        workspace.remember(self.payload(1, "è🙂" * 20))
        carousel = Mock(focus_id=1, reading_id=1)
        text = workspace.render(carousel, "answered")
        report = carousel.context_report
        self.assertLessEqual(report["input_units"], 1000)
        span = report["node_spans"][0]
        item = json.loads(text.encode()[span["start"]:span["end"]])
        self.assertEqual(item["reading_id"], 1)
