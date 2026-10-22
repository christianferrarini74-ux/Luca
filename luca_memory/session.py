"""Persistent conversational shell over Luca's native synaptic memory."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from .adapters import LanguageAdapter, LanguageAdapterUnavailable, RuleAdapter
from .budget import PromptBudget
from .context_builder import active_vram_component_ids, build_vram_context
from .curriculum import Curriculum, cell_payload, curriculum_from_file, load_curriculum
from .language import ItalianSeedInterface
from .memory import MemoryEditor
from .navigation import MemoryNavigator, answer_context
from .node import load_node
from .planning import RecallPlan, RecallPlanner
from .protocol import EvidenceBundle, LanguageIntent
from .search import MemorySearch
from .seed_v1 import ensure_knowledge_seed, is_v1_seed, knowledge_seed_from_file
from .store import MemoryStore
from .synaptic import serialized
from .synaptic_settings import SynapticSettings
from .task_state import TaskMemory
from .tiers import SynapticCarousel

_STOPWORDS = {
    "a", "ad", "al", "alla", "alle", "altri", "altro", "anche", "argomento", "avere",
    "cambiamo", "che", "chi", "ci", "come", "con", "cosa", "cui", "da", "dal", "dalla",
    "dei", "del", "della", "delle", "dello", "dentro", "di", "dire", "e", "ed", "era",
    "ero", "essere", "fa", "fanno", "fare", "generale", "gli", "ha", "hai", "ho", "i",
    "il", "in", "insomma", "io", "la", "le", "li", "lo", "ma", "me", "mi", "mia", "mio",
    "molto", "ne", "nei", "nel", "nella", "nelle", "non", "o", "parlami", "parliamo",
    "penso", "per", "perche", "piu", "poi", "possono", "portare", "prima", "produce",
    "proprio", "puo", "qual", "quale", "quali", "quando", "quel", "quello", "questa",
    "questo", "qui", "secondo", "sei", "sembra", "se", "si", "sia", "sono", "su", "sua",
    "sui", "sul", "sulla", "te", "ti", "tipi", "tipo", "tra", "tu", "tua", "tuo", "un",
    "una", "uno", "vero",
}


@dataclass(frozen=True, slots=True)
class SessionReply:
    text: str
    trace: tuple[int, ...] = ()


class LucaSession:
    """Coordinate dialogue, the VRAM<->RAM<->SSD synaptic carousel, and durable memory."""

    def __init__(
        self,
        store: MemoryStore,
        seed_path: str | Path,
        adapter: LanguageAdapter | None = None,
        *,
        vram_capacity: int = 8,
        ram_capacity: int = 32,
        search_policy: str = "fast",
        planner_mode: str = "hybrid",
        memory_settings: dict | None = None,
    ) -> None:
        self.store = store
        self.seed_path = Path(seed_path)
        self.is_v1 = is_v1_seed(self.seed_path) if self.seed_path.exists() else False
        if self.is_v1:
            v1_seed = knowledge_seed_from_file(self.seed_path)
            self.curriculum = Curriculum(v1_seed.version, v1_seed.language, v1_seed.ids)
        else:
            self.curriculum = curriculum_from_file(self.seed_path)
        self.language = ItalianSeedInterface(store, self.curriculum)
        self.editor = MemoryEditor(store)
        self.search = MemorySearch(store)
        settings = memory_settings or {}
        # When bound, reuse the adapter's native counter throughout the session.
        self.carousel = SynapticCarousel(
            store, vram_capacity=vram_capacity, ram_capacity=ram_capacity, search_policy=search_policy,
            recent_window=int(settings.get("recent_window", 8)),
            vram_bytes=int(settings.get("vram_bytes", 8_000_000)), ram_bytes=int(settings.get("ram_bytes", 32_000_000)),
            prompt_budget=(adapter.prompt_budget if getattr(getattr(adapter, "prompt_budget", None), "counter", None) is not None
                           else PromptBudget.from_config(settings)),
            memory_backend=str(settings.get("memory_backend", "host")),
            gpu_device=int(settings.get("gpu_device", 0)),
        )
        try:
            self.adapter = adapter or RuleAdapter()
            self.current_subject_id: int | None = None
            self.history: list[dict[str, str]] = []
            self.planner_mode = planner_mode
            self.synaptic_settings = SynapticSettings.from_config(settings)
            if planner_mode == "llm" and not hasattr(self.adapter, "navigate_memory"):
                raise ValueError("The llm planner requires an adapter with navigate_memory.")
            self.planner = RecallPlanner(store, mode="rules" if planner_mode == "llm" else planner_mode)
            self.navigator = MemoryNavigator(self.carousel,
                max_steps=self.synaptic_settings.navigation_steps,
                search_limit=self.synaptic_settings.global_candidates,
                directory_bytes=self.synaptic_settings.fast_index_bytes,
                search_query_characters=self.synaptic_settings.search_query_characters)
            self.last_plan: RecallPlan | None = None
            self.task = TaskMemory(store, self.carousel.prompt_budget.task_limit, counter=self.carousel.prompt_budget.count)
        except BaseException:
            self.carousel.close()
            raise

    @classmethod
    def open(
        cls,
        database: str | Path,
        seed_path: str | Path,
        adapter: LanguageAdapter | None = None,
        *,
        vram_capacity: int = 8,
        ram_capacity: int = 32,
        search_policy: str = "fast",
        planner_mode: str = "hybrid",
        memory_settings: dict | None = None,
    ) -> LucaSession:
        # Seed migration and session construction share ownership of this one connection.
        store = MemoryStore(database)
        seed_file = Path(seed_path)
        try:
            if seed_file.exists():
                if is_v1_seed(seed_file):
                    ensure_knowledge_seed(store, seed_file)
                elif not store.has_cells():
                    load_curriculum(store, seed_file)
            return cls(store, seed_file, adapter, vram_capacity=vram_capacity, ram_capacity=ram_capacity, search_policy=search_policy, planner_mode=planner_mode, memory_settings=memory_settings)
        except BaseException:
            store.close()
            raise

    @serialized
    def close(self) -> None:
        try:
            self.carousel.close()
        finally:
            self.store.close()

    @serialized
    def open_section(self, node_id: int, key: str) -> None:
        """Open a validated document section while retaining its node identity."""
        node = load_node(self.store, node_id)
        if node is None or key not in {section.key for section in node.sections}:
            raise ValueError("Unknown document section.")
        self.recall_manual(node_id)
        self.carousel.section_focus = (node_id, key)
        self.task.observe(node_id, node_id, True, key)

    @serialized
    def recall_manual(self, node_id: int, *, alternative: bool = False) -> None:
        """Apply manual focus changes through the same task-continuity boundary."""
        previous = self.current_subject_id
        before = active_vram_component_ids(self.carousel)
        if alternative:
            self.carousel.open_alternative(node_id)
        else:
            self.carousel.begin_turn()
            self.carousel.step_to(node_id)
        self.current_subject_id = self.carousel.focus_id if self.is_v1 else node_id
        self.last_plan = None
        after = active_vram_component_ids(self.carousel)
        self.task.observe(previous, node_id, not before or not before.isdisjoint(after))

    @serialized
    def reset(self) -> None:
        """Reset conversational history and empty VRAM/RAM slots while keeping SSD up to date."""

        self.history.clear()
        self.current_subject_id = None
        self.last_plan = None
        self.task.update({"clear": True})
        previous = self.carousel
        # Construct first: failed GPU allocation must not destroy the existing carousel.
        replacement = SynapticCarousel(
            self.store,
            vram_capacity=self.carousel.vram.capacity,
            ram_capacity=self.carousel.ram.capacity,
            search_policy=self.carousel.search_policy,
            recent_window=self.carousel.activity.window,
            vram_bytes=self.carousel.vram.max_bytes,
            ram_bytes=self.carousel.ram.max_bytes,
            prompt_budget=self.carousel.prompt_budget,
            memory_backend=self.carousel.memory_backend,
            gpu_device=self.carousel.gpu_device,
        )
        try:
            previous.close()
        except BaseException:
            replacement.close()
            raise
        self.carousel = replacement
        self.navigator.carousel = replacement
        self.navigator.memory = replacement.synaptic
        self.navigator.begin_turn()

    @serialized
    def handle(self, text: str) -> SessionReply:
        """Serialize a turn: validate, navigate, preserve task continuity, then answer."""
        # Refresh revisions before accepting input; a new turn does not erase durable memory.
        self.carousel.synchronize()
        self.navigator.begin_turn()
        budget = self.carousel.prompt_budget
        if budget.count(text) > budget.context_window - budget.output_reserve - budget.framing_reserve:
            raise ValueError("Il messaggio supera il budget configurato.")
        self.carousel.begin_turn()
        previous_focus = self.current_subject_id
        prev_component = active_vram_component_ids(self.carousel) if self.is_v1 else set()
        # Explicit task edits/resume take precedence over ordinary recall planning.
        task_changed = self.task.apply_text(text, self.current_subject_id)
        if task_changed:
            self.last_plan = RecallPlan("task_update", expose_memory=False)
            recalled_ids = []
        elif self.task.requests_resume(text) and self.task.state.focus_id is not None:
            target = self.task.state.focus_id
            if self.store.cell(target) is not None:
                self.carousel.step_to(target)
                self.current_subject_id = target
                if self.task.state.section_key:
                    self.carousel.section_focus = (target, self.task.state.section_key)
                self.task.resumed()
                self.last_plan = RecallPlan("resume", target, reason="Resume the saved task focus.")
                recalled_ids = [target]
            else:
                self.last_plan = RecallPlan("unresolved", expose_memory=False)
                recalled_ids = []
        else:
            recalled_ids = self._activate_carousel_from_text(text) if self.is_v1 else []
        # A local traversal stays in the task even if a small VRAM slot evicts its origin.
        new_component = active_vram_component_ids(self.carousel) if self.is_v1 else set()
        local_steps = [step for step in self.navigator.trace if "target_id" in step] if self.planner_mode == "llm" else []
        connected = (previous_focus == self.carousel.focus_id or not prev_component
                     or not prev_component.isdisjoint(new_component)
                     or bool(local_steps) and all(step.get("source") == "local" for step in local_steps))
        if self.last_plan is None or self.last_plan.operation != "resume":
            self.task.observe(previous_focus, self.current_subject_id, connected,
                              self.carousel.section_focus[1] if self.carousel.section_focus else None)
        if self.is_v1 and self.planner_mode != "llm" and recalled_ids and prev_component and previous_focus != self.current_subject_id:
            new_component = active_vram_component_ids(self.carousel)
            if prev_component.isdisjoint(new_component):
                self.history.clear()
        current_subject = self._current_subject_label()
        if hasattr(self.adapter, "respond"):
            return self._respond_with_model(text, current_subject)
        return self._respond_with_rules(text, current_subject, task_changed, recalled_ids)

    def _respond_with_model(self, text: str, current_subject: str | None) -> SessionReply:
        """Generate one answer and record only the knowledge actually exposed."""
        budget = self.carousel.prompt_budget
        context = self._memory_context(text)
        # Navigation may already have produced the final answer; never generate it twice.
        if self.planner_mode == "llm" and self.navigator.response is not None:
            response = self.navigator.response
            report = getattr(self.adapter, "last_prompt_report", None)
            if isinstance(report, dict):
                report["memory_units"] = budget.count(context)
                report["memory_bytes"] = len(context.encode("utf-8"))
        elif self.planner_mode == "llm" and hasattr(self.adapter, "respond_with_navigation"):
            response = self.adapter.respond_with_navigation(text, context, self.history, self.task.state.render())
        elif hasattr(self.adapter, "respond_with_task"):
            response = self.adapter.respond_with_task(text, context, self.history, self.task.state.render())
        else:
            response = self.adapter.respond(text, self.task.state.render() + "\n" + context, self.history)
        # Byte spans describe serialized excerpts; model token counts are not byte offsets.
        exposed = self.carousel.context_report.get("node_ids", ())
        report = getattr(self.adapter, "last_prompt_report", {})
        if self.planner_mode != "llm" and ("memory_bytes" in report or "memory_units" in report):
            exposed = [span["node_id"] for span in self.carousel.context_report.get("node_spans", ())
                        if span["start"] < report.get("memory_bytes", report.get("memory_units", 0))]
        self.carousel.mark_exposed(exposed, read_ids=self.navigator.workspace.nodes if self.planner_mode == "llm" else ())
        trace: tuple[int, ...] = tuple(self.carousel.vram.node_ids())
        # Only the legacy assertion path interprets lessons after answering.
        if not self.is_v1:
            try:
                intent = self.adapter.interpret(text, current_subject)
            except LanguageAdapterUnavailable:
                intent = None
            if intent is not None:
                consolidated = self._consolidate_intent(intent)
                if consolidated:
                    trace = consolidated
        self.history.extend(({"role": "user", "content": text}, {"role": "assistant", "content": response}))
        self.history = budget.trim_history(self.history)
        return SessionReply(response, trace)

    def _respond_with_rules(self, text: str, current_subject: str | None,
                            task_changed: bool, recalled_ids: list[int]) -> SessionReply:
        """Keep the deterministic seed/test path separate from model generation."""
        budget = self.carousel.prompt_budget
        if task_changed:
            return SessionReply("Ho aggiornato il compito.", tuple(self.carousel.vram.node_ids()))

        intent = self.adapter.interpret(text, current_subject)
        if intent.kind == "greet":
            if self.is_v1 and 1 in self.curriculum.ids.values():
                self.carousel.recall(1)
            return SessionReply("Ciao Christian. Sono Luca.", tuple(self.carousel.vram.node_ids()))
        if intent.kind == "remember":
            remembered = self.editor.consolidate(intent.proposal())
            first = remembered[0]
            self.current_subject_id = first.subject_id
            detail = "Ho già questa conoscenza." if all(not item.created for item in remembered) else "Ho registrato la conoscenza."
            trace = tuple(value for item in remembered for value in (item.subject_id, item.assertion_id, item.predicate_id, item.object_id))
            return SessionReply(detail, trace)

        if self.is_v1 and recalled_ids:
            conv = self.carousel.last_convergence
            if conv is not None and conv.mode == "strict" and conv.has_only_partial_matches:
                partials: list[str] = []
                for match in conv.partial_matches[:3]:
                    p_node = load_node(self.store, match.node_id)
                    if p_node is not None:
                        partials.append(f"{p_node.title}: {p_node.content}")
                text_reply = (
                    "Non conosco nulla che riguardi insieme tutto quello che mi chiedi. "
                    + ("So soltanto qualcosa su una parte: " + " | ".join(partials) if partials else "")
                ).strip()
                return SessionReply(budget.truncate(text_reply, budget.memory_limit), tuple(self.carousel.vram.node_ids()))
            top_node = self.carousel.vram.get(self.carousel.vram.node_ids()[0])
            body = top_node.content
            if self.carousel.section_focus and self.carousel.section_focus[0] == top_node.id:
                source = load_node(self.store, top_node.id)
                section = next((s for s in source.sections if s.key == self.carousel.section_focus[1]), None) if source else None
                if section:
                    body = section.content
            return SessionReply(budget.truncate(f"{top_node.title}: {body}", budget.per_node_limit), tuple(self.carousel.vram.node_ids()))

        if intent.kind == "describe" and intent.subject:
            subject = self.store.cell_by_alias(intent.subject)
            if subject is None:
                return SessionReply("Non possiedo ancora conoscenze su questo argomento.")
            self.current_subject_id = subject.id
            facts = self.editor.facts_about(subject.id)
            if not facts:
                return SessionReply("Non possiedo ancora una risposta verificata.", (subject.id,))
            phrases = []
            trace_list = [subject.id]
            for fact in facts:
                predicate = str(cell_payload(self.store, fact.predicate_id)["label"])
                object_label = str(cell_payload(self.store, fact.object_id)["label"])
                phrases.append(f"{predicate} {object_label}")
                trace_list.extend((fact.assertion_id, fact.predicate_id, fact.object_id))
            label = str(cell_payload(self.store, subject.id)["label"])
            return SessionReply(f"So che {label} " + " e ".join(phrases) + ".", tuple(trace_list))

        return self._answer(intent.question or text)

    def _activate_carousel_from_text(self, text: str) -> list[int]:
        """Execute a Core-validated plan rather than guessing from edge order."""
        if self.planner_mode == "llm":
            self.navigator.run(text, self.adapter, self.history, self.task.state.render())
            self.current_subject_id = self.carousel.focus_id
            self.last_plan = RecallPlan("llm_navigation", self.current_subject_id,
                                        expose_memory=self.navigator.expose_memory, source="llm")
            return [step["target_id"] for step in self.navigator.trace if "target_id" in step]
        plan = self.planner.plan(text, self.current_subject_id, self.adapter)
        self.last_plan = plan
        if plan.section_key is not None and plan.target_id is not None:
            self.open_section(plan.target_id, plan.section_key)
            self.last_plan = plan
            return [plan.target_id]
        if plan.operation == "intersection":
            self.carousel.recall_with_convergence(plan.anchors)
            ids = self.carousel.vram.node_ids()
            self.current_subject_id = ids[0] if ids else None
            return list(plan.anchors)
        if plan.target_id is not None:
            self.carousel.step_to(plan.target_id)
            self.carousel.reinforce_supports(plan.target_id, (*plan.anchors, *plan.support_ids))
            self.current_subject_id = plan.target_id
            return [plan.target_id]
        return []

    def _consolidate_intent(self, intent: object) -> tuple[int, ...]:
        if not isinstance(intent, LanguageIntent) or intent.kind != "remember":
            return ()
        remembered = self.editor.consolidate(intent.proposal())
        self.current_subject_id = remembered[0].subject_id
        return tuple(value for item in remembered for value in (item.subject_id, item.assertion_id, item.predicate_id, item.object_id))

    def _memory_context(self, text: str, intent: LanguageIntent | None = None) -> str:
        """Render actual readings for LLM navigation, or preserve legacy context assembly."""
        self.carousel.context_report = {}
        # Preserve per-turn readings and their full directories, even after physical eviction.
        if self.planner_mode == "llm" and self.navigator.response is not None and self.navigator.workspace.nodes:
            context = self.navigator.workspace.render(self.carousel, self.navigator.status)
            self.carousel.context_report["memory_used"] = self.navigator.expose_memory
            return context
        if self.is_v1 and self.last_plan is not None and not self.last_plan.expose_memory:
            return json.dumps({"memory_used": False, "navigation_status": self.navigator.status})
        if self.planner_mode == "llm":
            if self.navigator.workspace.nodes:
                return self.navigator.workspace.render(self.carousel, self.navigator.status)
            return answer_context(self.carousel)
        sections: list[str] = []
        if len(self.carousel.vram) > 0:
            sections.append(build_vram_context(self.carousel))
        if self.is_v1:
            return "\n\n".join(sections) if sections else "(Nessun fatto specifico attivo in questo momento)"

        # The original concept/assertion seed remains usable without the V1 node planner.
        lines: list[str] = []
        seen: set[int] = set()
        sources = [text]
        if intent:
            sources.extend(value for value in (intent.subject, intent.question) if value)
        queries = [
            token
            for source in sources
            for token in re.findall(r"[a-zàèéìòóù0-9]+", source.lower())
            if len(token) > 2 and token not in _STOPWORDS
        ]
        for query in dict.fromkeys(queries):
            for result in self.search.cells_by_text(query, kind="concept", limit=8):
                if result.cell.id in seen:
                    continue
                seen.add(result.cell.id)
                label = str(cell_payload(self.store, result.cell.id).get("label") or result.cell.id)
                facts = self.editor.facts_about(result.cell.id)
                if not facts:
                    lines.append(f"- concept: {label}")
                    continue
                for fact in facts:
                    predicate = str(cell_payload(self.store, fact.predicate_id).get("label") or "?")
                    object_label = str(cell_payload(self.store, fact.object_id).get("label") or "?")
                    lines.append(f"- {label} {predicate} {object_label} (assertion {fact.assertion_id})")
        if lines:
            sections.append("\n".join(lines))
        return "\n\n".join(sections) if sections else "(nessun ricordo locale direttamente collegato alla richiesta)"

    def _answer(self, question: str) -> SessionReply:
        answer = self.language.answer(question)
        if answer.trace:
            self.current_subject_id = answer.trace[0]
        bundle = EvidenceBundle(answer.text, answer.trace, answer.trace[1::3] if answer.trace else ())
        return SessionReply(bundle.text, bundle.trace)

    def _current_subject_label(self) -> str | None:
        if self.current_subject_id is None:
            return None
        payload = cell_payload(self.store, self.current_subject_id)
        return str(payload.get("label") or payload.get("title") or payload.get("slug") or "")
