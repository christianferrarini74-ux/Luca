# Luca

[English](README.md) | [Italiano](README.it.md)

Fase 1.11 implementata: [famiglie canoniche, indici completi, navigazione LLM e manutenzione atomica](docs/it/fase-1-sinapsi/12-implementazione-memoria-navigabile.md).
La [specifica confermata](docs/it/fase-1-sinapsi/11-memoria-sinaptica-riorganizzabile.md) resta il riferimento concettuale.
Avvio: `python run_luca.py`; configurati `memory_planner: llm` e limiti esterni 50/45.
Test su Core, HTTP e CUDA reale. Resta da fare la prova del nuovo protocollo con l'LLM reale: LM Studio non era avviato durante lo sviluppo.

Ultima verifica: [sicurezza seed, contatori alias e trasferimenti GPU misurati](docs/it/fase-1-sinapsi/10-verifica-claude.md).

Milestone memoria fisica: [giostra SSD/RAM/GPU](docs/it/fase-1-sinapsi/09-memoria-fisica.md).
I nodi completi usano allocazioni CUDA reali, senza nuovi pacchetti Python.
La GPU configurata è la numero 1; scegliere un dispositivo disponibile in `config.yaml`.
Vedere la [verifica delle dipendenze](docs/it/dependency-audit.md); prova sintetica:
`python -m luca_memory.hardware_check`. La biblioteca reale sarà testata insieme.

Milestone precedente: [sviluppo della memoria, punti 1–5](docs/it/fase-1-sinapsi/08-roadmap-utilizzo-memoria.md).

Runtime attuale di Fase 1: [memoria sinaptica, politiche di ricerca e cruscotto](docs/it/fase-1-sinapsi/07-completamento-runtime.md).
Avvio: `python run_luca.py`; il cockpit attuale è servito da Python sulla porta 8765.
Gli esperimenti originari riportati sotto restano come contesto storico.

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

Il runtime predefinito usa l'adapter conversazionale Gemma locale. Avviare il
server locale di LM Studio: Luca individua il modello configurato e chiede a
LM Studio di caricarlo se è installato ma non ancora residente. Il key
predefinito è `google/gemma-3-1b`.

```powershell
python run_luca.py
```

Endpoint e modello sono configurati nella sezione `llm.runtimes` di
`config.yaml`. L'LLM risponde liberamente usando il contesto della memoria;
l'output strutturato viene usato solo quando Luca estrae una proposta di
memoria durevole. Impostare `runtime.language_adapter: rules` solo per i test
deterministici offline.

## Avviare il runtime completo di Luca

Il punto di avvio unico legge `config.yaml`, avvia il runtime Python, avvia il
frontend e apre automaticamente la dashboard nel browser. La GUI resta solo un
frontend: visualizza lo stato restituito da Luca e non contiene la logica della
memoria o del linguaggio.

Avviare il runtime completo dalla radice del repository:

```powershell
python run_luca.py
```

Avviare LM Studio prima di usare l'adapter conversazionale Gemma predefinito.
Luca seleziona e carica automaticamente il modello configurato:

```powershell
python run_luca.py
```

La dashboard chiama `http://127.0.0.1:8765/api` per la chat e gli snapshot del
runtime. Il backend resta l'unico componente autorizzato ad accedere alla
memoria di Luca e al connector LLM.

## Stato

Il milestone attuale comprende un percorso conversazionale LLM libero, un
recupero limitato dalla memoria a celle e archi, proposte di memoria controllate
e un fallback deterministico. Il lavoro successivo estenderà consolidamento e
recupero associativo senza spostare la proprietà della memoria nella GUI o nel
modello.
