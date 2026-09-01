"""Run the initial Italian curriculum in an in-memory Luca store."""

from __future__ import annotations

import argparse
from pathlib import Path

from .curriculum import load_curriculum
from .language import ItalianSeedInterface
from .store import MemoryStore


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("question")
    args = parser.parse_args()
    seed = Path(__file__).parent.parent / "seed" / "italian_base_v0.json"
    with MemoryStore(":memory:") as store:
        curriculum = load_curriculum(store, seed)
        answer = ItalianSeedInterface(store, curriculum).answer(args.question)
    print(answer.text)
    print(f"trace: {list(answer.trace)}")


if __name__ == "__main__":
    main()
