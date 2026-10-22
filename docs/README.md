# Luca documentation

[Italiano](it/INDICE.md) · [Project README](../README.md)

## Current state — 2026-10-22

Luca is an external synaptic-memory system for LLMs. It manages knowledge nodes,
directed arcs, explicit families, indexes, physical tier storage and atomic
mutations. External producers create/partition content. Chat and dashboard are
test consumers. PDF import, library creation and Cesare integration are out of scope.

During sleep the LLM classifies the complete directory; the Core calculates
routing groups and reaches the exact target when compatible single-level
capacity suffices. General semantic classification correctness is not guaranteed.
The distributed 50/45 thresholds are configurable, not mandatory code constants.

## Read these current guides first

| Guide | English | Italiano |
| --- | --- | --- |
| Producer/consumer contract | [Contract](memory-integration-contract.md) | [Contratto](it/fase-1-sinapsi/28-contratto-utilizzo-memoria.md) |
| Classification and routing | [Algorithm and evidence](category-routing-planner.md) | [Pianificatore](it/fase-1-sinapsi/32-classificazione-e-pianificazione-archi.md) |
| Startup/configuration | [Configuration](configuration.md) | [Configurazione](it/configuration.md) |
| Frontend/lifecycle | [Dashboard](gui-runtime.md) | [Cruscotto](it/gui-runtime.md) |
| LLM boundary | [Connector](llm-connector.md) | [Connettore](it/llm-connector.md) |
| Documentation review | [Audit](documentation-audit.md) | [Audit](it/fase-1-sinapsi/33-revisione-documentazione.md) |
| Model instructions | [Reference translation](bible.en.md) | [Runtime bible](../bible.md) |

## Reading historical records

Milestones are dated evidence, not a current missing-feature list or committed
roadmap. Their test counts, models, policies and commands describe their own
stage. Status notices point to the current contract without erasing failures,
measurements or superseded designs. The first six phase originals are Italian
only; current operating guides are bilingual. The
[previous Italian index](it/INDICE-storico-20261022.md), earlier READMEs and old
operating guides are retained as archives.

The bible and experimental prompt data are not all operating guides; the English
translation is not automatically loaded. IRIS-17 manuals are fictional controlled
fixtures, not personal knowledge or real-hardware instructions.

## Complete catalog

Every Markdown file under `docs/`, including snapshots, is listed here.
“Current” identifies live guidance, “Historical” a dated milestone/reference,
and “Fixture” controlled source material.

| Document | Status | Language |
| --- | --- | --- |
| [README.md](README.md) | Current | EN |
| [architecture.md](architecture.md) | Historical | EN |
| [bible.en.md](bible.en.md) | Current | EN |
| [bounded-synaptic-memory-design.md](bounded-synaptic-memory-design.md) | Historical | EN |
| [category-routing-planner.md](category-routing-planner.md) | Current | EN |
| [code-maintenance-review.md](code-maintenance-review.md) | Historical | EN |
| [configuration.md](configuration.md) | Current | EN |
| [controlled-document-experiment.md](controlled-document-experiment.md) | Historical | EN |
| [curriculum.md](curriculum.md) | Historical | EN |
| [dependency-audit.md](dependency-audit.md) | Historical | EN |
| [documentation-audit.md](documentation-audit.md) | Current | EN |
| [experiments.md](experiments.md) | Historical | EN |
| [github-actions-checks.md](github-actions-checks.md) | Historical | EN |
| [goal-first-recovery.md](goal-first-recovery.md) | Historical | EN |
| [gui-runtime.md](gui-runtime.md) | Current | EN |
| [history/configuration.en.md](history/configuration.en.md) | Historical | EN |
| [history/configuration.it.md](history/configuration.it.md) | Historical | IT |
| [history/gui-runtime.en.md](history/gui-runtime.en.md) | Historical | EN |
| [history/gui-runtime.it.md](history/gui-runtime.it.md) | Historical | IT |
| [history/llm-connector.en.md](history/llm-connector.en.md) | Historical | EN |
| [history/llm-connector.it.md](history/llm-connector.it.md) | Historical | IT |
| [history/readme.en.md](history/readme.en.md) | Historical | EN |
| [history/readme.it.md](history/readme.it.md) | Historical | IT |
| [integrated-knowledge-bible.md](integrated-knowledge-bible.md) | Historical | EN |
| [iris17-manual.en.md](iris17-manual.en.md) | Fixture | EN |
| [it/INDICE-storico-20261022.md](it/INDICE-storico-20261022.md) | Historical | IT |
| [it/INDICE.md](it/INDICE.md) | Current | IT |
| [it/architecture.md](it/architecture.md) | Historical | IT |
| [it/configuration.md](it/configuration.md) | Current | IT |
| [it/curriculum.md](it/curriculum.md) | Historical | IT |
| [it/dependency-audit.md](it/dependency-audit.md) | Historical | IT |
| [it/esperimenti/iris17-manuale.md](it/esperimenti/iris17-manuale.md) | Fixture | IT |
| [it/experiments.md](it/experiments.md) | Historical | IT |
| [it/fase-1-sinapsi/01-svolta-sinaptica.md](it/fase-1-sinapsi/01-svolta-sinaptica.md) | Historical | IT |
| [it/fase-1-sinapsi/02-roadmap-codice-fase-1.md](it/fase-1-sinapsi/02-roadmap-codice-fase-1.md) | Historical | IT |
| [it/fase-1-sinapsi/03-esperimento-favole-contrasto.md](it/fase-1-sinapsi/03-esperimento-favole-contrasto.md) | Historical | IT |
| [it/fase-1-sinapsi/04-unificazione-gui-cesare.md](it/fase-1-sinapsi/04-unificazione-gui-cesare.md) | Historical | IT |
| [it/fase-1-sinapsi/05-bibbia-gating-sinaptico-2b.md](it/fase-1-sinapsi/05-bibbia-gating-sinaptico-2b.md) | Historical | IT |
| [it/fase-1-sinapsi/06-indicizzazione-famiglie-archi-multipli.md](it/fase-1-sinapsi/06-indicizzazione-famiglie-archi-multipli.md) | Historical | IT |
| [it/fase-1-sinapsi/07-completamento-runtime.md](it/fase-1-sinapsi/07-completamento-runtime.md) | Historical | IT |
| [it/fase-1-sinapsi/08-roadmap-utilizzo-memoria.md](it/fase-1-sinapsi/08-roadmap-utilizzo-memoria.md) | Historical | IT |
| [it/fase-1-sinapsi/09-memoria-fisica.md](it/fase-1-sinapsi/09-memoria-fisica.md) | Historical | IT |
| [it/fase-1-sinapsi/10-verifica-claude.md](it/fase-1-sinapsi/10-verifica-claude.md) | Historical | IT |
| [it/fase-1-sinapsi/11-memoria-sinaptica-riorganizzabile.md](it/fase-1-sinapsi/11-memoria-sinaptica-riorganizzabile.md) | Historical | IT |
| [it/fase-1-sinapsi/12-implementazione-memoria-navigabile.md](it/fase-1-sinapsi/12-implementazione-memoria-navigabile.md) | Historical | IT |
| [it/fase-1-sinapsi/13-verifica-live-lmstudio.md](it/fase-1-sinapsi/13-verifica-live-lmstudio.md) | Historical | IT |
| [it/fase-1-sinapsi/14-ingresso-memoria-e-dialogo.md](it/fase-1-sinapsi/14-ingresso-memoria-e-dialogo.md) | Historical | IT |
| [it/fase-1-sinapsi/15-contesto-in-token.md](it/fase-1-sinapsi/15-contesto-in-token.md) | Historical | IT |
| [it/fase-1-sinapsi/16-ragionamento-libero.md](it/fase-1-sinapsi/16-ragionamento-libero.md) | Historical | IT |
| [it/fase-1-sinapsi/17-bibbia-conoscenza-integrata.md](it/fase-1-sinapsi/17-bibbia-conoscenza-integrata.md) | Historical | IT |
| [it/fase-1-sinapsi/18-mappa-grafica-memoria.md](it/fase-1-sinapsi/18-mappa-grafica-memoria.md) | Historical | IT |
| [it/fase-1-sinapsi/19-correzione-centratura-mappa.md](it/fase-1-sinapsi/19-correzione-centratura-mappa.md) | Historical | IT |
| [it/fase-1-sinapsi/20-revisione-codice-e-commenti.md](it/fase-1-sinapsi/20-revisione-codice-e-commenti.md) | Historical | IT |
| [it/fase-1-sinapsi/21-controlli-github-actions.md](it/fase-1-sinapsi/21-controlli-github-actions.md) | Historical | IT |
| [it/fase-1-sinapsi/22-avvio-biblioteca-reale.md](it/fase-1-sinapsi/22-avvio-biblioteca-reale.md) | Historical | IT |
| [it/fase-1-sinapsi/23-esperimento-documento-controllato.md](it/fase-1-sinapsi/23-esperimento-documento-controllato.md) | Historical | IT |
| [it/fase-1-sinapsi/24-autonomia-e-attualita-memoria.md](it/fase-1-sinapsi/24-autonomia-e-attualita-memoria.md) | Historical | IT |
| [it/fase-1-sinapsi/25-modello-lettura-obbligatoria-multi-gpu.md](it/fase-1-sinapsi/25-modello-lettura-obbligatoria-multi-gpu.md) | Historical | IT |
| [it/fase-1-sinapsi/26-intervista-arresto-lettura.md](it/fase-1-sinapsi/26-intervista-arresto-lettura.md) | Historical | IT |
| [it/fase-1-sinapsi/27-ripristino-obiettivo-esplicito.md](it/fase-1-sinapsi/27-ripristino-obiettivo-esplicito.md) | Historical | IT |
| [it/fase-1-sinapsi/28-contratto-utilizzo-memoria.md](it/fase-1-sinapsi/28-contratto-utilizzo-memoria.md) | Current | IT |
| [it/fase-1-sinapsi/29-verifica-riorganizzazione-sonno.md](it/fase-1-sinapsi/29-verifica-riorganizzazione-sonno.md) | Historical | IT |
| [it/fase-1-sinapsi/30-arresto-riorganizzazione-obiettivo.md](it/fase-1-sinapsi/30-arresto-riorganizzazione-obiettivo.md) | Historical | IT |
| [it/fase-1-sinapsi/31-confronto-sonno-gemma26.md](it/fase-1-sinapsi/31-confronto-sonno-gemma26.md) | Historical | IT |
| [it/fase-1-sinapsi/32-classificazione-e-pianificazione-archi.md](it/fase-1-sinapsi/32-classificazione-e-pianificazione-archi.md) | Current | IT |
| [it/fase-1-sinapsi/33-revisione-documentazione.md](it/fase-1-sinapsi/33-revisione-documentazione.md) | Current | IT |
| [it/gui-runtime.md](it/gui-runtime.md) | Current | IT |
| [it/language-adapters.md](it/language-adapters.md) | Historical | IT |
| [it/llm-connector.md](it/llm-connector.md) | Current | IT |
| [it/memory-search.md](it/memory-search.md) | Historical | IT |
| [it/roadmap.md](it/roadmap.md) | Historical | IT |
| [it/vision.md](it/vision.md) | Historical | IT |
| [language-adapters.md](language-adapters.md) | Historical | EN |
| [llm-connector.md](llm-connector.md) | Current | EN |
| [maintenance-target-stop.md](maintenance-target-stop.md) | Historical | EN |
| [memory-autonomy-investigation.md](memory-autonomy-investigation.md) | Historical | EN |
| [memory-development-roadmap.md](memory-development-roadmap.md) | Historical | EN |
| [memory-entry-cues.md](memory-entry-cues.md) | Historical | EN |
| [memory-graph-centering.md](memory-graph-centering.md) | Historical | EN |
| [memory-graph.md](memory-graph.md) | Historical | EN |
| [memory-integration-contract.md](memory-integration-contract.md) | Current | EN |
| [memory-search.md](memory-search.md) | Historical | EN |
| [memory-stopping-interview.md](memory-stopping-interview.md) | Historical | EN |
| [model-and-required-read.md](model-and-required-read.md) | Historical | EN |
| [phase-1-11-implementation.md](phase-1-11-implementation.md) | Historical | EN |
| [phase-1-11-live-validation.md](phase-1-11-live-validation.md) | Historical | EN |
| [physical-memory.md](physical-memory.md) | Historical | EN |
| [real-library-start.md](real-library-start.md) | Historical | EN |
| [reasoning-contract.md](reasoning-contract.md) | Historical | EN |
| [review-hardening.md](review-hardening.md) | Historical | EN |
| [roadmap.md](roadmap.md) | Historical | EN |
| [sleep-gemma26-comparison.md](sleep-gemma26-comparison.md) | Historical | EN |
| [sleep-reorganization-verification.md](sleep-reorganization-verification.md) | Historical | EN |
| [synaptic-memory-runtime.md](synaptic-memory-runtime.md) | Historical | EN |
| [token-context.md](token-context.md) | Historical | EN |
| [vision.md](vision.md) | Historical | EN |

## Maintenance rule

Keep current guidance aligned with code; preserve historical evidence with explicit
status. Code comments are English; new operating guides are English and Italian.
Run `python -m unittest discover -s tests -v` to check links and catalog coverage.
