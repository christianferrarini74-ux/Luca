"""Bounded recent activity; historical opening never grants permanent priority."""

from collections import deque
from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class ActivityEvent:
    kind: str
    node_id: int
    tick: int
    source_id: int | None = None


class MemoryActivity:
    def __init__(self, recent_window: int = 8, max_recent: int = 256) -> None:
        if recent_window < 1 or max_recent < 1:
            raise ValueError("Activity limits must be positive.")
        self.window = recent_window
        self.max_recent = max_recent
        self.tick = 0
        self.recent: dict[int, int] = {}
        self.events: deque[ActivityEvent] = deque(maxlen=128)

    def advance(self) -> None:
        self.tick += 1
        self.recent = {nid: tick for nid, tick in self.recent.items() if self.tick - tick < self.window}

    def record(self, kind: str, node_id: int, source_id: int | None = None) -> None:
        self.events.append(ActivityEvent(kind, node_id, self.tick, source_id))
        if kind in {"open", "traverse", "expose"}:
            self.recent[node_id] = self.tick
            if len(self.recent) > self.max_recent:
                oldest = min(self.recent, key=self.recent.get)
                del self.recent[oldest]

    def snapshot(self) -> dict:
        return {"tick": self.tick, "recent_ids": list(self.recent), "window": self.window,
                "events": [asdict(event) for event in self.events]}
