"""Isolated A/B investigation of memory coverage and scoped knowledge updates."""

import argparse
import copy
import hashlib
import json
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from .bible import read_bible
from .config import load_config
from .controlled_document_check import ROOT, indicators, run_case
from .live_memory_check import ObservedAdapter
from .seed_v1 import knowledge_seed_from_file

CASES = ROOT / "tests/fixtures/autonomy_questions.json"
GUIDANCE = ROOT / "experiments/autonomy-guidance.it.md"
REVIEW = ROOT / "experiments/autonomy-review.it.md"


class AuditedAdapter(ObservedAdapter):
    """Prototype one model self-review, never a Core-selected retrieval route."""

    def navigate_memory(self, text, state, history):
        proposal = super().navigate_memory(text, state, history)
        if proposal.get("action") != "answer" or getattr(self, "draft_reviewed", False):
            return proposal
        self.draft_reviewed = True
        # Only experimental data is added; review instructions live in the profile bible.
        review_state = {**state, "draft_response": proposal.get("response", "")}
        self.observations[-1]["draft_proposal"] = True
        reviewed = super().navigate_memory(text, review_state, history)
        self.observations[-1]["draft_review"] = True
        return reviewed


def profile_config(config, bible_path):
    """Keep the application's config and primary instruction file untouched."""
    experimental = copy.deepcopy(config)
    experimental["runtime"]["bible"] = str(bible_path)
    return experimental


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--questions", type=Path, default=CASES, help="Question set; evaluation rubrics are never sent to the model.")
    parser.add_argument("--model", help="Override the model only in the experimental configuration copy.")
    parser.add_argument("--capture-inputs", action="store_true", help="Record actual public navigation states.")
    parser.add_argument("--vram-capacity", type=int, help="Experimental slot override; main config is not edited.")
    parser.add_argument("--ram-capacity", type=int, help="Experimental slot override; main config is not edited.")
    parser.add_argument("--case", default="all", help="Comma-separated case IDs, or all.")
    parser.add_argument("--profile", choices=("all", "current", "candidate", "audited", "addressed"), default="all")
    parser.add_argument("--repeat", type=int, default=1)
    args = parser.parse_args()
    cases = json.loads(args.questions.read_text(encoding="utf-8"))
    if args.capture_inputs and args.profile == "audited":
        parser.error("Input capture and the audited adapter are separate experimental modes.")
    if any(value is not None and value < 1 for value in (args.vram_capacity, args.ram_capacity)):
        parser.error("Slot overrides must be positive.")
    wanted = set(args.case.split(","))
    if args.repeat < 1 or (args.case != "all" and not wanted.issubset({case["id"] for case in cases})):
        parser.error("Use positive repeats and existing case IDs.")
    selected = [case for case in cases if args.case == "all" or case["id"] in wanted]
    config = load_config(args.config)
    for name, value in (("vram_capacity", args.vram_capacity), ("ram_capacity", args.ram_capacity)):
        if value is not None:
            config["runtime"][name] = value
    if args.model:
        active = config["llm"]["active_runtime"]
        role = config["runtime"].get("adapter_role", "orchestrator")
        config["llm"]["runtimes"][active]["agents"][role]["model"] = args.model
    capture_adapter = None
    if args.capture_inputs:
        # Import lazily: the continuous-session diagnostic also reuses this module's fixtures.
        from .memory_interview_check import InterviewAdapter
        capture_adapter = InterviewAdapter
    base = read_bible(config["runtime"]["bible"])
    guidance = GUIDANCE.read_text(encoding="utf-8").strip()
    profiles = {"current": base, "candidate": base + "\n\n" + guidance}
    if args.profile == "audited":
        profiles = {"audited": profiles["candidate"] + "\n\n" + REVIEW.read_text(encoding="utf-8").strip()}
    elif args.profile == "addressed":
        profiles = {"addressed": base}
    root = Path(config["storage"]["database"]).parent
    root.mkdir(parents=True, exist_ok=True)
    path = root / ("autonomy-check-" + datetime.now(UTC).strftime("%Y%m%d-%H%M%S-%f") + ".json")
    report = {"started_utc": datetime.now(UTC).isoformat(), "profiles": profiles,
              "questions_path": str(args.questions.resolve()),
              "questions_sha256": hashlib.sha256(args.questions.read_bytes()).hexdigest(),
              "profile_sha256": {key: hashlib.sha256(value.encode()).hexdigest() for key, value in profiles.items()},
              "runtime": config["runtime"], "turns": [], "review_required": True,
              "note": "Fresh sessions; fixed current/candidate order. Stale history is explicitly injected test data, not an old model's generated answer."}
    try:
        with tempfile.TemporaryDirectory(prefix="autonomy-check-", dir=root) as directory:
            for repeat in range(args.repeat):
                for case in selected:
                    seed = ROOT / "seed" / case["seed"]
                    if args.profile == "addressed" and case["seed"] == "iris17_controlled_v1.json":
                        seed = ROOT / "seed/iris17_addressed_v1.json"
                    ids = knowledge_seed_from_file(seed).ids
                    turn = {"case": case, "repeat": repeat + 1, "seed": str(seed),
                            "seed_sha256": hashlib.sha256(seed.read_bytes()).hexdigest()}
                    report["turns"].append(turn)
                    for profile, bible in profiles.items():
                        if args.profile not in ("all", profile):
                            continue
                        bible_path = Path(directory) / f"{profile}.md"
                        bible_path.write_text(bible, encoding="utf-8")
                        print(f"Starting {case['id']} / {profile} / {repeat + 1}", flush=True)
                        try:
                            outcome = run_case(profile_config(config, bible_path), case, seed,
                                               Path(directory) / f"{repeat}-{case['id']}-{profile}.sqlite",
                                               history=case.get("history", ()),
                                               adapter_type=AuditedAdapter if profile == "audited" else capture_adapter)
                            outcome["indicators"] = indicators(case, outcome["reply"], outcome["read_ids"], ids)
                            turn[profile] = outcome
                        # Preserve failed arms as diagnostic evidence, without altering the runtime.
                        except Exception as error:  # noqa: BLE001
                            turn[profile] = {"error": str(error)}
                        print(json.dumps({"case": case["id"], "profile": profile, **turn[profile]}, ensure_ascii=True), flush=True)
        report["resources_released"] = True
    finally:
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"report": str(path), "review_required": True}), flush=True)
    return int(any("error" in turn.get(profile, {}) for turn in report["turns"] for profile in profiles))


if __name__ == "__main__":
    raise SystemExit(main())
