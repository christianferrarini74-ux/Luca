"""Keep current guidance separate from dated evidence and validate repository links."""

import re
import unittest
from pathlib import Path
from urllib.parse import unquote, urlsplit

import yaml

ROOT = Path(__file__).resolve().parents[1]
CURRENT = {
    "docs/README.md", "docs/it/INDICE.md", "docs/bible.en.md",
    "docs/configuration.md", "docs/it/configuration.md",
    "docs/gui-runtime.md", "docs/it/gui-runtime.md",
    "docs/llm-connector.md", "docs/it/llm-connector.md",
    "docs/memory-integration-contract.md", "docs/it/fase-1-sinapsi/28-contratto-utilizzo-memoria.md",
    "docs/category-routing-planner.md", "docs/it/fase-1-sinapsi/32-classificazione-e-pianificazione-archi.md",
    "docs/documentation-audit.md", "docs/it/fase-1-sinapsi/33-revisione-documentazione.md",
}
FIXTURES = {"docs/iris17-manual.en.md", "docs/it/esperimenti/iris17-manuale.md"}


def local_links(path):
    """Inspect Markdown destinations outside fenced examples, without network access."""
    fence = None
    visible = []
    for line in path.read_text(encoding="utf-8").splitlines():
        marker = re.match(r"\s*(`{3,}|~{3,})", line)
        if marker:
            char = marker[1][0]
            if fence is None:
                fence = char
            elif fence == char:
                fence = None
            continue
        if fence is None:
            visible.append(line)
    for destination in re.findall(r"\[[^\]\n]+\]\(([^)\n]+)\)", "\n".join(visible)):
        destination = destination.split(' "', 1)[0].strip("<>")
        parsed = urlsplit(destination)
        if parsed.scheme or parsed.netloc or not parsed.path:
            continue
        yield (path.parent / unquote(parsed.path)).resolve()


class DocumentationContractTests(unittest.TestCase):
    def test_all_repository_markdown_links_resolve(self):
        paths = [ROOT / "README.md", ROOT / "README.it.md", *sorted((ROOT / "docs").rglob("*.md"))]
        broken = [(str(path.relative_to(ROOT)), str(target)) for path in paths
                  for target in local_links(path) if not target.exists()]
        self.assertEqual(broken, [])

    def test_both_catalogs_cover_every_document(self):
        documents = {path.resolve() for path in (ROOT / "docs").rglob("*.md")}
        for name in ("docs/README.md", "docs/it/INDICE.md"):
            catalog = ROOT / name
            missing = documents - set(local_links(catalog)) - {catalog.resolve()}
            self.assertEqual(sorted(str(path.relative_to(ROOT)) for path in missing), [], name)

    def test_default_model_and_database_match_current_guidance(self):
        config = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
        runtime = config["llm"]["runtimes"][config["llm"]["active_runtime"]]
        model = runtime["agents"][config["runtime"]["adapter_role"]]["model"]
        for name in ("README.md", "README.it.md", "docs/configuration.md", "docs/it/configuration.md"):
            text = (ROOT / name).read_text(encoding="utf-8")
            self.assertIn(model, text, name)
            self.assertIn(config["storage"]["database"], text, name)
            self.assertIn("run_luca.py", text, name)

    def test_dated_documents_have_explicit_status(self):
        for path in (ROOT / "docs").rglob("*.md"):
            name = path.relative_to(ROOT).as_posix()
            if name in CURRENT | FIXTURES:
                continue
            text = path.read_text(encoding="utf-8")
            self.assertTrue(any(marker in text for marker in (
                "**Historical record", "**Documento storico", "Archived on 2026-10-22", "Archivio del 2026-10-22")), name)

    def test_readmes_state_current_scope_without_obsolete_demo_claims(self):
        for name in ("README.md", "README.it.md"):
            text = (ROOT / name).read_text(encoding="utf-8")
            self.assertIn("PyYAML", text)
            self.assertIn("Esci", text)
            self.assertIn("52→45", text)
            self.assertNotIn("google/gemma-3-1b", text)
            self.assertNotIn("It contains no LLM", text)
            self.assertNotIn("no third-party dependency is required", text)
