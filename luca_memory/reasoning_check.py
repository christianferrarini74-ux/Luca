"""Replay memory/general-knowledge dialogues against disposable real-model memory."""

import argparse
import hashlib
import json
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from .bible import read_bible
from .config import load_config
from .live_memory_check import ObservedAdapter
from .session import LucaSession

CASES = (
    ("greeting", "buonasera", None),
    ("general_rain", "Sai dirmi come si genera la pioggia?", "general"),
    ("special_rain", "hai mai sentito parlare della pioggia di zucchero filato?", "rain"),
    ("rain_details", "dimmi i dettagli di questo fenomeno", "rain"),
    ("mountain", "ma avviene in montagna?", "mountain"),
    ("donkeys", "sai qualcosa degli asini che volano?", "donkeys"),
    ("connection", "secondo te c'entra qualcosa con la pioggia di zucchero filato?", "connection"),
    ("towers", "ti piacciono i campanili che si trovano in montagna?", None),
    ("nests", "e i nidi di paglia dorata che si trovano sui campanili?", "nests"),
    ("exploration", "quindi riassumendo, in aria succedono diverse cose straordinarie: pioggia di zucchero filato, gli asini volano e costruiscono nidi di paglia sui campanili, c'è dell'altro?", "exploration"),
)

INTEGRATION_CASES = (
    ("diet_before", "Cosa mangiano gli asini?", "diet"),
    ("flying", "Parlami degli asini che volano", "donkeys"),
    ("diet_after", "cosa mangiano gli asini?", "diet"),
    ("general_rain", "Come si forma la pioggia?", "general"),
    ("special_rain", "Hai sentito parlare della pioggia di zucchero filato?", "rain"),
    ("details", "approfondisci e spiegami meglio", "rain"),
    ("connection", "quale è il collegamento tra Asini che volano e pioggia di zucchero filato?", "connection"),
    ("diet_return", "E cosa mangiano gli asini, in generale?", "diet"),
)


def assess(kind, text, readings):
    """Lexical evidence checks are not a substitute for reviewing the answers."""
    text = text.lower()
    if kind is None:
        return None
    if kind == "diet":
        return any(word in text for word in ("erbivor", "erba", "fieno")) and not any(
            phrase in text for phrase in ("non specificano", "non specifica", "non posso sapere"))
    if kind == "general":
        return "evapor" in text and "condens" in text and "zucchero" not in text
    if kind == "rain":
        return 2 in readings and "zucchero" in text and "montagn" in text and "macchinar" not in text
    if kind == "mountain":
        return 2 in readings and "montagn" in text and "artificiale" not in text
    if kind == "donkeys":
        return bool({2, 3}.intersection(readings)) and "asin" in text and "vol" in text
    if kind == "connection":
        return 2 in readings and "zucchero" in text and "asin" in text and "gravit" in text
    if kind == "nests":
        return 4 in readings and "paglia" in text and "campanil" in text
    return 5 in readings and "formaggio" in text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--scenario", choices=("weather", "integration"), default="weather")
    args = parser.parse_args()
    config = load_config(args.config)
    cases = CASES if args.scenario == "weather" else INTEGRATION_CASES
    bible = read_bible(config["runtime"]["bible"])
    adapter = ObservedAdapter.from_config(config)
    adapter.observations = []
    root = Path(config["storage"]["database"]).parent
    root.mkdir(parents=True, exist_ok=True)
    path = root / ("reasoning-live-" + datetime.now().strftime("%Y%m%d-%H%M%S") + ".json")
    report = {"started_utc": datetime.now(UTC).isoformat(), "model": adapter.model,
              "scenario": args.scenario, "bible_snapshot": bible,
              "bible_sha256": hashlib.sha256(bible.encode("utf-8")).hexdigest(),
              "note": "Synthetic seed; lexical and actual-reading checks, not factual certification.", "turns": []}
    try:
        with tempfile.TemporaryDirectory(prefix="reasoning-check-", dir=root) as directory:
            session = LucaSession.open(Path(directory) / "synthetic.sqlite", config["storage"]["seed"], adapter,
                planner_mode="llm", memory_settings=config["runtime"],
                vram_capacity=int(config["runtime"].get("vram_capacity", 5)),
                ram_capacity=int(config["runtime"].get("ram_capacity", 12)))
            try:
                for name, question, kind in cases:
                    try:
                        reply = session.handle(question)
                        readings = list(session.navigator.workspace.nodes)
                        turn = {"name": name, "question": question, "reply": reply.text,
                            "read_ids": readings, "trace": list(session.navigator.trace),
                            "navigation_status": session.navigator.status,
                            "direct_answer": session.navigator.response is not None,
                            "request": dict(adapter.last_prompt_report),
                            "passed": assess(kind, reply.text, readings)}
                    # Record diagnostic failures while allowing cleanup and the remaining checks.
                    except Exception as error:  # noqa: BLE001
                        turn = {"name": name, "question": question, "error": str(error), "passed": False}
                    report["turns"].append(turn)
                    print(json.dumps(turn, ensure_ascii=True), flush=True)
            finally:
                session.close()
                report["resources_released"] = True
    finally:
        checked = [turn for turn in report["turns"] if turn["passed"] is not None]
        report["passed"] = len(checked) == sum(kind is not None for _, _, kind in cases) and all(
            turn["passed"] for turn in checked) and report.get("resources_released", False)
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"report": str(path), "passed": report["passed"]}), flush=True)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
