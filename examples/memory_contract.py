"""Minimal external producer: populate a NEW database through Luca's Core contract."""

import argparse
from dataclasses import replace
from pathlib import Path

from luca_memory.node import KnowledgeNode, KnowledgeSection, load_node
from luca_memory.seed_v1 import ensure_knowledge_seed
from luca_memory.store import MemoryStore
from luca_memory.synaptic import SynapticMemory


def populate_example(store):
    """Create a family and an external reference without resetting an existing library."""
    with store.transaction():
        if store.has_cells():
            raise ValueError("This example only accepts an empty database.")
        # Keep the app's empty-library seed identity without importing a document.
        seed = Path(__file__).resolve().parents[1] / "seed/library_empty_v1.json"
        ensure_knowledge_seed(store, seed)
        memory = SynapticMemory(store)
        ids = {}
        for key, title, body in (
            ("root", "Module Atlas: index", "Source: controlled example, revision 1. Parts: installation and reference."),
            ("installation", "Atlas: installation", "Source: controlled example, revision 1, section 1. Install Atlas in the chosen environment."),
            ("reference", "Atlas: reference", "Source: controlled example, revision 1, section 2. The entry function is atlas.start()."),
            ("environment", "Execution environment", "Source: controlled example, revision 1. Record the selected environment here."),
        ):
            identity = store.next_cell_id()  # Allocate and insert while holding the same transaction lock.
            ids[key] = identity
            memory.update_node(KnowledgeNode(identity, f"example_{key}", title, body,
                                            keywords=("Atlas", key)))
        memory.attach_part(ids["root"], ids["installation"])
        memory.attach_part(ids["root"], ids["reference"])
        memory.connect(ids["installation"], ids["environment"])  # Canonical external route: root -> environment.
        old = load_node(store, ids["reference"])
        memory.update_node(replace(old, sections=(KnowledgeSection("entry", "Entry function", "atlas.start()"),)),
                           expected_revision=store.revision)
        return ids


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, required=True, help="New file in an existing directory; never your personal DB.")
    args = parser.parse_args()
    if args.database.exists() or not args.database.parent.is_dir():
        parser.error("Choose a nonexistent database file in an existing directory.")
    with MemoryStore(args.database) as store:
        print(populate_example(store))


if __name__ == "__main__":
    raise SystemExit(main())
