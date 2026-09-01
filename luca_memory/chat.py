"""Run a persistent light-conversation demonstration of Luca."""

from __future__ import annotations

import argparse
from pathlib import Path

from .session import LucaSession


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=Path("luca.sqlite"))
    args = parser.parse_args()
    seed = Path(__file__).parent.parent / "seed" / "italian_base_v0.json"
    session = LucaSession.open(args.database, seed)
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
