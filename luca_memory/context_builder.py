"""Assemble only the opened ([APERTA]) nodes of the active connected VRAM chain into LLM context."""

from __future__ import annotations

from typing import Any

from .node import KnowledgeNode, load_node
from .tiers.carousel import SynapticCarousel
from .budget import clip, units


def active_vram_component_ids(carousel: SynapticCarousel) -> set[int]:
    """Return the node IDs in VRAM connected via prefix:suffix edges to the current focus node."""

    vram_nodes = carousel.vram.nodes()
    if not vram_nodes:
        return set()

    valid_ids = {node.id for node in vram_nodes}
    focus_id = vram_nodes[0].id
    visited: set[int] = {focus_id}
    queue: list[int] = [focus_id]

    while queue:
        current = queue.pop(0)
        neighbors = [
            edge.source_id
            for edge in carousel.vram_graph.incoming_for(current)
            if edge.source_id in valid_ids
        ] + [
            edge.target_id
            for edge in carousel.vram_graph.outgoing_for(current)
            if edge.target_id in valid_ids
        ]
        for neighbor_id in neighbors:
            if neighbor_id not in visited:
                visited.add(neighbor_id)
                queue.append(neighbor_id)

    return visited


def build_vram_context(carousel: SynapticCarousel) -> str:
    """Expose only opened ([APERTA]) nodes in the active connected VRAM component to prevent premature spoilers."""

    vram_nodes = carousel.vram.nodes()
    if not vram_nodes:
        return "Fatti noti:\n- Nessun dettaglio registrato su questo argomento."

    connected_ids = active_vram_component_ids(carousel)
    open_nodes: list[KnowledgeNode] = [
        node
        for node in vram_nodes
        if node.id in connected_ids and node.id in carousel.expanded_in_vram
    ]
    if not open_nodes:
        open_nodes = [vram_nodes[0]]

    budget = carousel.prompt_budget
    lines = ["Fatti noti:"]
    exposed: list[int] = []
    truncated: list[int] = []

    def append_node(node: KnowledgeNode, label: str, *, opened: bool = True) -> None:
        source = load_node(carousel.store, node.id) if not node.content_complete else node
        source = source or node
        body = source.summary or source.content
        section_title = ""
        if carousel.section_focus and carousel.section_focus[0] == node.id:
            section = next((s for s in source.sections if s.key == carousel.section_focus[1]), None)
            if section:
                body = section.content
                section_title = " / " + section.title
        prefix = f"- {label} {clip(source.title + section_title, 256)}: "
        remaining = budget.memory_limit - units("\n".join(lines)) - 1
        if remaining <= units(prefix) + 40:
            truncated.append(node.id)
            return
        allowance = min(budget.per_node_limit, remaining - units(prefix) - 40)
        excerpt = clip(body, allowance)
        if units(excerpt) < units(body):
            excerpt += " [estratto parziale]"
            truncated.append(node.id)
        lines.append(prefix + excerpt)
        if opened:
            exposed.append(node.id)

    for index, node in enumerate(open_nodes):
        append_node(node, "[FOCUS CORRENTE]" if index == 0 else "[CONTESTO GIÀ APERTO]")

    conv = carousel.last_convergence
    if conv is not None and conv.mode == "strict" and conv.has_only_partial_matches:
        # Plain Italian only: small models echo any technical label they read (see doc 05).
        notice = "- Non conosco nessun fatto che riguardi insieme tutto quello che è stato chiesto."
        # Reserve the notice before adding partial candidates.
        while len(lines) > 1 and units("\n".join([*lines, notice])) > budget.memory_limit:
            lines.pop()
        lines.append(notice)
        for match in conv.partial_matches[:3]:
            partial_node = load_node(carousel.store, match.node_id)
            if partial_node is not None:
                append_node(partial_node, "So soltanto questo, che riguarda solo una parte della domanda:", opened=False)
    text = clip("\n".join(lines), budget.memory_limit)
    carousel.context_report = {"node_ids": exposed, "truncated_ids": truncated,
                               "input_units": units(text), "limit": budget.memory_limit,
                               "accounting": "utf8_bytes_conservative", "section": carousel.section_focus}
    return text


EMPTY_STRICT_LABEL = "[INTERSEZIONE VINCOLANTE VUOTA]"


def partial_match_label(matched_required: int, required_total: int) -> str:
    return f"[CORRISPONDENZA PARZIALE ({matched_required}/{required_total} vincoli)]"


def convergence_signals(carousel: SynapticCarousel, *, previous: bool = False) -> dict[str, Any] | None:
    """Structured convergence outcome with technical labels, for the API/dashboard only (never for the LLM prompt)."""

    conv = carousel.previous_convergence if previous else carousel.last_convergence
    if conv is None:
        return None

    def describe(match: Any) -> dict[str, Any]:
        node = load_node(carousel.store, match.node_id)
        return {
            "id": match.node_id,
            "title": node.title if node else str(match.node_id),
            "matched_required": match.matched_required,
            "required_total": match.required_total,
            "matched_context": match.matched_context,
            "context_total": match.context_total,
        }

    empty_strict = conv.mode == "strict" and conv.has_only_partial_matches
    return {
        "mode": conv.mode,
        "strategy": conv.strategy,
        "search_scope": "hot_candidates" if conv.strategy == "hot_first" else "full_graph",
        "ranking_is_global": conv.strategy != "hot_first",
        "historical": previous,
        "alternatives": [describe(m) for m in conv.available_alternatives],
        "required_anchors": list(conv.required_anchors),
        "context_anchors": list(conv.context_anchors),
        "ranked_ids": list(conv.ranked_ids),
        "opened_ids": list(conv.opened_ids),
        "unopened_ids": list(conv.unopened_ids),
        "exact_matches": [describe(m) for m in conv.exact_matches],
        "partial_matches": [
            {**describe(m), "label": partial_match_label(m.matched_required, m.required_total)}
            for m in conv.partial_matches
        ],
        "status_label": EMPTY_STRICT_LABEL if empty_strict else None,
        "estimated_seed_edges": conv.estimated_seed_edges,
        "timings_ms": {
            "selection": round(conv.selection_ms, 3),
            "query": round(conv.query_ms, 3),
            "recall": round(conv.recall_ms, 3),
        },
    }



