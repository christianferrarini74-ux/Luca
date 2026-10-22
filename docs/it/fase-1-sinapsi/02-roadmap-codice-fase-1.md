# Fase 1.02 — Roadmap e Specifica Modulare del Codice (La Giostra Sinaptica)

> **Documento storico — non guida operativa attuale.** Specifiche, default, risultati e passi successivi qui descritti appartengono alla fase registrata. Per ambito, API e comportamento vigenti leggere il [contratto attuale](28-contratto-utilizzo-memoria.md). Le evidenze originali sono conservate.

> **Stato di avanzamento:** **COMPLETATA (Tappe 1–6 implementate e verificate — 43/43 test superati)**
>
> **Obiettivo di questo documento:** Definire la scomposizione modulare e i passi esatti di implementazione della **Fase 1A (La Giostra Sinaptica)**.
> Ogni modulo ha una singola responsabilità, confini netti e file piccoli per prevenire qualsiasi forma di *spaghetti code*. Questa roadmap è scritta per poter essere eseguita passo dopo passo (anche da modelli LLM più piccoli) e verificata con test automatici ad ogni tappa.

---

## 1. Principi Ingegneristici e Struttura dei Moduli

Per evitare file monolitici, la nuova architettura affianca ai moduli esistenti una struttura pulita e separata per responsabilità:

```text
luca_memory/
├── store.py                 # Storage SQLite su SSD (celle, archi prefisso:suffisso, contatori d'uso)
├── node.py                  # [NUOVO] Modello del Nodo di Conoscenza Articolata (KnowledgeNode)
├── tiers/                   # [NUOVO PACCHETTO] La Giostra dei Livelli (VRAM ↔ RAM ↔ SSD)
│   ├── __init__.py
│   ├── slot.py              # TierSlot: coda ordinata a capienza fissa con espulsione LRU
│   ├── graph_view.py        # Assemblaggio auto-ordinante degli archi prefisso:suffisso
│   └── carousel.py          # SynapticCarousel: richiamo 1° grado, spostamento fuoco, cascata VRAM→RAM→SSD
├── context_builder.py       # [NUOVO] Formattazione della VRAM in contesto leggibile per l'LLM
├── seed_v1.py               # [NUOVO] Caricamento dei nodi ricchi "a tavolino"
├── session.py               # Integrazione della Giostra nella sessione conversazionale
└── api.py                   # Esposizione dello stato reale di VRAM, RAM e SSD alla Dashboard GUI
```

> **Regola di taglia massima:** Nessun file del pacchetto `tiers/` o dei nuovi moduli deve superare le **120–150 righe di codice**. Se un file cresce oltre quella soglia, va diviso.

---

## 2. Tappe di Implementazione (Passo dopo Passo)

### Tappa 1 — Il Nodo di Conoscenza Articolata (`luca_memory/node.py`)
**Scopo:** Superare la vecchia divisione tra paroline (`concept`) e triple (`assertion`) introducendo il blocco di conoscenza ricco, retrocompatibile con la tabella `cells` di SQLite.

- **Cosa contiene un `KnowledgeNode`:**
  - `id: int` — indirizzo numerico univoco della cella.
  - `slug: str` — chiave identificativa leggibile (es. `"architettura_livelli_memoria"`).
  - `title: str` — titolo sintetico del blocco di conoscenza.
  - `content: str` — il pensiero articolato completo (può essere un paragrafo, una specifica tecnica o un intero modulo).
  - `keywords: tuple[str, ...]` — parole chiave / concetti-ancora che permettono di agganciare il nodo dall'esterno.
  - `recall_count: int` e `last_recalled_at: int` — metadati di utilizzo sinaptico.
- **Criterio di verifica (`tests/test_node.py`):**
  - Serializzazione e deserializzazione JSON dentro `Cell.content` senza perdita di dati.
  - Ricerca esatta per `slug`/`keywords` e full-text search tramite FTS5 sul contenuto articolato.

---

### Tappa 2 — Ordine Sinaptico degli Archi nell'SSD (`luca_memory/store.py`)
**Scopo:** Fare in modo che gli archi `(source_id, target_id)` (`prefisso:suffisso`) riflettano l'utilizzo, così che le sinapsi più usate siano immediate e quelle non usate diventino più remote.

- **Modifica a `MemoryStore`:**
  - La tabella `edges` mantiene la chiave primaria `(source_id, target_id)` ma registra `last_used_at: int` e `use_count: int` (con migrazione trasparente se il DB esiste già).
  - `touch_edge(source_id, target_id)` aggiorna il timestamp e incrementa l'utilizzo quando l'arco viene percorso.
  - `outgoing(source_id)` (`B:*`) e `incoming(target_id)` (`*:B`) ordinano i risultati per **`last_used_at DESC, use_count DESC`** invece che per semplice ID numerico: gli archi vivi sono in prima fila, quelli dimenticati scivolano in fondo.
- **Criterio di verifica (`tests/test_store_synaptic_order.py`):**
  - Dati 3 archi uscenti da `B` (`B:1`, `B:2`, `B:3`), se viene richiamato `B:3`, la query `outgoing(B)` restituisce `B:3` in prima posizione e fa scivolare gli altri indietro.

---

### Tappa 3 — Lo Slot di Livello e l'Auto-Ordinamento (`luca_memory/tiers/slot.py` e `graph_view.py`)
**Scopo:** Creare il contenitore base per `VRAM` e `RAM` e il meccanismo "domino" che incastona automaticamente gli archi `prefisso:suffisso`.

- **`TierSlot` (`luca_memory/tiers/slot.py`):**
  - Usa una struttura ordinata (`OrderedDict[int, KnowledgeNode]`) con capienza massima configurabile (`max_nodes`).
  - `promote(node)`: inserisce il nodo o, se già presente, lo sposta **in testa** (più recente). Se lo slot supera `max_nodes`, espelle il nodo **in coda** (meno recentemente richiamato) e restituisce la lista dei nodi espulsi così che il livello inferiore possa raccoglierli.
  - `remove(node_id)`: rimuove un nodo dallo slot (usato quando un nodo in `RAM` viene promosso in `VRAM`).
- **`GraphView` (`luca_memory/tiers/graph_view.py`):**
  - Mantiene gli archi attivi per i nodi presenti nello slot.
  - Ricostruisce automaticamente le catene ordinate `A → B → C` verificando dove il **suffisso** di `A:B` coincide con il **prefisso** di `B:C`.
- **Criterio di verifica (`tests/test_tier_slot.py`):**
  - Test di capienza: con `max_nodes = 3`, inserendo `1, 2, 3` e poi richiamando `1`, l'ordine diventa `[1, 3, 2]`. Inserendo `4`, viene espulso `2` (il meno recente, NON il primo entrato).
  - Test domino: caricando i nodi `A, B, C` in ordine sparso con gli archi `A:B` e `B:C`, `GraphView` ricostruisce la catena ordinata `A → B → C`.

---

### Tappa 4 — La Giostra Sinaptica (`luca_memory/tiers/carousel.py`)
**Scopo:** Implementare il cuore del movimento `SSD ↔ RAM ↔ VRAM` e la regola rigorosa del **1° grado**.

- **Funzionamento di `SynapticCarousel`:**
  1. **`recall(node_id)` (Richiamo di un nodo `B`):**
     - Carica `B` (da `RAM` o da `SSD`) e lo porta in **testa alla `VRAM`**.
     - Recupera tutti gli archi con prefisso `B:*` (uscenti) e suffisso `*:B` (entranti) e carica in **`VRAM`** i relativi nodi di **1° grado**.
     - Marca `B` come **nodo espanso (centro attivo)** e i suoi vicini di 1° grado come **nodi di confine (non ancora espansi al 2° grado)**.
     - Ogni nodo che trabocca dalla `VRAM` perché piena scende in **testa alla `RAM`**; ogni nodo che trabocca dalla `RAM` torna a riposare solo su **`SSD`**.
  2. **`step_to(neighbour_id)` (Spostamento del pensiero sul 1° grado per aprire il 2°):**
     - Quando il pensiero si sposta su un nodo `C` già presente in `VRAM` (perché toccato dalla conversazione, per convergenza di 2+ archi attivi, o su richiesta dell'LLM), `C` esegue `recall(C)` tirando su in `VRAM` il suo grappolo `*:C` e `C:*` (il 2° livello rispetto a `B`).
  3. **`check_convergence()` (Riflesso sinaptico automatico):**
     - Se in un turno due nodi richiamati (`B1` e `B2`) condividono entrambi un arco verso lo stesso nodo non espanso `X`, `X` riceve due impulsi convergenti e viene espanso automaticamente in `VRAM`.
- **Criterio di verifica (`tests/test_carousel.py`):**
  - Verifica che richiamando `B` in una catena `A → B → C → D`, in `VRAM` salgano `A, B, C` e gli archi `A:B`, `B:C`, ma **NON** salga `D` né l'arco `C:D`.
  - Verifica che spostando il pensiero su `C` (`step_to(C)`), salga in `VRAM` anche `D` con l'arco `C:D`.
  - Verifica che riempiendo la `VRAM`, i nodi più vecchi scendano in `RAM` e poi in `SSD`, e che richiamandoli dall'`SSD` tornino in testa alla `VRAM` col loro grappolo.

---

### Tappa 5 — Seed "A Tavolino" di Nodi Articolati (`seed/knowledge_base_v1.json` e `luca_memory/seed_v1.py`)
**Scopo:** Creare il primo grafo di test realistico (12–15 blocchi di conoscenza articolata e interconnessa, simili a distillazioni della Biblioteca di Cesare / moduli architetturali) per far girare la giostra.

- **Struttura del Seed v1:**
  - Nodi con pensieri articolati completi (es. architettura di Luca, livelli di memoria, ruolo dell'LLM, progetto Cesare, distillazione della biblioteca, gestione delle dipendenze, plasticità sinaptica, ecc.) collegati da una rete di archi `prefisso:suffisso` di 1°, 2° e 3° grado.
- **Criterio di verifica (`tests/test_seed_v1.py`):**
  - Caricamento deterministico su database vuoto, verifica degli archi `prefisso:suffisso` e test di navigazione multi-salto tramite la Giostra.

---

### Tappa 6 — Contesto LLM, Sessione e Dashboard GUI (`context_builder.py`, `session.py`, `api.py`, `gui/`)
**Scopo:** Collegare la Giostra Sinaptica all'LLM locale e rendere visibili i tre livelli (`VRAM`, `RAM`, `SSD`) nella Dashboard.

- **`context_builder.py`:**
  - Formatta il contenuto attuale della `VRAM` per l'LLM mostrando:
    1. I **Blocchi Attivi in VRAM** con il loro testo completo e le catene `prefisso → nodo → suffisso` già auto-assemblate.
    2. I **Nodi di Confine (1° grado)** attaccati agli archi, indicando che sono pronti ad essere esplorati se il discorso si sposta su di essi.
- **`api.py` e `gui/app/page.tsx`:**
  - `/api/state` restituisce l'elenco reale dei nodi attualmente in `VRAM` (in ordine di freschezza), dei nodi scivolati in `RAM` e il conteggio dei nodi su `SSD`, oltre agli archi `prefisso:suffisso` attivi.
- **Criterio di verifica (`tests/test_session.py` e `tests/test_api.py`):**
  - Tutti i test esistenti ed i nuovi test end-to-end passano al 100%.
