"""Isolated model/policy matrix with measured GPU and physical-carousel evidence."""

import argparse
import copy
import csv
import hashlib
import json
import subprocess
import tempfile
import threading
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

from .autonomy_check import CASES
from .bible import read_bible
from .config import load_config
from .controlled_document_check import DOCUMENT, ROOT, indicators, run_case
from .live_memory_check import ObservedAdapter
from .node import load_node
from .seed_v1 import ensure_knowledge_seed, knowledge_seed_from_file
from .store import MemoryStore
from .tiers import SynapticCarousel


class MeasuredAdapter(ObservedAdapter):
    def _record_usage(self, model):
        super()._record_usage(model)
        if not hasattr(self, "request_observations"):
            self.request_observations = []
        self.request_observations.append(dict(self.last_prompt_report))


class RequiredReadAdapter(MeasuredAdapter):
    """Require one model-chosen read when addresses exist; never select its ID."""

    def navigate_memory(self, text, state, history):
        self.require_first_read = not state.get("read_nodes") and bool(
            state.get("global_candidates") or state.get("local_target_ids"))
        result = super().navigate_memory(text, state, history)
        self.observations[-1]["required_read_gate"] = self.require_first_read
        return result

    def _json_schema(self, name, schema):
        if name == "memory_navigation" and getattr(self, "require_first_read", False):
            schema = copy.deepcopy(schema)
            schema["anyOf"] = [item for item in schema["anyOf"]
                               if item["properties"]["action"].get("const") == "open"]
            if not schema["anyOf"]:
                raise ValueError("Required read has no legal address; experiment cannot continue.")
        return super()._json_schema(name, schema)


def gpu_snapshot():
    """Use the installed driver utility, without adding monitoring dependencies."""
    result = subprocess.run(
        ["nvidia-smi", "--query-gpu=index,name,memory.total,memory.used,utilization.gpu", "--format=csv,noheader,nounits"],
        capture_output=True, text=True, timeout=10, check=True)
    return [{"index": int(row[0]), "name": row[1].strip(), "total_mib": int(row[2]),
             "used_mib": int(row[3]), "utilization_percent": int(row[4])}
            for row in csv.reader(result.stdout.splitlines())]


def carousel_cycle(database, device):
    """Check device/host/disk round trips on real document nodes, independently of the LLM."""
    with MemoryStore(database) as store:
        ensure_knowledge_seed(store, DOCUMENT)
        carousel = SynapticCarousel(store, vram_capacity=1, ram_capacity=1,
                                     memory_backend="cuda", gpu_device=device)
        memory = carousel.vram.memory
        results = []
        try:
            for node_id in (1, 2, 3, 4, 5, 6, 7, 1):
                event = carousel.recall(node_id)
                expected = load_node(store, node_id).content.encode("utf-8")
                actual = carousel.vram.get(node_id).content.encode("utf-8")
                if actual != expected:
                    raise RuntimeError("Physical carousel changed document content.")
                results.append({"id": node_id, "sha256": hashlib.sha256(actual).hexdigest(),
                                "to_ram": event.evicted_to_ram, "to_ssd": event.evicted_to_ssd,
                                "physical_memory": carousel.physical_state()})
        finally:
            carousel.close()
        if memory._buffers or not memory.closed:
            raise RuntimeError("Physical carousel did not release its allocations.")
        return {"steps": results, "integrity_verified": True, "allocations_released": True}


def experiment_config(config, model, bible):
    selected = copy.deepcopy(config)
    active = selected["llm"]["active_runtime"]
    role = selected["runtime"].get("adapter_role", "orchestrator")
    selected["llm"]["runtimes"][active]["agents"][role]["model"] = model
    selected["runtime"].update({"bible": str(bible), "vram_capacity": 1, "ram_capacity": 1})
    return selected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--models", required=True, help="Comma-separated installed LM Studio model keys.")
    parser.add_argument("--case", default="all", help="Comma-separated case IDs, or all.")
    args = parser.parse_args()
    cases = json.loads(CASES.read_text(encoding="utf-8"))
    cases += json.loads((ROOT / "tests/fixtures/read_gate_extra_questions.json").read_text(encoding="utf-8"))
    wanted = set(args.case.split(","))
    if args.case != "all" and not wanted.issubset({case["id"] for case in cases}):
        parser.error("Unknown case ID.")
    cases = [case for case in cases if args.case == "all" or case["id"] in wanted]
    config = load_config(args.config)
    root = Path(config["storage"]["database"]).parent
    root.mkdir(parents=True, exist_ok=True)
    path = root / ("model-memory-check-" + datetime.now(UTC).strftime("%Y%m%d-%H%M%S-%f") + ".json")
    report = {"started_utc": datetime.now(UTC).isoformat(), "bible": read_bible(config["runtime"]["bible"]),
              "runtime": config["runtime"], "gpu_start": gpu_snapshot(), "gpu_samples": [],
              "turns": [], "review_required": True,
              "note": "One slot per GPU/host tier to exercise eviction. Conditional required read, no Core-selected ID. Alternating policy order, fresh sessions."}
    stopped = threading.Event()

    def monitor():
        while not stopped.wait(1):
            try:
                report["gpu_samples"].append({"utc": datetime.now(UTC).isoformat(), "gpus": gpu_snapshot()})
            except (OSError, subprocess.SubprocessError, ValueError) as error:
                report["gpu_samples"].append({"error": str(error)})

    thread = threading.Thread(target=monitor, daemon=True)
    thread.start()
    try:
        with tempfile.TemporaryDirectory(prefix="model-memory-check-", dir=root) as directory:
            bible = Path(directory) / "bible.md"
            bible.write_text(report["bible"], encoding="utf-8")
            report["carousel_cycle"] = carousel_cycle(Path(directory) / "cycle.sqlite", config["runtime"]["gpu_device"])
            for index, case in enumerate(cases):
                seed = ROOT / "seed" / case["seed"]
                ids = knowledge_seed_from_file(seed).ids
                policies = (("free", MeasuredAdapter), ("required", RequiredReadAdapter))
                if index % 2:
                    policies = tuple(reversed(policies))
                for model in args.models.split(","):
                    selected = experiment_config(config, model, bible)
                    for policy, adapter in policies:
                        turn = {"case": case, "model": model, "policy": policy,
                                "seed_sha256": hashlib.sha256(seed.read_bytes()).hexdigest()}
                        report["turns"].append(turn)
                        print(f"Starting {model} / {case['id']} / {policy}", flush=True)
                        started = perf_counter()
                        try:
                            outcome = run_case(selected, case, seed, Path(directory) / f"turn-{len(report['turns'])}.sqlite",
                                               history=case.get("history", ()), adapter_type=adapter)
                            outcome["indicators"] = indicators(case, outcome["reply"], outcome["read_ids"], ids)
                            requests = outcome["requests"]
                            outcome["cost"] = {"calls": len(requests), **{key: sum(item.get("server_" + key, 0) for item in requests)
                                               for key in ("prompt_tokens", "completion_tokens", "total_tokens")}}
                            turn["outcome"] = outcome
                        # Keep model/provider failures distinct from semantic failures.
                        except Exception as error:  # noqa: BLE001
                            turn["error"] = str(error)
                        turn["wall_seconds_including_setup"] = round(perf_counter() - started, 3)
                        outcome = turn.get("outcome", {})
                        print(json.dumps({"case": case["id"], "model": model, "policy": policy,
                                          "read_ids": outcome.get("read_ids"), "reply": outcome.get("reply"),
                                          "seconds": outcome.get("seconds"), "cost": outcome.get("cost"),
                                          "error": turn.get("error")}, ensure_ascii=True), flush=True)
        report["resources_released"] = True
    finally:
        stopped.set()
        thread.join(timeout=15)
        report["gpu_end"] = gpu_snapshot()
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"report": str(path), "review_required": True}), flush=True)
    return int(any("error" in turn for turn in report["turns"]))


if __name__ == "__main__":
    raise SystemExit(main())
