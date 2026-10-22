"""Bounded LLM-led navigation over complete directories, not semantic Core rules."""

from dataclasses import asdict
import json

from .budget import units
from .node import load_node
from .synaptic import StaleRevision, serialized
from .reading_workspace import ReadingWorkspace


def focus_context(carousel, *, structured=False) -> str | dict:
    """Reserve the full directory first; only the reading payload may be excerpted."""
    if carousel.reading_id is None:
        return ""
    if carousel.reading_id not in carousel.vram:
        carousel.recall(carousel.reading_id)
    directory = carousel.synaptic.directory(carousel.reading_id)
    node = carousel._fetch_node(carousel.reading_id)
    if node is None:
        return ""
    if not node.content_complete:
        node = load_node(carousel.store, node.id)
    header = json.dumps({"focus_id": directory.focus_id, "reading_id": node.id,
                         "title": node.title, "directory": directory.payload()}, ensure_ascii=False)
    budget = carousel.prompt_budget
    allowance = min(budget.per_node_limit, budget.memory_limit - budget.count(header) - 100)
    if allowance < 0:
        raise ValueError("Complete directory exceeds memory_limit; increase the configured budget or reorganize the node. No routes were truncated.")
    body = node.content
    if carousel.section_focus and carousel.section_focus[0] == node.id:
        section = next((s for s in node.sections if s.key == carousel.section_focus[1]), None)
        if section:
            body = section.content
    excerpt = budget.truncate(body, allowance)
    prefix = header + "\nContenuto:\n"
    text = prefix + excerpt + ("\n[estratto parziale]" if excerpt != body else "")
    carousel.context_report = {"node_ids": [node.id], "directory_revision": directory.revision,
        "focus_id": directory.focus_id, "reading_id": node.id, "directory_complete": True,
        "external_degree": directory.external_degree, "internal_parts": len(directory.parts),
        "truncated_ids": [node.id] if excerpt != body else [], "input_units": budget.count(text),
        "limit": budget.memory_limit, "accounting": budget.accounting, "span_unit": "utf8_bytes",
        "node_spans": [{"node_id": node.id, "start": units(prefix), "end": units(prefix + excerpt)}]}
    if structured:
        return {**json.loads(header), "content": excerpt, "partial_content": excerpt != body}
    return text


def answer_context(carousel):
    """Expose selected knowledge, not routing JSON, to the conversational renderer."""
    payload = focus_context(carousel, structured=True)
    if not payload:
        return ""
    prefix = payload["title"] + ":\n"
    body = payload["content"]
    text = prefix + body + ("\n[estratto parziale]" if payload["partial_content"] else "")
    carousel.context_report.update({"input_units": carousel.prompt_budget.count(text), "directory_in_answer": False,
        "directory_in_navigation": True, "node_spans": [{"node_id": payload["reading_id"],
            "start": units(prefix), "end": units(prefix + body)}]})
    return text


class MemoryNavigator:
    """Own per-turn routing state; persistent residency remains in the carousel."""
    def __init__(self, carousel, *, max_steps=8, search_limit=20, directory_bytes=65536, search_query_characters=2000):
        self.carousel = carousel
        self.memory = carousel.synaptic
        self.store = carousel.store
        self.max_steps, self.search_limit = max_steps, search_limit
        self.directory_bytes = directory_bytes
        self.search_query_characters = search_query_characters
        self.begin_turn()

    def begin_turn(self):
        """Use the same initialization on construction, reset and subsequent requests."""
        self.trace = []
        self.response = None
        self.expose_memory = False
        self.status = "not_started"
        self.entry_ids = ()
        self.search_performed = False
        self.workspace = ReadingWorkspace(self.carousel.prompt_budget)

    @serialized
    def run(self, text, adapter, history, task_context=""):
        """The model alone decides search terms, entry IDs, local steps and stopping."""
        self.begin_turn()
        self.status = "running"
        candidates = self.memory.entry_candidates(text, self.search_limit)
        self.entry_ids = tuple(entry.id for entry in candidates)
        self.search_performed = False
        search_revision = self.memory.store.revision if candidates else None
        self.trace.append({"action": "entry_index", "candidate_ids": self.entry_ids})
        visited = set()
        feedback = ""
        for _ in range(self.max_steps):
            # Complete addresses and actual content reads are separate inputs to the model.
            reading = self.carousel.reading_id
            directory = self.memory.directory(reading) if reading is not None else None
            context = focus_context(self.carousel, structured=True) if directory else {}
            self.workspace.remember(context)
            if directory and units(directory.render()) > self.directory_bytes:
                raise ValueError("Complete fast directory exceeds fast_index_bytes; increase its reserved budget.")
            state = {"focus": directory.focus_id if directory else None, "reading_id": reading,
                     "context": context, "global_candidates": [asdict(entry) for entry in candidates],
                     "read_nodes": self.workspace.payload(), "omitted_ids": self.workspace.omitted_ids,
                     "task": task_context,
                     "visited_ids": sorted(visited),
                     "local_target_ids": sorted(({directory.focus_id, *(entry.id for entry in (
                         *directory.incoming, *directory.outgoing, *directory.parts))} - {reading}) if directory else set()),
                     "index_checked": True, "feedback": feedback}
            try:
                proposal = adapter.navigate_memory(text, state, history)
            except Exception as error:
                self.status = "error"
                self.trace.append({"action": "provider_error", "error_type": type(error).__name__})
                raise
            if not isinstance(proposal, dict):
                proposal = {}
            action = proposal.get("action")
            self.trace.append({"action": action, "reading_id": reading})
            feedback = ""
            if action == "answer":
                # The final text is model output, not a semantic fallback generated by the Core.
                self.expose_memory = proposal.get("use_memory") is True and directory is not None
                answer = proposal.get("response")
                self.response = answer if isinstance(answer, str) and answer.strip() else None
                self.status = "answered"
                return
            if action == "search":
                query = proposal.get("query")
                if not isinstance(query, str) or not query.strip() or len(query) > self.search_query_characters:
                    feedback = {"error": "invalid_search_query"}
                    continue
                candidates = self.memory.global_lookup(query, self.search_limit)
                self.search_performed = True
                search_revision = self.memory.store.revision
                feedback = {"search_result_limit": self.search_limit}
                continue
            if action == "open":
                target = proposal.get("target_id")
                if type(target) is not int:
                    feedback = {"error": "invalid_target_id"}
                    continue
                try:
                    if proposal.get("source") == "global":
                        # Candidate IDs are valid only for the revision that produced them.
                        if search_revision != self.memory.store.revision:
                            raise StaleRevision("global_index_revision_mismatch")
                        if target not in {entry.id for entry in candidates}:
                            raise ValueError("target_not_in_global_candidates")
                    elif proposal.get("source", "local") == "local" and directory is not None:
                        self.memory.validate_step(reading, target, directory.revision)
                    else:
                        raise ValueError("no_current_directory")
                    if target == reading:
                        raise ValueError("target_already_open")
                    self.carousel.step_to(target)
                    visited.add(target)
                    self.expose_memory = True
                    feedback = {"opened_id": target}
                    self.trace[-1]["target_id"] = target
                    self.trace[-1]["source"] = proposal.get("source", "local")
                except (ValueError, KeyError) as error:
                    # Invalid routes become feedback, never silently substituted targets.
                    feedback = {"error": str(error)}
                continue
            feedback = {"error": "invalid_action"}
        # Bounded work is visible, not a semantic fallback to a Core-selected node.
        self.trace.append({"action": "step_limit", "limit": self.max_steps})
        self.status = "step_limit"
        if self.carousel.reading_id is not None:
            self.workspace.remember(focus_context(self.carousel, structured=True))
