"""Explicit, bounded task continuity independent of the active knowledge cluster."""

import json
import re
from dataclasses import asdict, dataclass, field

from .budget import units
from .node import normalise_key


@dataclass
class TaskState:
    goal: str = ""
    constraints: list[str] = field(default_factory=list)
    decisions: list[str] = field(default_factory=list)
    focus_id: int | None = None
    section_key: str | None = None
    suspended: bool = False
    trail: list[int] = field(default_factory=list)

    @property
    def active(self) -> bool:
        return bool(self.goal or self.constraints or self.decisions)

    def render(self) -> str:
        if not self.active:
            return ""
        lines = [f"Obiettivo del lavoro: {self.goal}"]
        lines.extend(f"Vincolo: {value}" for value in self.constraints)
        lines.extend(f"Decisione confermata: {value}" for value in self.decisions)
        return "\n".join(lines)


class TaskMemory:
    def __init__(self, store, limit: int = 512, *, counter=units) -> None:
        self.store = store
        self.limit = limit
        self.count = counter
        row = store.connection.execute("SELECT payload FROM task_state WHERE name = 'current'").fetchone()
        self.state = TaskState(**json.loads(row[0])) if row else TaskState()
        if self.count(self.state.render()) > limit:
            raise ValueError("Il compito salvato supera task_limit; aumenta il budget prima di riprenderlo.")

    def _save(self, state: TaskState) -> None:
        if self.count(state.render()) > self.limit:
            raise ValueError("Obiettivo, vincoli e decisioni superano task_limit; abbreviali o aumenta il budget.")
        payload = json.dumps(asdict(state), ensure_ascii=False)
        with self.store.transaction():
            self.store.connection.execute(
                "INSERT INTO task_state (name, payload) VALUES ('current', ?) ON CONFLICT(name) DO UPDATE SET payload=excluded.payload",
                (payload,),
            )
        self.state = state

    def update(self, values: dict, focus: int | None = None) -> None:
        if not isinstance(values, dict) or set(values) - {"goal", "constraints", "decisions", "clear"}:
            raise ValueError("Task updates accept goal, constraints, decisions and clear only.")
        if "clear" in values and type(values["clear"]) is not bool:
            raise ValueError("Task clear must be a boolean.")
        state = TaskState() if values.get("clear") is True else TaskState(**asdict(self.state))
        for key in ("goal", "constraints", "decisions"):
            if key not in values:
                continue
            value = values[key]
            if key == "goal":
                if not isinstance(value, str):
                    raise ValueError("Task goal must be text.")
                state.goal = value.strip()
            else:
                if not isinstance(value, list) or len(value) > 8 or any(not isinstance(item, str) for item in value):
                    raise ValueError("Task constraints and decisions must each contain at most eight strings.")
                setattr(state, key, list(dict.fromkeys(item.strip() for item in value if item.strip())))
        if state.active and state.focus_id is None:
            state.focus_id = focus
        self._save(state)

    def apply_text(self, text: str, focus: int | None) -> bool:
        match = re.fullmatch(r"\s*(obiettivo|nuovo compito|vincolo|decisione)\s*:\s*(.+)\s*", text, re.IGNORECASE | re.DOTALL)
        if not match:
            return False
        kind, value = match.groups()
        kind = normalise_key(kind)
        if kind in {"obiettivo", "nuovo compito"}:
            self.update({"goal": value, "clear": kind == "nuovo compito"}, focus)
        else:
            key = "constraints" if kind == "vincolo" else "decisions"
            self.update({key: [*getattr(self.state, key), value]}, focus)
        return True

    @staticmethod
    def requests_resume(text: str) -> bool:
        text = normalise_key(text)
        return any(phrase in text for phrase in ("riprendi il compito", "riprendiamo il lavoro", "torniamo al compito", "riprendi il lavoro"))

    def observe(self, previous: int | None, current: int | None, connected: bool, section: str | None = None) -> None:
        state = TaskState(**asdict(self.state))
        if not state.active or current is None:
            return
        if current != previous:
            state.trail = [*state.trail, current][-8:]
        if state.focus_id is None:
            state.focus_id, state.section_key = current, section
        elif not state.suspended:
            if previous is not None and previous != current and not connected:
                state.suspended = True
            else:
                state.focus_id, state.section_key = current, section
        if state != self.state:
            self._save(state)

    def resumed(self) -> None:
        state = TaskState(**asdict(self.state))
        state.suspended = False
        self._save(state)

    def snapshot(self) -> dict:
        return {**asdict(self.state), "active": self.state.active, "input_units": self.count(self.state.render()), "limit": self.limit}
