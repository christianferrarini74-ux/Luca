"""Bounded recall planning; model proposals never bypass Core graph validation."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from typing import Any

from .node import load_node, normalise_key
from .store import MemoryStore


_WORDS = re.compile(r"[a-z0-9_]+")
_STOP = set("a ad al alla alle anche altri altro animali che chi ci come con cosa da dal dei del della delle di dove e ed gli ha hai ho i il in io la le lo ma mai mi nei nel non o parlare parlami parliamo per perche poi puoi quale quali quando questi questo questa queste sai sei sentito si solo sono su sui sul ti tu un una voglio guidano conducono".split())


@dataclass(frozen=True, slots=True)
class RecallPlan:
    operation: str
    target_id: int | None = None
    anchors: tuple[int, ...] = ()
    excluded_ids: tuple[int, ...] = ()
    candidate_ids: tuple[int, ...] = ()
    reason: str = ""
    source: str = "rules"
    expose_memory: bool = True
    support_ids: tuple[int, ...] = ()

    def payload(self) -> dict[str, Any]:
        return asdict(self)


class RecallPlanner:
    """Interpret references before using topology to select a knowledge node."""

    def __init__(self, store: MemoryStore, *, mode: str = "hybrid") -> None:
        if mode not in {"rules", "hybrid"}:
            raise ValueError("planner mode must be 'rules' or 'hybrid'.")
        self.store = store
        self.mode = mode

    def _mentions(self, text: str) -> tuple[list[int], list[int]]:
        positive: list[int] = []
        negative: list[int] = []
        # Negation is scoped to clauses rather than deleting its subject from the graph.
        for clause in re.split(r"[,;:.!?]|\b(?:ma|invece)\b", normalise_key(text)):
            words = _WORDS.findall(clause)
            excluded = bool(re.search(r"\b(?:non|escludi|senza|eccetto|tranne)\b", clause))
            bucket = negative if excluded else positive
            for width in (4, 3, 2, 1):
                for start in range(len(words) - width + 1):
                    phrase = " ".join(words[start:start + width])
                    if width == 1 and phrase in _STOP:
                        continue
                    for cell in self.store.cells_by_alias(phrase, limit=4):
                        if cell.id not in bucket:
                            bucket.append(cell.id)
            if len(positive) + len(negative) >= 16:
                break
        return [nid for nid in positive if nid not in negative][:8], negative[:8]

    def _neighbors(self, focus: int) -> list[int]:
        return list(dict.fromkeys(
            [e.source_id for e in self.store.incoming(focus, limit=16)]
            + [e.target_id for e in self.store.outgoing(focus, limit=16)]
        ))

    def _family(self, focus: int, query: str) -> int | None:
        options = [focus, *self._neighbors(focus)]
        families = [nid for nid in options if self.store.out_degree(nid) >= 2]
        def score(nid: int) -> tuple[int, int]:
            node = load_node(self.store, nid)
            content = normalise_key(node.content) if node else ""
            enumeration = sum(word in content for word in ("diverse", "oltre", "ciascuno", "vari", "famiglia"))
            overlap = len((set(_WORDS.findall(query)) - _STOP) & set(_WORDS.findall(content)))
            return enumeration * 3 + overlap, self.store.out_degree(nid)
        return max(families, key=score) if families else None

    def plan(self, text: str, focus: int | None, adapter: Any = None) -> RecallPlan:
        query = normalise_key(text)
        mentions, excluded = self._mentions(text)
        available = [nid for nid in mentions if nid not in excluded]
        base = dict(anchors=tuple(available), excluded_ids=tuple(excluded))
        reference = bool(re.search(r"\b(?:questi|queste|questo|questa|stessi|stesse|quei|quelle)\b", query))
        causal = any(h in query for h in ("perche", "come mai", "come fanno", "come fa", "motivo", "ragione", "dipende", "causa"))
        forward = any(h in query for h in ("dove", "dentro", "cosa c", "cosa ci", "nascosto", "nasconde", "dopo", "succede", "poi"))
        if focus is not None and reference and not any(nid in excluded for nid in (focus,)):
            plan = RecallPlan("hold", focus, reason="Preserve the referenced object's attributes.", **base)
        elif focus is not None and "altri" in query and not reference:
            hub = self._family(focus, query)
            plan = RecallPlan("family", hub, reason="Enumerate the family rather than a shared destination.", **base) if hub else RecallPlan("unresolved", reason="No family found.", expose_memory=False, **base)
        elif focus is not None and (causal or forward) and (not available or available == [focus]):
            edges = self.store.incoming(focus, limit=16) if causal else self.store.outgoing(focus, limit=16)
            candidates = [e.source_id if causal else e.target_id for e in edges]
            candidates = [nid for nid in candidates if nid not in excluded]
            terms = set(_WORDS.findall(query)) - _STOP
            def relevance(nid: int) -> int:
                node = load_node(self.store, nid)
                content = normalise_key(node.content) if node else ""
                cues = ("grazie", "permette", "permettendo", "causa", "perche") if causal else ("attracc", "atterra", "dentro", "nascost", "raggiunge", "cadono")
                return sum(cue in content for cue in cues) * 3 + len(terms & set(_WORDS.findall(content)))
            ranked = sorted(candidates, key=relevance, reverse=True)
            target = ranked[0] if ranked and relevance(ranked[0]) > 0 and (len(ranked) == 1 or relevance(ranked[0]) > relevance(ranked[1])) else None
            plan = RecallPlan("cause" if causal else "consequence", target, candidate_ids=tuple(candidates), reason="Select content relevant to the requested relation; abstain on ties.", expose_memory=target is not None, **base)
        elif available:
            # A named child and its parent identify that child, not a common neighbor.
            specific = [nid for nid in available if any(self.store.edge(parent, nid) for parent in available if parent != nid)]
            if specific:
                plan = RecallPlan("focus", specific[0], reason="Explicit child of a named family.", **base)
            elif len(available) >= 2:
                plan = RecallPlan("intersection", reason="All explicit subjects are required.", **base)
            elif focus is not None and available[0] != focus and "cambiamo argomento" not in query and "in generale" not in query:
                anchors = [focus]
                anchors.extend(e.source_id for e in self.store.incoming(focus, limit=16) if self.store.out_degree(e.source_id) >= 2)
                result = self.store.resolve_convergence(available, context_anchors=anchors, hot_k=0)
                target = next((nid for nid in result.ranked_ids if nid not in excluded), None)
                plan = RecallPlan("lateral" if target else "focus", target or available[0], candidate_ids=result.ranked_ids, support_ids=tuple(anchors) if target else (), reason="Resolve the new subject within the active family.", **base)
            else:
                plan = RecallPlan("focus", available[0], reason="Explicit subject.", **base)
        else:
            plan = RecallPlan("unresolved", reason="No local subject or justified step found.", expose_memory=False, **base)

        # Restrict model proposals to ambiguous graph neighbors and bounded content previews.
        if self.mode == "hybrid" and plan.target_id is None and plan.candidate_ids and hasattr(adapter, "propose_recall"):
            previews = []
            for nid in plan.candidate_ids[:12]:
                node = load_node(self.store, nid)
                if node:
                    previews.append({"id": nid, "title": node.title[:160], "content": node.content[:800]})
            try:
                proposed = adapter.propose_recall(text, focus, previews, plan.operation)
                if isinstance(proposed, dict) and type(proposed.get("target_id")) is int:
                    target = proposed["target_id"]
                    if target in plan.candidate_ids and target not in excluded and focus is not None and (self.store.edge(focus, target) or self.store.edge(target, focus)):
                        return RecallPlan(plan.operation, target, plan.anchors, plan.excluded_ids, plan.candidate_ids, "Validated model proposal.", "llm", True)
            except (ValueError, TypeError, RuntimeError):
                pass
        return plan
