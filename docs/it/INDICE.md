# Indice Generale della Documentazione di LUCA

> **Regola fondamentale del progetto:** *Non si sovrascrive il passato.*
> Ogni documento riflette il pensiero, le scelte architetturali, gli esperimenti e i problemi di una specifica fase evolutiva di LUCA. Quando il progetto cambia direzione o matura, i documenti precedenti vengono **conservati intatti** per mantenere la memoria storica completa del percorso, e i nuovi documenti vengono aggiunti nella fase corrispondente.

---

## 🧭 Bussola Rapida: Dove Siamo Oggi

Aggiornamento 2026-10-19: [Fase 1.09 — Giostra fisica SSD/RAM/GPU](fase-1-sinapsi/09-memoria-fisica.md)
([English](../physical-memory.md)): allocazioni CUDA native, nodi completi,
trasferimenti verificati, diagnostica e rilascio risorse. [Audit dipendenze](dependency-audit.md).
Biblioteca reale da verificare insieme a Christian; nessuna integrazione Cesare.

Aggiornamento 2026-10-19: [Fase 1.08 — Utilizzo della memoria, punti 1–5](fase-1-sinapsi/08-roadmap-utilizzo-memoria.md)
([English](../memory-development-roadmap.md)): planner, attività e oblio, budget,
documenti e sezioni, continuità del compito. Integrazione con Cesare rinviata.

Aggiornamento 2026-10-19: [Fase 1.07 — Completamento del runtime](fase-1-sinapsi/07-completamento-runtime.md)
([English](../synaptic-memory-runtime.md)). Questo aggiornamento integra gli
stati storici riportati nelle tabelle: politiche fast/complete, diagnostica per
turno, apertura esplicita delle alternative e cruscotto.

- **Fase Attiva:** **Fase 1 — Architettura Sinaptica della Conoscenza e Giostra dei Livelli (`VRAM ↔ RAM ↔ SSD`)**
- **Obiettivo Strategico:** Costruire in LUCA una nuova fonte di conoscenza esplicita e sinaptica per gli LLM (testata con modelli locali piccoli da 1B–2B o medi fino a 26B, e destinata a entrare in **Cesare** con modelli frontier).
- **Documenti di riferimento attuali (da leggere per primi):**
  1. [Fase 1.01 — La Svolta Sinaptica: dai Nodi-Parola ai Blocchi di Conoscenza](fase-1-sinapsi/01-svolta-sinaptica.md)
  2. [Fase 1.02 — Roadmap e Specifica Modulare del Codice (La Giostra Sinaptica)](fase-1-sinapsi/02-roadmap-codice-fase-1.md)
  3. [Fase 1.03 — Esperimento Favole ("Liquido di Contrasto")](fase-1-sinapsi/03-esperimento-favole-contrasto.md)
  4. [Fase 1.04 — Unificazione GUI con il Cockpit di Cesare](fase-1-sinapsi/04-unificazione-gui-cesare.md)
  5. [Fase 1.05 — Bibbia Invisibile, Gating Sinaptico (`[APERTA]` vs `[1° grado]`) e Salto al 2B (`gemma-4-e2b`)](fase-1-sinapsi/05-bibbia-gating-sinaptico-2b.md)
  6. [Fase 1.06 — Indicizzazione per Famiglie `prefisso:suffisso`, Archi Multipli e Flotta dei Sommergibili](fase-1-sinapsi/06-indicizzazione-famiglie-archi-multipli.md)

---

## 📜 Cronologia Evolutiva del Progetto

### Fase 0 — Genesi: Prototipo a Nodi-Parola e Asserzioni Atomiche (`v0.1`)
- **Cosa avevamo pensato:** Partire da un micro-vocabolario italiano in cui ogni singola parola (`sole`, `scalda`, `pelle`) è una cella `concept` e ogni fatto semplice è una cella intermedia `assertion` collegata da tre archi (`sole → asserzione → scalda / pelle`), con un motore di pensiero (`ThoughtEngine`) che espande alla cieca fino a profondità 3.
- **Cosa abbiamo ottenuto:** Validazione dello storage SQLite deterministico con indici diretti `(source_id, target_id)` e inversi `(target_id, source_id)`, ricerca FTS5, connettore LLM locale (LM Studio) e dashboard web.
- **Perché l'abbiamo superata (Lezione appresa):**
  1. Usare i nodi per singole parole cercava di ricostruire la grammatica nel grafo, sprecando la struttura sinaptica per qualcosa che anche un LLM da 2B sa già fare benissimo.
  2. L'espansione cieca a profondità 3 caricava livelli non richiesti invece di seguire lo spostamento reale del pensiero.
  3. I livelli `RAM` e `VRAM` erano stateless (ricalcolati da zero a ogni turno e subito buttati via) invece di funzionare come veri slot dinamici con scivolamento per mancato utilizzo.

#### Catalogo Documenti Storici — Fase 0 (Conservati Intatti)
| Documento (IT) | Documento (EN) | Contenuto Storico |
| :--- | :--- | :--- |
| [vision.md](vision.md) | [../vision.md](../vision.md) | Visione originaria: memoria esplicita vs pesi opachi dell'LLM. |
| [architecture.md](architecture.md) | [../architecture.md](../architecture.md) | Architettura logica originaria: celle, archi puri e gerarchia SSD/RAM/VRAM. |
| [roadmap.md](roadmap.md) | [../roadmap.md](../roadmap.md) | Prima roadmap di validazione in 6 tappe (dal dimostratore al fabric distribuito). |
| [experiments.md](experiments.md) | [../experiments.md](../experiments.md) | Protocollo sperimentale iniziale per i benchmark sul grafo sintetico. |
| [curriculum.md](curriculum.md) | [../curriculum.md](../curriculum.md) | Specifica del primo seed italiano a triple atomiche (`seed/italian_base_v0.json`). |
| [memory-search.md](memory-search.md) | [../memory-search.md](../memory-search.md) | Livello di ricerca lessicale FTS5 e filtro sulle celle `assertion`. |
| [language-adapters.md](language-adapters.md) | [../language-adapters.md](../language-adapters.md) | Contratto tra `RuleAdapter`, `LMStudioAdapter` e `MemoryEditor`. |
| [llm-connector.md](llm-connector.md) | [../llm-connector.md](../llm-connector.md) | Connettore neutrale verso LM Studio, Ollama e provider OpenAI-compatibili. |
| [configuration.md](configuration.md) | [../configuration.md](../configuration.md) | Configurazione centralizzata tramite `config.yaml`. |
| [gui-runtime.md](gui-runtime.md) | [../gui-runtime.md](../gui-runtime.md) | Architettura del punto di avvio unico `run_luca.py` e dashboard frontend. |

---

### Fase 1 — Architettura Sinaptica della Conoscenza (`In Corso`)
- **Cosa stiamo costruendo:**
  - **Nodi di Conoscenza Articolata:** ogni nodo non è più una parolina ma un blocco completo e autosufficiente di conoscenza (un pensiero articolato, una distillazione in stile Biblioteca di Cesare, o l'equivalente di un'intera dipendenza/modulo).
  - **Archi `prefisso:suffisso` Auto-Ordinanti e Indicizzazione per Famiglie:** gli archi collegano direttamente i nodi di conoscenza mantenendo l'ordine logico tramite l'incastro `A:B` ↔ `B:C`; i nodi che condividono lo stesso prefisso (`F:*`) o suffisso (`*:S`) formano famiglie indicizzate direttamente in SQLite, e l'intersezione tra più archi (`F1:* ∩ F2:*`) disambigua in tempo logaritmico il nodo specifico.
  - **Richiamo del Grappolo di 1° Grado e Gating `[APERTA]` vs `[1° grado]`:** richiamare `B` dall'`SSD` catapulta in `VRAM` il nodo `B` (`[APERTA]`) più i suoi archi top-$K$ `B:*` / `*:B` e i nodi di 1° livello (`[1° grado]`, pre-caricati ma chiusi finché la conversazione non fa step su di essi).
  - **Giostra `VRAM ↔ RAM ↔ SSD` per Utilizzo e Isolamento Componenti:** slot reali a capienza finita; i ricordi non richiamati scivolano da `VRAM` a `RAM` e poi in `SSD`, mentre il prompt riceve solo la componente connessa al focus attivo.

#### Catalogo Documenti — Fase 1
| Documento | Stato | Descrizione |
| :--- | :--- | :--- |
| [01-svolta-sinaptica.md](fase-1-sinapsi/01-svolta-sinaptica.md) | **Attivo** | Dettaglio concettuale e biologico-architetturale del nuovo modello sinaptico di LUCA. |
| [02-roadmap-codice-fase-1.md](fase-1-sinapsi/02-roadmap-codice-fase-1.md) | **Completato (43/43 test)** | Piano di implementazione modulare (anti-spaghetti) passo-passo per costruire e testare la giostra sinaptica. |
| [03-esperimento-favole-contrasto.md](fase-1-sinapsi/03-esperimento-favole-contrasto.md) | **Completato** | Protocollo di test con "favole assurde" (liquido di contrasto) e cronologia delle revisioni 1.1–1.4. |
| [04-unificazione-gui-cesare.md](fase-1-sinapsi/04-unificazione-gui-cesare.md) | **Completato** | Unificazione della GUI di Luca con il cockpit di Cesare (`packages/gui_kit`), servita direttamente dal backend Python senza Streamlit né Node a runtime. |
| [05-bibbia-gating-sinaptico-2b.md](fase-1-sinapsi/05-bibbia-gating-sinaptico-2b.md) | **Completato (45/45 test)** | `bible.md` a vocabolario invisibile, filtro di componente connessa in `VRAM`, gating `[APERTA]` vs `[1° grado]`, step automatico `prefisso`/`suffisso` e passaggio a `google/gemma-4-e2b`. |
| [06-indicizzazione-famiglie-archi-multipli.md](fase-1-sinapsi/06-indicizzazione-famiglie-archi-multipli.md) | **Completato (50/50 test)** | Famiglie `prefisso:suffisso` (`P:*` e `*:S`), separazione tra ricerca su `SSD` e precaricamento `VRAM`, modalità `strict` (intersezione vincolante) vs `associative`, pertinenza prima della recenza e benchmark di scalabilità fino a $10\,000$ membri/famiglia. |

---

## 📏 Regole di Metodo per Chiunque Lavori su LUCA (Umani e AI)

1. **La documentazione precede o accompagna sempre il codice:** ogni nuova idea, modifica architetturale o correzione di rotta va prima fissata in `docs/` e registrata in questo indice.
2. **Divieto assoluto di sovrascrivere la storia:** non cancellare o riscrivere i documenti delle fasi passate per farli sembrare "sempre stati così". Aggiungere nuovi documenti datati/numerati che spiegano il *perché* del cambiamento.
3. **Zero Spaghetti Code:** ogni file di codice deve avere una singola responsabilità chiara. Quando un modulo cresce o intreccia più concetti, **deve** essere scomposto preventivamente in moduli piccoli, leggibili e testabili separatamente.
4. **Specifiche eseguibili:** le roadmap del codice devono essere scritte con tale precisione che anche un LLM più piccolo ed economico possa implementarne i singoli blocchi sotto la supervisione di un modello frontier.
