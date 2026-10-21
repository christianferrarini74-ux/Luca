"""Bounded LLM-led navigation over complete directories, not semantic Core rules."""

from dataclasses import asdict
import json

from .budget import clip, units
from .node import load_node
from .synaptic import StaleRevision, serialized


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
    allowance = min(budget.per_node_limit, budget.memory_limit - units(header) - 100)
    if allowance < 0:
        raise ValueError("Complete directory exceeds memory_limit; increase the configured budget or reorganize the node. No routes were truncated.")
    body = node.content
    if carousel.section_focus and carousel.section_focus[0] == node.id:
        section = next((s for s in node.sections if s.key == carousel.section_focus[1]), None)
        if section:
            body = section.content
    excerpt = clip(body, allowance)
    prefix = header + "\nContenuto:\n"
    text = prefix + excerpt + ("\n[estratto parziale]" if excerpt != body else "")
    carousel.context_report = {"node_ids": [node.id], "directory_revision": directory.revision,
        "focus_id": directory.focus_id, "reading_id": node.id, "directory_complete": True,
        "external_degree": directory.external_degree, "internal_parts": len(directory.parts),
        "truncated_ids": [node.id] if excerpt != body else [], "input_units": units(text),
        "limit": budget.memory_limit, "accounting": "utf8_bytes_conservative",
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
    carousel.context_report.update({"input_units": units(text), "directory_in_answer": False,
        "directory_in_navigation": True, "node_spans": [{"node_id": payload["reading_id"],
            "start": units(prefix), "end": units(prefix + body)}]})
    return text


class MemoryNavigator:
    def __init__(self, carousel, *, max_steps=8, search_limit=20, directory_bytes=65536):
        self.carousel = carousel
        self.memory = carousel.synaptic
        self.store = carousel.store
        self.max_steps, self.search_limit = max_steps, search_limit
        self.directory_bytes = directory_bytes
        self.trace = []
        self.expose_memory = False
        self.entry_ids = ()
        self.search_performed = False

    @serialized
    def run(self, text, adapter, history):
        """The model alone decides search terms, entry IDs, local steps and stopping."""
        self.trace = []
        self.expose_memory = False
        candidates = self.memory.entry_candidates(text, self.search_limit)
        self.entry_ids = tuple(entry.id for entry in candidates)
        self.search_performed = False
        search_revision = self.memory.store.revision if candidates else None
        self.trace.append({"action": "entry_index", "candidate_ids": self.entry_ids})
        visited = set()
        feedback = ""
        for _ in range(self.max_steps):
            reading = self.carousel.reading_id
            directory = self.memory.directory(reading) if reading is not None else None
            context = focus_context(self.carousel, structured=True) if directory else {}
            if directory and units(directory.render()) > self.directory_bytes:
                raise ValueError("Complete fast directory exceeds fast_index_bytes; increase its reserved budget.")
            state = {"focus": directory.focus_id if directory else None, "reading_id": reading,
                     "context": context, "global_candidates": [asdict(entry) for entry in candidates],
                     "visited_ids": sorted(visited),
                     "local_target_ids": sorted(({directory.focus_id, *(entry.id for entry in (
                         *directory.incoming, *directory.outgoing, *directory.parts))} - {reading}) if directory else set()),
                     "index_checked": True, "feedback": feedback}
            proposal = adapter.navigate_memory(text, state, history)
            if not isinstance(proposal, dict):
                proposal = {}
            action = proposal.get("action")
            self.trace.append({"action": action, "reading_id": reading})
            feedback = ""
            if action == "answer":
                self.expose_memory = proposal.get("use_memory") is True and directory is not None
                return
            if action == "search":
                query = proposal.get("query")
                if not isinstance(query, str) or not query.strip() or len(query) > 2000:
                    feedback = "Provide a nonempty search query of at most 2000 characters."
                    continue
                candidates = self.memory.global_lookup(query, self.search_limit)
                self.search_performed = True
                search_revision = self.memory.store.revision
                feedback = f"At most {self.search_limit} global candidates are shown; refine the query if necessary."
                continue
            if action == "open":
                target = proposal.get("target_id")
                if type(target) is not int:
                    feedback = "target_id must be an integer from the current directory or search results."
                    continue
                try:
                    if proposal.get("source") == "global":
                        if search_revision != self.memory.store.revision:
                            raise StaleRevision("Search results changed; search again.")
                        if target not in {entry.id for entry in candidates}:
                            raise ValueError("The ID is not in the latest global results.")
                    elif directory is not None:
                        self.memory.validate_step(reading, target, directory.revision)
                    else:
                        raise ValueError("Search for a global entry first.")
                    if target == reading:
                        raise ValueError("Questo nodo è già aperto: leggi context e rispondi, oppure apri un nodo diverso.")
                    self.carousel.step_to(target)
                    visited.add(target)
                    self.expose_memory = True
                    feedback = f"Nodo {target} aperto. Il suo contenuto è ora in context. Se basta, scegli answer; non riaprirlo."
                    candidates = ()
                    search_revision = None
                    self.trace[-1]["target_id"] = target
                    self.trace[-1]["source"] = proposal.get("source", "local")
                except (ValueError, KeyError) as error:
                    feedback = str(error)
                continue
            feedback = "Use action search, open or answer; do not invent an ID."
        # Bounded work is visible, not a semantic fallback to a Core-selected node.
        self.trace.append({"action": "step_limit", "limit": self.max_steps})
