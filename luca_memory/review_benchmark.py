"""Synthetic review benchmarks; never open personal memory or call an LLM."""

import argparse
import hashlib
import json
import math
from pathlib import Path
import statistics
import tempfile
import time

from .config import load_config
from .store import MemoryStore
from .session import LucaSession


class SyntheticAdapter:
    """Deterministic prompt consumer: benchmark the Core, not inference latency."""

    def respond(self, text, context, history):
        self.context_hash = hashlib.sha256(context.encode("utf-8")).hexdigest()
        return "Synthetic response"


REFERENCE_ALIAS_SQL = """SELECT cells.* FROM cell_aliases
JOIN cells ON cells.id = cell_aliases.cell_id
LEFT JOIN edges ON edges.source_id = cells.id OR edges.target_id = cells.id
WHERE cell_aliases.alias = ? GROUP BY cells.id
ORDER BY COALESCE(MAX(edges.last_used_at),0) DESC,
COALESCE(SUM(edges.use_count),0) DESC, cells.id ASC LIMIT ?"""


def distribution(samples):
    ordered = sorted(samples)
    return {"median_ms": statistics.median(ordered),
            "p95_ms": ordered[math.ceil(len(ordered) * .95) - 1], "samples": len(ordered)}


def measure(call, repeats):
    for _ in range(2):
        call()
    samples = []
    for _ in range(repeats):
        start = time.perf_counter()
        call()
        samples.append((time.perf_counter() - start) * 1000)
    return distribution(samples)


def aliases(root, cells=500000, edges=100000, repeats=20):
    if cells < edges + 2 or edges < 1:
        raise ValueError("The fixture needs at least edges + 2 cells.")
    with tempfile.TemporaryDirectory(prefix="alias-review-", dir=root) as directory:
        with MemoryStore(Path(directory) / "synthetic.sqlite") as store:
            with store.transaction():
                store.connection.execute("""WITH RECURSIVE ids(n) AS
                    (VALUES(1) UNION ALL SELECT n+1 FROM ids WHERE n < ?)
                    INSERT INTO cells SELECT n, CAST('synthetic' AS BLOB), 1 FROM ids""", (cells,))
                store.connection.executemany("INSERT INTO edges(source_id,target_id) VALUES(1,?)", ((i,) for i in range(2, edges + 2)))
                store.add_alias("hub", 1)
                store.add_alias("hub", cells)
                store.touch_edge(1, 2, 10)
            reference = lambda: list(store.connection.execute(REFERENCE_ALIAS_SQL, ("hub", 8)))
            current = lambda: store.cells_by_alias("hub")
            if [r["id"] for r in reference()] != [cell.id for cell in current()]:
                raise RuntimeError("Alias ordering differs from the reference query.")
            result = {"kind": "aliases", "cells": cells, "hub_edges": edges,
                      "reference": measure(reference, repeats), "current": measure(current, repeats)}
            tick = 100
            def touch():
                nonlocal tick
                tick += 1
                store.touch_edge(1, 2, tick)
            store.connection.execute("BEGIN")
            try:
                result["touch_with_summary"] = measure(touch, max(100, repeats))
                # Disable only the disposable fixture's new usage triggers, then roll back.
                for name in ("trg_edges_ai_usage", "trg_edges_au_usage", "trg_edges_ad_usage"):
                    store.connection.execute(f"DROP TRIGGER IF EXISTS {name}")
                result["touch_without_summary"] = measure(touch, max(100, repeats))
            finally:
                store.connection.rollback()
            return result


def turns(root, device=1, repeats=5):
    questions = ["Parlami dei gatti", "E i cani?", "Parlami dei sommergibili", "E i gatti?", "Parlami dei cani"]
    results = []
    for size in (64000, 1650000):
        signatures = []
        for backend in ("host", "cuda"):
            with tempfile.TemporaryDirectory(prefix="turn-review-", dir=root) as directory:
                path = Path(directory)
                descriptions = [("gatti", "Gatti", "I gatti conducono sommergibili gialli."),
                                ("cani", "Cani", "I cani conducono sommergibili rossi."),
                                ("sommergibili", "Sommergibili", "Diverse famiglie di sommergibili: gatti e cani."),
                                ("gialli", "Gialli", "I sommergibili dei gatti sono gialli."),
                                ("rossi", "Rossi", "I sommergibili dei cani sono rossi.")]
                nodes = [{"slug": slug, "title": title, "keywords": [slug],
                          "content": prefix + " " + "x" * (size - len(prefix.encode("utf-8")) - 1)}
                         for slug, title, prefix in descriptions]
                seed = path / "synthetic.json"
                seed.write_text(json.dumps({"version": "review-1", "nodes": nodes,
                                           "edges": [["sommergibili", "gatti"], ["sommergibili", "cani"],
                                                     ["gatti", "gialli"], ["cani", "rossi"]]}), encoding="utf-8")
                adapter = SyntheticAdapter()
                session = LucaSession.open(path / "synthetic.sqlite", seed, adapter, vram_capacity=5,
                                           memory_settings={"memory_backend": backend, "gpu_device": device,
                                                            "vram_bytes": 16000000, "ram_bytes": 32000000})
                signature, samples = [], []
                try:
                    for _ in range(2):
                        for question in questions:
                            session.handle(question)
                    before = session.carousel.physical_state()
                    for _ in range(repeats):
                        for question in questions:
                            start = time.perf_counter()
                            reply = session.handle(question)
                            samples.append((time.perf_counter() - start) * 1000)
                            signature.append((reply.trace, adapter.context_hash))
                    after = session.carousel.physical_state()
                    results.append({"backend": backend, "node_content_bytes": size, **distribution(samples),
                                    "uploads": after.get("uploads", 0) - before.get("uploads", 0),
                                    "downloads": after.get("downloads", 0) - before.get("downloads", 0),
                                    "upload_bytes": after["upload_bytes"] - before["upload_bytes"],
                                    "download_bytes": after["download_bytes"] - before["download_bytes"]})
                    signatures.append(signature)
                finally:
                    session.close()
            if backend == "cuda" and signatures[0] != signatures[1]:
                raise RuntimeError("Host/CUDA recall traces or prompt contents differ.")
    return {"kind": "turns", "model": "deterministic synthetic adapter; no LLM call", "results": results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--cells", type=int, default=500000)
    parser.add_argument("--edges", type=int, default=100000)
    parser.add_argument("--repeats", type=int, default=20)
    parser.add_argument("--mode", choices=("aliases", "turns", "all"), default="aliases")
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error("repeats must be positive")
    config = load_config(args.config)
    root = Path(config["storage"]["database"]).parent
    root.mkdir(parents=True, exist_ok=True)
    if args.mode in {"aliases", "all"}:
        print(json.dumps(aliases(root, args.cells, args.edges, args.repeats)), flush=True)
    if args.mode in {"turns", "all"}:
        print(json.dumps(turns(root, config["runtime"]["gpu_device"], args.repeats)), flush=True)


if __name__ == "__main__":
    main()
