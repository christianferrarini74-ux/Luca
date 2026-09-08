# Luca

[English](README.md) | [Italiano](README.it.md)

Luca è un progetto sperimentale che esplora una memoria esplicita e persistente
invece di un modello linguistico pre-addestrato. Ogni tesi importante deve
essere sostenuta da un esperimento piccolo e riproducibile.

## Modello di lavoro

- Le **celle** contengono conoscenza e stato: concetti, esperienze, ipotesi, evidenze e conclusioni.
- Gli **archi** non contengono semantica. Sono indirizzi diretti tra celle, identificati da `(source_id, target_id)`.
- Il grafo diretto è la navigazione certa di Luca: `A:*` cerca percorsi uscenti e `*:B` percorsi entranti.
- Un futuro indice associativo può proporre candidati lontani, ma solo il grafo esplicito può verificare una connessione.

```text
SSD   cervello completo e persistente
RAM   contesto attivo e vicinato topologico
VRAM  working set più piccolo e prioritario per un pensiero
```

La CPU coordina lavoro e consolidamento. I worker GPU sono acceleratori
opzionali: l'implementazione CPU resta la baseline semantica e le GPU non
scrivono mai direttamente nella memoria persistente.

Leggi [l'architettura](docs/architecture.md) e [il protocollo sperimentale](docs/experiments.md)
prima di estendere il sistema. Il primo seme italiano controllato è descritto
nelle [specifiche del curriculum](docs/it/curriculum.md). Scopo e tappe sono
descritti nella [visione](docs/vision.md) e nella [roadmap](docs/roadmap.md).
Il confine sostituibile tra linguaggio e memoria durevole è definito nel
[protocollo degli adapter linguistici](docs/language-adapters.md).
Il livello di recupero indicizzato è descritto nella [ricerca della memoria](docs/it/memory-search.md).

## Esperimento attuale

Il codice valida l'accesso deterministico al grafo e fornisce una baseline CPU
per un pensiero locale delimitato: attiva celle-seme, espande attraverso
indirizzi entranti e uscenti, assegna un punteggio al contesto scoperto e
conserva un focus più piccolo, delle dimensioni della VRAM. Non richiede
dipendenze esterne.

## Verifica

```powershell
python -m unittest discover -s tests -v
```

## Conversazione persistente

```powershell
python -m luca_memory.chat --database .\luca.sqlite
```

Per usare l'interprete locale Gemma tramite LM Studio, caricare
`gemma-3-1B-it-QAT-GGUF`, avviare il server locale e impostare
`runtime.language_adapter: gemma` in `config.yaml`.

```powershell
python run_luca.py
```

Endpoint e modello sono configurati nella sezione `llm.runtimes` di
`config.yaml`. Luca non contatta LM Studio quando l'adapter configurato è
`rules`; se LM Studio non è disponibile, non viene
scritta alcuna lezione parziale.

## Avviare il runtime completo di Luca

Il punto di avvio unico legge `config.yaml`, avvia il runtime Python, avvia il
frontend e apre automaticamente la dashboard nel browser. La GUI resta solo un
frontend: visualizza lo stato restituito da Luca e non contiene la logica della
memoria o del linguaggio.

Avviare il runtime completo dalla radice del repository:

```powershell
python run_luca.py
```

Per usare l'adapter Gemma locale, avviare prima LM Studio, impostare
`runtime.language_adapter: gemma` in `config.yaml` e usare lo stesso comando:

```powershell
python run_luca.py
```

La dashboard chiama `http://127.0.0.1:8765/api` per la chat e gli snapshot del
runtime. Il backend resta l'unico componente autorizzato ad accedere alla
memoria di Luca e al connector LLM.

## Stato

Questa è una baseline SQLite sostituibile. Valida accesso ai dati, budget del
pensiero e apprendimento persistente prima di introdurre un formato cerebrale
personalizzato, una cache, un runtime GPU o un indice associativo.
