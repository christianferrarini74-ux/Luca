# Indice Generale della Documentazione di LUCA

> **Regola fondamentale del progetto:** *Non si sovrascrive il passato.*
> Ogni documento riflette il pensiero, le scelte architetturali, gli esperimenti e i problemi di una specifica fase evolutiva di LUCA. Quando il progetto cambia direzione o matura, i documenti precedenti vengono **conservati intatti** per mantenere la memoria storica completa del percorso, e i nuovi documenti vengono aggiunti nella fase corrispondente.

---

## 🧭 Bussola Rapida: Dove Siamo Oggi

Correzione 2026-10-22: [centratura della mappa dopo il trascinamento](fase-1-sinapsi/19-correzione-centratura-mappa.md)
([English](../memory-graph-centering.md)). Risolta la perdita delle coordinate
DOMPoint e aggiunto recupero della geometria; 10 test JavaScript e 219 Python.

Mappa 2026-10-22: [visualizzazione interattiva della memoria](fase-1-sinapsi/18-mappa-grafica-memoria.md)
([English](../memory-graph.md)). Globale/focus, famiglie, livelli e percorso del
navigatore; ispezione senza richiamo. Nessuna nuova dipendenza; 219 test Python
con CUDA/tokenizer reali e 5 test JavaScript. Limiti grafici configurabili.

Bibbia 2026-10-22: [conoscenza acquisita e conoscenza generale](fase-1-sinapsi/17-bibbia-conoscenza-integrata.md)
([English](../integrated-knowledge-bible.md)). 210 test con CUDA/tokenizer reali,
8/8 controlli nel nuovo dialogo di integrazione; restano premesse sulle fonti
e dettagli aggiunti. Nessuna modifica al Core o alla memoria personale.

Ragionamento 2026-10-21: [bibbia unica, letture multiple e libertà del modello](fase-1-sinapsi/16-ragionamento-libero.md)
([English](../reasoning-contract.md)). Separazione istruzioni/dati, eliminazione
dei filtri semantici, opzioni di generazione esplicite e risposte dirette dalla
navigazione. 206 test automatici con CUDA/tokenizer reali, 8/8 sintetici live;
dialogo 7/8 per esplorazione ulteriore ancora inaffidabile. Limiti nel resoconto.

Contesto 2026-10-21: [70.000 token e budget configurabili](fase-1-sinapsi/15-contesto-in-token.md)
([English](../token-context.md)). Conteggio nativo del modello senza nuove
dipendenze; cronologia misurata in token, memoria fisica in byte. 182 test con
tokenizer e CUDA reali; prova di costruzione prompt da 63.760 token.

Correzione del dialogo 2026-10-21: [ingresso nella memoria e continuità](fase-1-sinapsi/14-ingresso-memoria-e-dialogo.md)
([English](../memory-entry-cues.md)). Indice globale anticipato di soli metadati,
stato “non usato” distinto da “inesistente”, estratti espliciti della cronologia.
158 test con CUDA reale e 8/8 sintetici; dialogo completo non ancora accettato per
cause inventate e svalutazione del ricordo come “testo fornito”.

Verifica live 2026-10-21: [LM Studio e Gemma E2B](fase-1-sinapsi/13-verifica-live-lmstudio.md)
([English](../phase-1-11-live-validation.md)). Ultima esecuzione 7/8: meccanismi
strutturali verificati, richiamo spontaneo non ancora affidabile e nomi dei gruppi
da validare semanticamente. Corretto il formato JSON del provider; introdotti
budget operativi configurabili. Suite aggiornata: 151 test, anche CUDA reale.

Implementazione 2026-10-21: [Fase 1.11 — Esecuzione, contratti e verifiche](fase-1-sinapsi/12-implementazione-memoria-navigabile.md)
([English](../phase-1-11-implementation.md)). Realizzati famiglie canoniche,
aggiornamenti atomici, indici globale/rapido, navigazione LLM e manutenzione con
conferma/ripristino e worker in inattività. Il resoconto distingue test controllati,
CUDA reale e prova conversazionale ancora da effettuare con LM Studio disponibile.
Le annotazioni progettuali seguenti descrivono il momento precedente all'implementazione.

Sintesi progettuale 2026-10-20: [Fase 1.11 — Memoria navigabile e riorganizzabile](fase-1-sinapsi/11-memoria-sinaptica-riorganizzabile.md)
([English](../bounded-synaptic-memory-design.md)): indice del libro, connettività
completa, limiti morbidi, nodi intermedi e manutenzione locale. È la base per la
prossima roadmap, non una funzionalità implementata. Luca è autonomo: i riferimenti
storici a Cesare riportati sotto non sono vincoli per la sua architettura attuale.

Integrazione Fase 1.11: contenuto misurato in parole (token esatti se semplici da
ottenere); ogni frammento mantiene l'intera rubrica del nodo suddiviso. La vista
di navigazione effettiva conta anche gli archi ereditati, non soltanto quelli locali.

Decisioni successive del §14: prossima fase limitata a navigazione e archi;
soglie configurabili 50/45, rubrica ID/titolo, manutenzione manuale confermata
oppure automatica in inattività per i soli sforamenti. Distillazione dei contenuti
e biblioteca reale rinviate, non prerequisiti della fase corrente.

Chiusura concettuale confermata: famiglia A = padre e parti An con un'unica
identità e rubrica; uscire da una parte verso B percorre A→B. Il limite 50/45
riguarda i soli archi esterni, con collegamenti interni contati separatamente.
I nodi G di raggruppamento hanno invece identità e rubrica proprie. La specifica
è pronta per la roadmap; il nuovo modello non è ancora implementato.

Integrazione sui punti d'ingresso: indice globale per individuare l'argomento
nell'intera memoria e indice rapido del primo grado per continuare dal focus,
separati dai contenuti trasferiti dalla giostra. Secondo grado opzionale da
valutare; residenza e budget del rapido da verificare nell'implementazione.

Aggiornamento 2026-10-19: [Fase 1.10 — Verifica delle proposte di Claude](fase-1-sinapsi/10-verifica-claude.md)
([English](../review-hardening.md)): impronta seed, migrazione contatori alias
con ordinamento invariato e riduzione misurata delle copie GPU senza cache host.

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
