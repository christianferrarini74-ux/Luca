"""Ask about stopping decisions within the actual ongoing model conversation."""

import argparse
import copy
import hashlib
import json
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

from .bible import read_bible
from .config import load_config
from .controlled_document_check import DOCUMENT
from .model_memory_check import MeasuredAdapter, experiment_config
from .session import LucaSession

INITIAL = "La IRIS-17 mostra E42. Il segnale ora è tornato normale: come faccio a riprendere a irrigare?"
NEUTRAL = "Ritieni di aver risposto completamente alla mia prima domanda? C'è qualcosa che avresti dovuto approfondire?"


def explicit_question(initial_read_ids):
    """Never assert that a node was missed if the actual initial trace says otherwise."""
    if 3 in initial_read_ids:
        return ("Nella prima risposta hai letto anche le condizioni di apertura del capitolo 2. "
                "Che cosa ti ha portato ad approfondire quel punto?")
    return ("Nella tua prima risposta non hai aperto il capitolo 2, sulle condizioni di apertura della valvola. "
            "Perché ti sei fermato senza leggerlo?")


class InterviewAdapter(MeasuredAdapter):
    def navigate_memory(self, text, state, history):
        if not hasattr(self, "navigation_inputs"):
            self.navigation_inputs = []
        # Preserve actual public tool inputs, not inferred private model reasoning.
        self.navigation_inputs.append({"question": text, "state": copy.deepcopy(state),
                                       "history": copy.deepcopy(history)})
        return super().navigate_memory(text, state, history)


def interview(session, adapter, *, turns=None):
    """Keep one session, history and carousel through the neutral and explicit probes."""
    turns = [] if turns is None else turns
    initial_reads = []
    for stage in ("initial", "neutral", "explicit"):
        question = INITIAL if stage == "initial" else NEUTRAL if stage == "neutral" else explicit_question(initial_reads)
        first_choice = len(adapter.observations)
        first_request = len(getattr(adapter, "request_observations", ()))
        first_input = len(getattr(adapter, "navigation_inputs", ()))
        before = copy.deepcopy(session.history)
        started = perf_counter()
        reply = session.handle(question)
        readings = list(session.navigator.workspace.nodes)
        if stage == "initial":
            initial_reads = readings
        turn = {"stage": stage, "question": question, "reply": reply.text,
                "read_ids": readings, "sensor_read_this_turn": 3 in readings,
                "trace": list(session.navigator.trace), "history_before": before,
                "navigation_inputs": adapter.navigation_inputs[first_input:],
                "choices": adapter.observations[first_choice:],
                "requests": adapter.request_observations[first_request:],
                "seconds": round(perf_counter() - started, 3),
                "physical_memory": session.carousel.physical_state(),
                "navigation_status": session.navigator.status}
        turns.append(turn)
        print(json.dumps({key: turn[key] for key in ("stage", "question", "reply", "read_ids", "seconds")},
                         ensure_ascii=True), flush=True)
    return {"initial_sensor_read": 3 in initial_reads, "turns": turns}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--model", required=True)
    parser.add_argument("--repeat", type=int, default=1)
    args = parser.parse_args()
    if args.repeat < 1:
        parser.error("repeat must be positive")
    config = load_config(args.config)
    root = Path(config["storage"]["database"]).parent
    root.mkdir(parents=True, exist_ok=True)
    path = root / ("memory-interview-" + datetime.now(UTC).strftime("%Y%m%d-%H%M%S-%f") + ".json")
    report = {"model": args.model, "bible": read_bible(config["runtime"]["bible"]),
              "document_sha256": hashlib.sha256(DOCUMENT.read_bytes()).hexdigest(),
              "started_utc": datetime.now(UTC).isoformat(), "runs": [], "review_required": True,
              "note": "Model explanations are retrospective hypotheses. Conversation stores answers, not prior tool decisions. The explicit probe supplies one observed fact, never the answer key."}
    try:
        with tempfile.TemporaryDirectory(prefix="memory-interview-", dir=root) as directory:
            bible = Path(directory) / "bible.md"
            bible.write_text(report["bible"], encoding="utf-8")
            selected = experiment_config(config, args.model, bible)
            report["runtime"] = selected["runtime"]
            for repeat in range(args.repeat):
                adapter = InterviewAdapter.from_config(selected)
                adapter.observations = []
                session = LucaSession.open(Path(directory) / f"interview-{repeat}.sqlite", DOCUMENT, adapter,
                                           planner_mode="llm", memory_settings=selected["runtime"],
                                           vram_capacity=1, ram_capacity=1)
                run = {"repeat": repeat + 1, "turns": []}
                report["runs"].append(run)
                try:
                    run.update(interview(session, adapter, turns=run["turns"]))
                finally:
                    session.close()
                    run["resources_released"] = True
    finally:
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"report": str(path)}), flush=True)


if __name__ == "__main__":
    main()
