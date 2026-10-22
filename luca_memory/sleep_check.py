"""Opt-in real-worker sleep experiment on disposable controlled graphs."""

import argparse
import copy
import hashlib
import json
import tempfile
import threading
import time
from dataclasses import asdict, replace
from datetime import UTC, datetime
from pathlib import Path

from .adapters import LMStudioAdapter
from .config import load_config
from .maintenance import IdleMaintenance, MemoryMaintenance
from .sleep_fixture import graph_snapshot, populate, verify_regrouping
from .store import MemoryStore
from .synaptic import SynapticMemory
from .synaptic_settings import SynapticSettings


class SleepAdapter(LMStudioAdapter):
    """Record the actual maintenance request without injecting evaluation categories."""

    def _request(self, operation, question, data, history=(), **kwargs):
        messages, report = super()._request(operation, question, data, history, **kwargs)
        if operation == "group":
            self.inputs.append({"data": copy.deepcopy(data), "budget": report,
                                "instruction_sha256": hashlib.sha256(messages[0]["content"].encode()).hexdigest()})
        return messages, report

    def propose_groups(self, directory, settings):
        started = time.perf_counter()
        try:
            groups = super().propose_groups(directory, settings)
            self.proposals.append({"groups": groups, "seconds": round(time.perf_counter() - started, 3)})
            return groups
        finally:
            # The worker still validates and applies after this signal; close() joins it.
            self.finished.set()


def run_worker(memory, settings, adapter, *, timeout):
    """Use the actual polling worker and real elapsed inactivity, not direct apply()."""
    maintenance = MemoryMaintenance(memory, settings)
    worker = IdleMaintenance(maintenance, adapter)
    started = time.perf_counter()
    deadline = time.monotonic() + timeout
    worker.start()
    try:
        if not adapter.finished.wait(timeout):
            raise TimeoutError("Sleep proposal exceeded the diagnostic wait budget.")
        # Proposal completion is not commit completion: do not cancel the very plan being tested.
        while worker.last_operation is None and worker.last_error is None:
            if time.monotonic() >= deadline:
                raise TimeoutError("Sleep application exceeded the diagnostic wait budget.")
            time.sleep(0.01)
    finally:
        worker.close()
    return {"operation_id": worker.last_operation, "error": worker.last_error,
            "worker_stopped": not worker._thread.is_alive(),
            "seconds": round(time.perf_counter() - started, 3)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--model", help="Experimental override; config.yaml remains unchanged.")
    parser.add_argument("--repeat", type=int, default=2)
    parser.add_argument("--idle-seconds", type=int, default=1, help="Real idle wait in this diagnostic only.")
    args = parser.parse_args()
    if args.repeat < 1 or args.idle_seconds < 1:
        parser.error("Repeat and idle seconds must be positive.")
    config = copy.deepcopy(load_config(args.config))
    role = config["runtime"].get("adapter_role", "orchestrator")
    if args.model:
        config["llm"]["runtimes"][config["llm"]["active_runtime"]]["agents"][role]["model"] = args.model
    adapter = SleepAdapter.from_config(config, assignment=role)
    settings = replace(SynapticSettings.from_config(config["runtime"]), idle_seconds=args.idle_seconds,
                       sleep_poll_seconds=1, automatic_sleep=True)
    root = Path(config["storage"]["database"]).parent
    root.mkdir(parents=True, exist_ok=True)
    path = root / ("sleep-check-" + datetime.now(UTC).strftime("%Y%m%d-%H%M%S-%f") + ".json")
    report = {"started_utc": datetime.now(UTC).isoformat(), "model": adapter.model, "settings": asdict(settings),
              "instruction_sha256": hashlib.sha256(Path(adapter.bible_path).read_bytes()).hexdigest(),
              "runs": [], "note": "Real worker, shortened real idle timers, synthetic title-labelled topics; no CUDA claim. "
              "passed and exit status indicate structural checks only; thematically_pure is a separate diagnostic, not title validation."}
    try:
        with tempfile.TemporaryDirectory(prefix="sleep-check-", dir=root) as temporary:
            for repeat in range(1, args.repeat + 1):
                database = Path(temporary) / f"run-{repeat}.sqlite"
                adapter.inputs, adapter.proposals, adapter.finished = [], [], threading.Event()
                run = {"repeat": repeat}
                report["runs"].append(run)
                print(f"Starting sleep worker / {adapter.model} / {repeat}", flush=True)
                try:
                    with MemoryStore(database) as store:
                        memory = SynapticMemory(store)
                        fixture = populate(memory, settings)
                        run["candidates_before"] = MemoryMaintenance(memory, settings).candidates()
                        run.update(run_worker(memory, settings, adapter, timeout=adapter.timeout_seconds + 30))
                        if run["operation_id"] is not None:
                            run.update(verify_regrouping(memory, settings, fixture, run["operation_id"]))
                    # Reopen the committed graph before undoing, not just the original connection.
                    if run.get("operation_id") is not None:
                        with MemoryStore(database) as store:
                            memory = SynapticMemory(store)
                            run["restart_checks"] = verify_regrouping(memory, settings, fixture, run["operation_id"])["checks"]
                            MemoryMaintenance(memory, settings).restore(run["operation_id"], confirmed=True)
                            run["exact_restore_after_restart"] = graph_snapshot(memory) == fixture["before"]
                    run["passed"] = (all(run.get("checks", {}).values()) and bool(run.get("checks"))
                                     and all(run.get("restart_checks", {}).values())
                                     and run.get("exact_restore_after_restart") is True and run["worker_stopped"])
                except Exception as error:  # noqa: BLE001 - Preserve diagnostic evidence and clean temporary resources.
                    run.update(passed=False, exception_type=type(error).__name__, exception=str(error))
                run.update(inputs=adapter.inputs, proposals=adapter.proposals)
                print(json.dumps({key: value for key, value in run.items() if key not in ("inputs", "proposals")}, ensure_ascii=False), flush=True)
        report["temporary_databases_removed"] = True
    finally:
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"report": str(path)}), flush=True)
    return int(any(not run["passed"] for run in report["runs"]))


if __name__ == "__main__":
    raise SystemExit(main())
