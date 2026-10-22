"""Compare fresh conversations with and without a controlled document."""

import argparse
import hashlib
import json
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

from .bible import read_bible
from .config import load_config
from .live_memory_check import ObservedAdapter
from .seed_v1 import knowledge_seed_from_file
from .session import LucaSession

ROOT = Path(__file__).resolve().parents[1]
DOCUMENT = ROOT / "seed/iris17_controlled_v1.json"
QUESTIONS = ROOT / "tests/fixtures/iris17_questions.json"
EMPTY = ROOT / "seed/library_empty_v1.json"


def indicators(case, text, readings, ids):
    """Report lexical/reading signals only; human semantic review remains required."""
    lowered = text.casefold()
    return {
        "lexical_match": all(any(term.casefold() in lowered for term in group) for group in case["terms"]),
        "required_nodes_read": all(ids[slug] in readings for slug in case["required_slugs"]),
        "review_required": True,
    }


def run_case(config, case, seed, database):
    """Give the model only the question and normal runtime memory, never the rubric."""
    adapter = ObservedAdapter.from_config(config)
    adapter.observations = []
    settings = config["runtime"]
    session = LucaSession.open(database, seed, adapter, planner_mode="llm", memory_settings=settings,
                               vram_capacity=int(settings.get("vram_capacity", 5)),
                               ram_capacity=int(settings.get("ram_capacity", 12)))
    started = perf_counter()
    try:
        reply = session.handle(case["question"])
        return {"model": adapter.model, "reply": reply.text, "read_ids": list(session.navigator.workspace.nodes),
                "trace": list(session.navigator.trace), "choices": list(adapter.observations),
                "navigation_status": session.navigator.status,
                "seconds": round(perf_counter() - started, 3),
                "request": dict(adapter.last_prompt_report),
                "physical_memory": session.carousel.physical_state()}
    finally:
        session.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--case", default="all", help="Case ID, or all; each arm starts a fresh session.")
    args = parser.parse_args()
    cases = json.loads(QUESTIONS.read_text(encoding="utf-8"))
    selected = [case for case in cases if args.case in ("all", case["id"])]
    if not selected:
        parser.error("Unknown case; choose all or " + ", ".join(case["id"] for case in cases))
    config = load_config(args.config)
    root = Path(config["storage"]["database"]).parent
    root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S-%f")
    path = root / f"iris17-check-{stamp}.json"
    report = {
        "started_utc": datetime.now(UTC).isoformat(),
        "document_sha256": hashlib.sha256(DOCUMENT.read_bytes()).hexdigest(),
        "questions_sha256": hashlib.sha256(QUESTIONS.read_bytes()).hexdigest(),
        "bible_snapshot": read_bible(config["runtime"]["bible"]),
        "runtime": config["runtime"],
        "llm": {"active_runtime": config.get("llm", {}).get("active_runtime")},
        "note": "Fixed baseline-then-document order; fresh sessions. Signals are not semantic certification.",
        "turns": [], "review_required": True,
    }
    # Runtime reports contain adapter outcomes and the answer key, never sent back to the model.
    # Record only selected non-secret model metadata, not full provider configuration.
    ids = knowledge_seed_from_file(DOCUMENT).ids
    try:
        with tempfile.TemporaryDirectory(prefix="iris17-check-", dir=root) as directory:
            for case in selected:
                result = {"id": case["id"], "question": case["question"], "rubric": case["rubric"]}
                report["turns"].append(result)
                for arm, seed in (("baseline", EMPTY), ("document", DOCUMENT)):
                    print(f"Starting {case['id']} / {arm}", flush=True)
                    try:
                        outcome = run_case(config, case, seed, Path(directory) / f"{case['id']}-{arm}.sqlite")
                        outcome["indicators"] = indicators(case, outcome["reply"], outcome["read_ids"], ids)
                        result[arm] = outcome
                    # Diagnostic failures must not prevent cleanup or the other arm.
                    except Exception as error:  # noqa: BLE001
                        result[arm] = {"error": str(error)}
                    print(json.dumps({"case": case["id"], "arm": arm, **result[arm]}, ensure_ascii=True), flush=True)
        report["resources_released"] = True
    finally:
        # Persist partial evidence even when the user interrupts an expensive live run.
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"report": str(path), "review_required": True}), flush=True)
    return int(any("error" in turn.get(arm, {}) for turn in report["turns"] for arm in ("baseline", "document")))


if __name__ == "__main__":
    raise SystemExit(main())
