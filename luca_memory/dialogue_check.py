"""Replay the reported dialogue against an isolated copy of the configured seed."""

import argparse
import json
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from .config import load_config
from .live_memory_check import ObservedAdapter
from .seed_v1 import knowledge_seed_from_file
from .session import LucaSession


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="config.yaml")
    args = parser.parse_args()
    config = load_config(args.config)
    adapter = ObservedAdapter.from_config(config)
    adapter.observations = []
    storage = Path(config["storage"]["database"]).parent
    storage.mkdir(parents=True, exist_ok=True)
    report_path = storage / ("dialogue-live-" + datetime.now().strftime("%Y%m%d-%H%M%S") + ".json")
    seed = config["storage"]["seed"]
    expected_id = knowledge_seed_from_file(seed).id_for("famiglia_topi")
    report = {"model": adapter.model, "started_utc": datetime.now(UTC).isoformat(),
              "note": "Lexical regression checks, not certification of biological facts.", "turns": []}
    cases = [
        ("recall_entry", "Hai mai sentito parlare dei topi intagliatori di formaggio?", "memory"),
        ("general_classification", "Dimmi che animale è il topo", "classification"),
        ("general_biology", "descrivimi nel mondo animale come vive un topo", "general"),
        ("concept_question", "Secondo te un animale come fa ad intagliare un materiale?", "review"),
        ("return_to_memory", "e allora perchè i topi intagliano il formaggio?", "memory"),
        ("memory_confirmation", "Si ma io so che ci sono topi intagliatori di formaggio", "memory"),
        ("repeated_recall", "hai mai sentito parlare dei topi intagliatori di formaggio?", "memory"),
    ]
    try:
        with tempfile.TemporaryDirectory(prefix="dialogue-check-", dir=storage) as directory:
            session = LucaSession.open(Path(directory) / "synthetic.sqlite", seed, adapter,
                vram_capacity=int(config["runtime"].get("vram_capacity", 5)),
                ram_capacity=int(config["runtime"].get("ram_capacity", 12)),
                planner_mode="llm", memory_settings=config["runtime"])
            try:
                for name, question, kind in cases:
                    try:
                        reply = session.handle(question)
                        text = reply.text.lower()
                        uses_memory = session.navigator.expose_memory
                        if kind == "memory":
                            passed = uses_memory and session.carousel.focus_id == expected_id and any(
                                word in text for word in ("cantin", "parmigian", "ingegner", "macchinar", "precisione"))
                            passed = passed and not any(word in text for word in (
                                "metafor", "racconto", "narrazion", "contesto fornito", "contenuto fornito", "mi sono stati forniti"))
                        elif kind == "classification":
                            passed = any(word in text for word in ("mammifer", "roditor")) and not any(
                                word in text for word in ("ingegner", "macchinar"))
                        elif kind == "general":
                            passed = not uses_memory and not any(word in text for word in ("ingegner", "macchinar"))
                        else:
                            passed = None
                        turn = {"name": name, "question": question, "reply": reply.text,
                            "passed": passed, "use_memory": uses_memory,
                            "focus_id": session.carousel.focus_id,
                            "entry_candidate_ids": session.navigator.entry_ids,
                            "trace": list(session.navigator.trace), "request": dict(adapter.last_prompt_report)}
                        turn["style_warnings"] = [word for word in (
                            "fornit", "ricevut", "racconto", "narrazion", "metafor", "si dice")
                            if kind == "memory" and word in text]
                    # Record diagnostic failures in the report and continue cleanup/remaining checks.
                    except Exception as error:  # noqa: BLE001
                        turn = {"name": name, "question": question, "passed": False, "error": str(error)}
                    report["turns"].append(turn)
                    print(json.dumps(turn, ensure_ascii=True), flush=True)
            finally:
                session.close()
                report["resources_released"] = True
    finally:
        assessed = [turn for turn in report["turns"] if turn["passed"] is not None]
        report["retrieval_checks_passed"] = len(assessed) == 6 and all(turn["passed"] for turn in assessed)
        report["style_passed"] = not any(turn.get("style_warnings") for turn in report["turns"])
        report["passed"] = report["retrieval_checks_passed"] and report["style_passed"]
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"report": str(report_path), "passed": report["passed"]}), flush=True)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
