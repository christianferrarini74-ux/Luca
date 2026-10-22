"""Opt-in real-model validation using only a disposable synthetic memory."""

import argparse
import json
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path

from .adapters import LMStudioAdapter
from .classification import ClassifiedDirectory
from .config import load_config
from .maintenance import IdleMaintenance, MemoryMaintenance
from .node import KnowledgeNode
from .session import LucaSession


class ObservedAdapter(LMStudioAdapter):
    def navigate_memory(self, text, state, history):
        started = time.perf_counter()
        try:
            choice = super().navigate_memory(text, state, history)
        except Exception as error:
            cause = error
            while cause.__cause__ is not None:
                cause = cause.__cause__
            diagnostic = {"error": str(error), "cause_type": type(cause).__name__, "cause": str(cause)}
            if hasattr(cause, "read"):
                diagnostic["provider_response"] = cause.read().decode("utf-8", errors="replace")[:2000]
            if isinstance(cause, json.JSONDecodeError):
                diagnostic["raw_response"] = cause.doc
            print(json.dumps(diagnostic, ensure_ascii=False), flush=True)
            raise
        event = {"focus": state["focus"], "reading_id": state["reading_id"], "choice": choice,
                 "seconds": round(time.perf_counter() - started, 3)}
        self.observations.append(event)
        print(json.dumps(event, ensure_ascii=False), flush=True)
        return choice


def family_index_read(session, root_id):
    """A family part may be the cursor when the family's index was actually read."""
    return (session.carousel.focus_id == root_id and root_id in session.navigator.workspace.nodes
            and session.carousel.reading_id is not None
            and session.carousel.synaptic.root(session.carousel.reading_id) == root_id)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--host-memory", action="store_true", help="Use host slots instead of the configured CUDA device.")
    args = parser.parse_args()
    config = load_config(args.config)
    adapter = ObservedAdapter.from_config(config)
    adapter.observations = []
    settings = dict(config["runtime"])
    if args.host_memory:
        settings["memory_backend"] = "host"
    root = Path(config["storage"]["database"]).parent
    root.mkdir(parents=True, exist_ok=True)
    fixture = Path(__file__).resolve().parents[1] / "seed/phase11_validation.json"
    report = {"model": adapter.model, "backend": settings.get("memory_backend"),
              "started_utc": datetime.now(UTC).isoformat(), "checks": [], "turns": []}
    report_path = root / ("phase11-live-" + datetime.now().strftime("%Y%m%d-%H%M%S") + ".json")
    try:
        with tempfile.TemporaryDirectory(prefix="phase11-live-", dir=root) as temporary:
            session = LucaSession.open(Path(temporary) / "synthetic.sqlite", fixture, adapter,
                vram_capacity=1, ram_capacity=2, planner_mode="llm", memory_settings=settings)
            memory = session.carousel.synaptic
            try:
                memory.attach_part(1, 2)
                memory.attach_part(1, 3)
                cases = [
                    ("global_entry", "Apri l'indice dell'Osservatorio Aurora e dimmi quali sezioni sono disponibili.", None, 1, 1),
                    ("family_part", "Apri la parte sull'apertura: qual è il codice di apertura?", "ZEFIRO-482", 1, 2),
                    ("external_route", "Dal ricordo attuale passa al Laboratorio Cobalto e dimmi il suo protocollo di accesso.", "IONIO-268", 4, 4),
                    ("natural_recall", "Qual è il codice di chiusura dell'Osservatorio Aurora?", "RAME-731", 1, 3),
                    ("resident_update", "Rileggi la parte sulla chiusura: quale codice vi è registrato ora?", "VELA-903", 1, 3),
                    ("general_knowledge", "Quanto fa 17 + 25?", "42", None, None),
                ]
                for name, question, expected, focus, reading in cases:
                    if name == "resident_update":
                        # Isolate cache freshness from the preceding semantic-navigation result.
                        session.recall_manual(3)
                        memory.update_node(KnowledgeNode(3, "aurora_chiusura", "Osservatorio Aurora - chiusura",
                            "Il codice di chiusura attuale dell'Osservatorio Aurora è VELA-903. Il precedente RAME-731 non è più valido."))
                    started = time.perf_counter()
                    first = len(adapter.observations)
                    try:
                        reply = session.handle(question)
                        choices = adapter.observations[first:]
                        position_ok = (family_index_read(session, focus) if name == "global_entry" else
                            focus is None or (session.carousel.focus_id, session.carousel.reading_id) == (focus, reading))
                        passed = (expected is None or expected in reply.text) and position_ok
                        passed = passed and not any(step["action"] == "step_limit" for step in session.navigator.trace)
                        passed = passed and bool(choices) and choices[-1]["choice"].get("action") == "answer"
                        if name == "global_entry":
                            passed = passed and any(item["choice"].get("source") == "global" for item in choices)
                            passed = passed and all(word in reply.text.lower() for word in ("apertura", "chiusura"))
                        if name == "external_route":
                            passed = passed and any(item["choice"].get("action") == "open" and
                                item["choice"].get("source") == "local" and item["choice"].get("target_id") == 4 for item in choices)
                        if name == "general_knowledge":
                            passed = passed and not session.navigator.expose_memory
                        turn = {"name": name, "question": question, "reply": reply.text, "passed": passed,
                                "focus": session.carousel.focus_id, "reading_id": session.carousel.reading_id,
                                "read_ids": list(session.navigator.workspace.nodes),
                                "trace": session.navigator.trace, "choices": choices,
                                "seconds": round(time.perf_counter() - started, 3)}
                    # Record diagnostic failures while allowing cleanup and the remaining checks.
                    except Exception as error:  # noqa: BLE001
                        turn = {"name": name, "passed": False, "error": str(error)}
                    report["turns"].append(turn)
                    report["checks"].append({"name": name, "passed": turn["passed"]})
                    print(json.dumps(turn, ensure_ascii=False), flush=True)
                memory.update_node(KnowledgeNode(100, "catalog", "Catalogo sintetico", "Indice di argomenti per verificare il raggruppamento."))
                for index in range(101, 152):
                    category = ("Botanica", "Geologia", "Astronomia")[(index - 101) // 17]
                    memory.update_node(KnowledgeNode(index, f"topic_{index}", f"{category} {index}", "Contenuto sintetico."))
                    memory.connect(100, index) if index < 135 else memory.connect(index, 100)
                maintenance = MemoryMaintenance(memory, session.synaptic_settings)
                try:
                    directory = memory.directory(100)
                    proposal = adapter.propose_groups(directory, session.synaptic_settings)
                    plan = maintenance.plan(100, proposal)
                    groups = ([{"title": title, "direction": direction, "members": list(members)}
                               for direction, title, members in proposal.categories(directory)]
                              if isinstance(proposal, ClassifiedDirectory) else proposal)
                    operation = maintenance.apply(plan, confirmed=True)
                    after = memory.directory(100).external_degree
                    maintenance.restore(operation, confirmed=True)
                    routes_restored = all(memory.store.edge(100, index) if index < 135 else memory.store.edge(index, 100)
                                          for index in range(101, 152))
                    passed = after <= session.synaptic_settings.edge_target and memory.directory(100).external_degree == 51 and routes_restored
                    report["maintenance"] = {"groups": groups, "before": 51, "after": after, "restored": 51}
                    report["maintenance"]["taxonomy_inspection"] = [{
                        "title": group["title"], "direction": group["direction"],
                        "source_categories": sorted({("Botanica", "Geologia", "Astronomia")[(nid - 101) // 17]
                                                     for nid in group["members"]})} for group in groups]
                    report["checks"].append({"name": "llm_grouping_and_restore", "passed": passed})
                # Record diagnostic failures while allowing cleanup and the remaining checks.
                except Exception as error:  # noqa: BLE001
                    report["maintenance"] = {"error": str(error)}
                    report["checks"].append({"name": "llm_grouping_and_restore", "passed": False})
                try:
                    sleep = IdleMaintenance(maintenance, adapter)
                    operation = sleep.run_once(now=sleep.last_activity + session.synaptic_settings.idle_seconds + 1)
                    after = memory.directory(100).external_degree
                    passed = operation is not None and after <= session.synaptic_settings.edge_target
                    if operation is not None:
                        maintenance.restore(operation, confirmed=True)
                    report["idle_maintenance"] = {"operation_id": operation, "after": after,
                        "restored": memory.directory(100).external_degree, "error": sleep.last_error,
                        "accelerated_idle_clock": True}
                    report["checks"].append({"name": "llm_idle_grouping", "passed": passed})
                # Record diagnostic failures while allowing cleanup and the remaining checks.
                except Exception as error:  # noqa: BLE001
                    report["idle_maintenance"] = {"error": str(error)}
                    report["checks"].append({"name": "llm_idle_grouping", "passed": False})
                report["physical_memory"] = session.carousel.physical_state()
            finally:
                device = session.carousel.vram.memory if settings.get("memory_backend") == "cuda" else None
                session.close()
                report["resources_released"] = device.closed if device else True
    finally:
        report["passed"] = len(report["checks"]) == 8 and all(check["passed"] for check in report["checks"]) and report.get("resources_released", False)
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"report": str(report_path), "passed": report["passed"], "checks": report["checks"]}, ensure_ascii=False), flush=True)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
