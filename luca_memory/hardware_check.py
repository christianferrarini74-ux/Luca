"""Run a synthetic disk/RAM/GPU carousel check without opening personal memory."""

import argparse
import hashlib
import json
from pathlib import Path
import tempfile

from .config import load_config
from .node import KnowledgeNode, save_node, load_node
from .store import MemoryStore
from .tiers import SynapticCarousel


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--device", type=int)
    args = parser.parse_args()
    config = load_config(args.config)
    root = Path(config["storage"]["database"]).parent
    root.mkdir(parents=True, exist_ok=True)
    device = config["runtime"]["gpu_device"] if args.device is None else args.device
    with tempfile.TemporaryDirectory(prefix="hardware-check-", dir=root) as directory:
        with MemoryStore(Path(directory) / "synthetic.sqlite") as store:
            chapter = "Capitolo sintetico: nero → carbone, integrità 🧠.\n" * 30000
            with store.transaction():
                for node_id, content in enumerate(("Un piccolo nodo.", chapter, "Terzo nodo.", "Quarto nodo."), 1):
                    save_node(store, KnowledgeNode(node_id, f"synthetic{node_id}", f"Synthetic {node_id}", content, created_at=1))
            carousel = SynapticCarousel(store, vram_capacity=1, ram_capacity=1, memory_backend="cuda",
                                         gpu_device=device, vram_bytes=4_000_000, ram_bytes=4_000_000)
            memory = carousel.vram.memory
            try:
                for node_id in (1, 2, 3, 4, 2):
                    event = carousel.recall(node_id)
                    expected = load_node(store, node_id).content.encode("utf-8")
                    actual = carousel.vram.get(node_id).content.encode("utf-8")
                    if actual != expected:
                        raise RuntimeError("Synthetic payload integrity failure.")
                    print(json.dumps({"node": node_id, "content_bytes": len(actual),
                                      "sha256": hashlib.sha256(actual).hexdigest(),
                                      "demoted_to_ram": event.evicted_to_ram, "evicted_to_disk_only": event.evicted_to_ssd,
                                      "physical_memory": carousel.physical_state()}))
            finally:
                carousel.close()
            if memory._buffers or not memory.closed:
                raise RuntimeError("Device resources were not fully released.")
            print(json.dumps({"result": "passed", "released_allocations": True, "personal_database_opened": False}))


if __name__ == "__main__":
    main()
