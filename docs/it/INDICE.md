# Documentazione di Luca

[English](../README.md) · [README del progetto](../../README.it.md)

## Stato attuale — 2026-10-22

Luca è un sistema di memoria sinaptica esterna per LLM. Gestisce nodi, archi,
famiglie esplicite, indici, giostra fisica e modifiche atomiche. La produzione
e suddivisione dei contenuti sono responsabilità esterne; chat e cruscotto sono
utilizzatori di prova. Niente importazione PDF, biblioteche o integrazione Cesare.

Nel sonno l'LLM classifica la rubrica completa; il Core calcola i gruppi e
raggiunge l'obiettivo esatto quando la capacità compatibile a un livello basta.
La correttezza semantica generale del classificatore non è garantita.
Le soglie distribuite sono 50/45, non costanti obbligatorie del programma.

## Guide da leggere per prime

| Guida | Italiano | English |
| --- | --- | --- |
| Contratto produttori/consumer | [Contratto](fase-1-sinapsi/28-contratto-utilizzo-memoria.md) | [Contract](../memory-integration-contract.md) |
| Classificazione e pianificatore | [Algoritmo ed evidenze](fase-1-sinapsi/32-classificazione-e-pianificazione-archi.md) | [Planner](../category-routing-planner.md) |
| Avvio e configurazione | [Configurazione](configuration.md) | [Configuration](../configuration.md) |
| Frontend e ciclo di vita | [Cruscotto](gui-runtime.md) | [Dashboard](../gui-runtime.md) |
| Interfaccia LLM | [Connettore](llm-connector.md) | [Connector](../llm-connector.md) |
| Revisione documentale | [Audit](fase-1-sinapsi/33-revisione-documentazione.md) | [Audit](../documentation-audit.md) |
| Istruzioni del modello | [Bibbia runtime](../../bible.md) | [Traduzione di riferimento](../bible.en.md) |

## Come leggere lo storico

I documenti di fase sono evidenze datate, non una lista di funzionalità mancanti
o una roadmap ancora impegnativa. I relativi conteggi test, modelli, politiche
e comandi valgono per la fase descritta. Le note di stato li collegano al contratto
attuale senza cancellare risultati, errori o progetti superati.
I primi sei originali di fase sono soltanto italiani; le guide operative attuali
sono disponibili in entrambe le lingue. L'[indice precedente](INDICE-storico-20261022.md)
è conservato nello storico, insieme ai precedenti README e alle vecchie guide.

Bibbia e file sperimentali di prompt non sono tutti guide operative: la traduzione
inglese non viene caricata automaticamente. I manuali IRIS-17 sono dati fittizi
di test, non contenuti della memoria personale o istruzioni per hardware reale.

## Catalogo completo

Questo elenco comprende tutti i file Markdown sotto `docs/`, incluse le copie
archiviate. “Attuale” significa guida vigente; “Storico” significa fase/riferimento
datato; “Fixture” è materiale di prova.

| Documento | Stato | Lingua |
| --- | --- | --- |
| [README.md](../README.md) | Attuale | EN |
| [architecture.md](../architecture.md) | Storico | EN |
| [bible.en.md](../bible.en.md) | Attuale | EN |
| [bounded-synaptic-memory-design.md](../bounded-synaptic-memory-design.md) | Storico | EN |
| [category-routing-planner.md](../category-routing-planner.md) | Attuale | EN |
| [code-maintenance-review.md](../code-maintenance-review.md) | Storico | EN |
| [configuration.md](../configuration.md) | Attuale | EN |
| [controlled-document-experiment.md](../controlled-document-experiment.md) | Storico | EN |
| [curriculum.md](../curriculum.md) | Storico | EN |
| [dependency-audit.md](../dependency-audit.md) | Storico | EN |
| [documentation-audit.md](../documentation-audit.md) | Attuale | EN |
| [experiments.md](../experiments.md) | Storico | EN |
| [github-actions-checks.md](../github-actions-checks.md) | Storico | EN |
| [goal-first-recovery.md](../goal-first-recovery.md) | Storico | EN |
| [gui-runtime.md](../gui-runtime.md) | Attuale | EN |
| [history/configuration.en.md](../history/configuration.en.md) | Storico | EN |
| [history/configuration.it.md](../history/configuration.it.md) | Storico | IT |
| [history/gui-runtime.en.md](../history/gui-runtime.en.md) | Storico | EN |
| [history/gui-runtime.it.md](../history/gui-runtime.it.md) | Storico | IT |
| [history/llm-connector.en.md](../history/llm-connector.en.md) | Storico | EN |
| [history/llm-connector.it.md](../history/llm-connector.it.md) | Storico | IT |
| [history/readme.en.md](../history/readme.en.md) | Storico | EN |
| [history/readme.it.md](../history/readme.it.md) | Storico | IT |
| [integrated-knowledge-bible.md](../integrated-knowledge-bible.md) | Storico | EN |
| [iris17-manual.en.md](../iris17-manual.en.md) | Fixture | EN |
| [it/INDICE-storico-20261022.md](INDICE-storico-20261022.md) | Storico | IT |
| [it/INDICE.md](INDICE.md) | Attuale | IT |
| [it/architecture.md](architecture.md) | Storico | IT |
| [it/configuration.md](configuration.md) | Attuale | IT |
| [it/curriculum.md](curriculum.md) | Storico | IT |
| [it/dependency-audit.md](dependency-audit.md) | Storico | IT |
| [it/esperimenti/iris17-manuale.md](esperimenti/iris17-manuale.md) | Fixture | IT |
| [it/experiments.md](experiments.md) | Storico | IT |
| [it/fase-1-sinapsi/01-svolta-sinaptica.md](fase-1-sinapsi/01-svolta-sinaptica.md) | Storico | IT |
| [it/fase-1-sinapsi/02-roadmap-codice-fase-1.md](fase-1-sinapsi/02-roadmap-codice-fase-1.md) | Storico | IT |
| [it/fase-1-sinapsi/03-esperimento-favole-contrasto.md](fase-1-sinapsi/03-esperimento-favole-contrasto.md) | Storico | IT |
| [it/fase-1-sinapsi/04-unificazione-gui-cesare.md](fase-1-sinapsi/04-unificazione-gui-cesare.md) | Storico | IT |
| [it/fase-1-sinapsi/05-bibbia-gating-sinaptico-2b.md](fase-1-sinapsi/05-bibbia-gating-sinaptico-2b.md) | Storico | IT |
| [it/fase-1-sinapsi/06-indicizzazione-famiglie-archi-multipli.md](fase-1-sinapsi/06-indicizzazione-famiglie-archi-multipli.md) | Storico | IT |
| [it/fase-1-sinapsi/07-completamento-runtime.md](fase-1-sinapsi/07-completamento-runtime.md) | Storico | IT |
| [it/fase-1-sinapsi/08-roadmap-utilizzo-memoria.md](fase-1-sinapsi/08-roadmap-utilizzo-memoria.md) | Storico | IT |
| [it/fase-1-sinapsi/09-memoria-fisica.md](fase-1-sinapsi/09-memoria-fisica.md) | Storico | IT |
| [it/fase-1-sinapsi/10-verifica-claude.md](fase-1-sinapsi/10-verifica-claude.md) | Storico | IT |
| [it/fase-1-sinapsi/11-memoria-sinaptica-riorganizzabile.md](fase-1-sinapsi/11-memoria-sinaptica-riorganizzabile.md) | Storico | IT |
| [it/fase-1-sinapsi/12-implementazione-memoria-navigabile.md](fase-1-sinapsi/12-implementazione-memoria-navigabile.md) | Storico | IT |
| [it/fase-1-sinapsi/13-verifica-live-lmstudio.md](fase-1-sinapsi/13-verifica-live-lmstudio.md) | Storico | IT |
| [it/fase-1-sinapsi/14-ingresso-memoria-e-dialogo.md](fase-1-sinapsi/14-ingresso-memoria-e-dialogo.md) | Storico | IT |
| [it/fase-1-sinapsi/15-contesto-in-token.md](fase-1-sinapsi/15-contesto-in-token.md) | Storico | IT |
| [it/fase-1-sinapsi/16-ragionamento-libero.md](fase-1-sinapsi/16-ragionamento-libero.md) | Storico | IT |
| [it/fase-1-sinapsi/17-bibbia-conoscenza-integrata.md](fase-1-sinapsi/17-bibbia-conoscenza-integrata.md) | Storico | IT |
| [it/fase-1-sinapsi/18-mappa-grafica-memoria.md](fase-1-sinapsi/18-mappa-grafica-memoria.md) | Storico | IT |
| [it/fase-1-sinapsi/19-correzione-centratura-mappa.md](fase-1-sinapsi/19-correzione-centratura-mappa.md) | Storico | IT |
| [it/fase-1-sinapsi/20-revisione-codice-e-commenti.md](fase-1-sinapsi/20-revisione-codice-e-commenti.md) | Storico | IT |
| [it/fase-1-sinapsi/21-controlli-github-actions.md](fase-1-sinapsi/21-controlli-github-actions.md) | Storico | IT |
| [it/fase-1-sinapsi/22-avvio-biblioteca-reale.md](fase-1-sinapsi/22-avvio-biblioteca-reale.md) | Storico | IT |
| [it/fase-1-sinapsi/23-esperimento-documento-controllato.md](fase-1-sinapsi/23-esperimento-documento-controllato.md) | Storico | IT |
| [it/fase-1-sinapsi/24-autonomia-e-attualita-memoria.md](fase-1-sinapsi/24-autonomia-e-attualita-memoria.md) | Storico | IT |
| [it/fase-1-sinapsi/25-modello-lettura-obbligatoria-multi-gpu.md](fase-1-sinapsi/25-modello-lettura-obbligatoria-multi-gpu.md) | Storico | IT |
| [it/fase-1-sinapsi/26-intervista-arresto-lettura.md](fase-1-sinapsi/26-intervista-arresto-lettura.md) | Storico | IT |
| [it/fase-1-sinapsi/27-ripristino-obiettivo-esplicito.md](fase-1-sinapsi/27-ripristino-obiettivo-esplicito.md) | Storico | IT |
| [it/fase-1-sinapsi/28-contratto-utilizzo-memoria.md](fase-1-sinapsi/28-contratto-utilizzo-memoria.md) | Attuale | IT |
| [it/fase-1-sinapsi/29-verifica-riorganizzazione-sonno.md](fase-1-sinapsi/29-verifica-riorganizzazione-sonno.md) | Storico | IT |
| [it/fase-1-sinapsi/30-arresto-riorganizzazione-obiettivo.md](fase-1-sinapsi/30-arresto-riorganizzazione-obiettivo.md) | Storico | IT |
| [it/fase-1-sinapsi/31-confronto-sonno-gemma26.md](fase-1-sinapsi/31-confronto-sonno-gemma26.md) | Storico | IT |
| [it/fase-1-sinapsi/32-classificazione-e-pianificazione-archi.md](fase-1-sinapsi/32-classificazione-e-pianificazione-archi.md) | Attuale | IT |
| [it/fase-1-sinapsi/33-revisione-documentazione.md](fase-1-sinapsi/33-revisione-documentazione.md) | Attuale | IT |
| [it/gui-runtime.md](gui-runtime.md) | Attuale | IT |
| [it/language-adapters.md](language-adapters.md) | Storico | IT |
| [it/llm-connector.md](llm-connector.md) | Attuale | IT |
| [it/memory-search.md](memory-search.md) | Storico | IT |
| [it/roadmap.md](roadmap.md) | Storico | IT |
| [it/vision.md](vision.md) | Storico | IT |
| [language-adapters.md](../language-adapters.md) | Storico | EN |
| [llm-connector.md](../llm-connector.md) | Attuale | EN |
| [maintenance-target-stop.md](../maintenance-target-stop.md) | Storico | EN |
| [memory-autonomy-investigation.md](../memory-autonomy-investigation.md) | Storico | EN |
| [memory-development-roadmap.md](../memory-development-roadmap.md) | Storico | EN |
| [memory-entry-cues.md](../memory-entry-cues.md) | Storico | EN |
| [memory-graph-centering.md](../memory-graph-centering.md) | Storico | EN |
| [memory-graph.md](../memory-graph.md) | Storico | EN |
| [memory-integration-contract.md](../memory-integration-contract.md) | Attuale | EN |
| [memory-search.md](../memory-search.md) | Storico | EN |
| [memory-stopping-interview.md](../memory-stopping-interview.md) | Storico | EN |
| [model-and-required-read.md](../model-and-required-read.md) | Storico | EN |
| [phase-1-11-implementation.md](../phase-1-11-implementation.md) | Storico | EN |
| [phase-1-11-live-validation.md](../phase-1-11-live-validation.md) | Storico | EN |
| [physical-memory.md](../physical-memory.md) | Storico | EN |
| [real-library-start.md](../real-library-start.md) | Storico | EN |
| [reasoning-contract.md](../reasoning-contract.md) | Storico | EN |
| [review-hardening.md](../review-hardening.md) | Storico | EN |
| [roadmap.md](../roadmap.md) | Storico | EN |
| [sleep-gemma26-comparison.md](../sleep-gemma26-comparison.md) | Storico | EN |
| [sleep-reorganization-verification.md](../sleep-reorganization-verification.md) | Storico | EN |
| [synaptic-memory-runtime.md](../synaptic-memory-runtime.md) | Storico | EN |
| [token-context.md](../token-context.md) | Storico | EN |
| [vision.md](../vision.md) | Storico | EN |

## Metodo

Mantenere guide e codice allineati; conservare la storia dichiarandone lo stato;
commenti al codice in inglese; nuove guide operative in italiano e inglese.
Verificare link e catalogo con `python -m unittest discover -s tests -v`.
