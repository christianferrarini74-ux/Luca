"""A token-bounded, per-turn workspace of actually read nodes and directories."""

import json
from .budget import units


class ReadingWorkspace:
    def __init__(self, budget):
        self.budget = budget
        self.nodes = {}
        self.omitted_ids = []

    def remember(self, payload):
        if not payload:
            return
        identity = payload["reading_id"]
        if identity in self.omitted_ids:
            self.omitted_ids.remove(identity)
        self.nodes.pop(identity, None)
        self.nodes[identity] = payload
        while self.budget.count(self._text("step_limit")) > self.budget.memory_limit:
            if len(self.nodes) == 1:
                raise ValueError("The complete reading directory exceeds memory_limit.")
            oldest = next(iter(self.nodes))
            del self.nodes[oldest]
            if oldest not in self.omitted_ids:
                self.omitted_ids.append(oldest)

    def payload(self):
        return list(self.nodes.values())

    def _text(self, status):
        return json.dumps({"navigation_status": status, "read_nodes": self.payload(),
                           "omitted_ids": self.omitted_ids}, ensure_ascii=False)

    def render(self, carousel, status):
        readings = self.payload()
        prefix = '{"navigation_status": ' + json.dumps(status) + ', "read_nodes": ['
        parts, spans = [], []
        for node in readings:
            text = json.dumps(node, ensure_ascii=False)
            start = units(prefix + ", ".join(parts) + (", " if parts else ""))
            spans.append({"node_id": node["reading_id"], "start": start, "end": start + units(text)})
            parts.append(text)
        text = prefix + ", ".join(parts) + '], "omitted_ids": ' + json.dumps(self.omitted_ids) + '}'
        carousel.context_report = {"node_ids": list(self.nodes), "node_spans": spans,
            "focus_id": carousel.focus_id, "reading_id": carousel.reading_id,
            "directory_complete": True, "directory_in_answer": True, "directory_in_navigation": True,
            "input_units": self.budget.count(text), "limit": self.budget.memory_limit,
            "accounting": self.budget.accounting, "span_unit": "utf8_bytes",
            "truncated_ids": [node["reading_id"] for node in readings if node.get("partial_content")],
            "omitted_ids": list(self.omitted_ids), "navigation_status": status}
        return text
