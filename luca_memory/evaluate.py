"""Evaluate the seed curriculum with questions kept outside the lessons."""

from __future__ import annotations

import json
from pathlib import Path

from .curriculum import load_curriculum
from .language import ItalianSeedInterface
from .store import MemoryStore


def main() -> None:
    root = Path(__file__).parent.parent
    checks = json.loads((root / "seed" / "italian_base_v0_checks.json").read_text(encoding="utf-8"))
    with MemoryStore(":memory:") as store:
        curriculum = load_curriculum(store, root / "seed" / "italian_base_v0.json")
        interface = ItalianSeedInterface(store, curriculum)
        failures = 0
        for case in checks["cases"]:
            answer = interface.answer(case["question"])
            passed = answer.text == case["expected"]
            failures += not passed
            status = "PASS" if passed else "FAIL"
            print(f"{status}: {case['question']} -> {answer.text}")
    if failures:
        raise SystemExit(f"{failures} curriculum checks failed")


if __name__ == "__main__":
    main()
