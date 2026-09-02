"""Run a persistent light-conversation demonstration of Luca."""

from __future__ import annotations

import argparse
from pathlib import Path

from .adapters import LMStudioAdapter
from .session import LucaSession


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=Path("luca.sqlite"))
    parser.add_argument("--adapter", choices=("rules", "gemma"), default="rules")
    parser.add_argument("--lm-studio-url", default=LMStudioAdapter.DEFAULT_BASE_URL)
    parser.add_argument("--lm-studio-model", default=LMStudioAdapter.DEFAULT_MODEL)
    args = parser.parse_args()
    seed = Path(__file__).parent.parent / "seed" / "italian_base_v0.json"
    adapter = (
        LMStudioAdapter(args.lm_studio_url, args.lm_studio_model)
        if args.adapter == "gemma"
        else None
    )
    session = LucaSession.open(args.database, seed, adapter=adapter)
    print("Luca è pronto. Scrivi 'esci' per terminare.")
    try:
        while True:
            text = input("Tu: ").strip()
            if text.lower() in {"esci", "exit", "quit"}:
                break
            reply = session.handle(text)
            print(f"Luca: {reply.text}")
            if reply.trace:
                print(f"Traccia: {list(reply.trace)}")
    finally:
        session.close()


if __name__ == "__main__":
    main()
