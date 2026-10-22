# Luca

[English](README.md) | [Italiano](README.it.md)

Confronto modelli: [sonno con Gemma 26B A4B](docs/it/fase-1-sinapsi/31-confronto-sonno-gemma26.md).
Quattro prove: nessun gruppo tematicamente misto, ma tre riduzioni insufficienti rifiutate; il solo cambio di modello non completa la manutenzione autonoma.

Correzione manutenzione: [arresto all'obiettivo configurato](docs/it/fase-1-sinapsi/30-arresto-riorganizzazione-obiettivo.md).
Applicati solo i gruppi interi necessari; gli archi dei gruppi scartati restano diretti.

Integrazione: [contratto per produttori e utilizzatori della memoria](docs/it/fase-1-sinapsi/28-contratto-utilizzo-memoria.md).
Nodi, archi, famiglie, budget, modifiche atomiche, API ed esempio eseguibile.

Verifica del sonno: [worker reale e simulazione dei guasti](docs/it/fase-1-sinapsi/29-verifica-riorganizzazione-sonno.md).
Struttura/riapertura/ripristino verificati; una proposta reale mista mostra il limite del raggruppamento semantico.
Luca gestisce la memoria; i contenuti e la loro suddivisione sono prodotti esternamente. Niente costruzione di biblioteche.

Prova con obiettivo esplicito: [ripristino completo senza cambiare la visibilità dei nodi](docs/it/fase-1-sinapsi/27-ripristino-obiettivo-esplicito.md).
Due nuove prove Qwen leggono le soglie mancanti e completano la procedura; non è una garanzia generale.

Indagine successiva: [chiedere a Luca perché si è fermato](docs/it/fase-1-sinapsi/26-intervista-arresto-lettura.md).
Autovalutazione nella stessa sessione confrontata con le letture, non assunta come prova causale.

Confronto misurato: [Qwen 27B, lettura obbligatoria e giostra in ambiente multi-GPU](docs/it/fase-1-sinapsi/25-modello-lettura-obbligatoria-multi-gpu.md).
24 esecuzioni live: miglioramenti, limiti residui e costi per chiamata documentati.

Indagine: [lettura autonoma e attualità della conoscenza](docs/it/fase-1-sinapsi/24-autonomia-e-attualita-memoria.md).
Profili sperimentali separati; completamento autonomo non ancora affidabile.

Esperimento controllato: [manuale IRIS-17, domande isolate e tracce di lettura](docs/it/fase-1-sinapsi/23-esperimento-documento-controllato.md).

Biblioteca reale: [memoria iniziale vuota, esempi sintetici separati](docs/it/fase-1-sinapsi/22-avvio-biblioteca-reale.md).
Chiudere e riavviare Luca per usare il nuovo database; quello precedente è conservato.

Manutenzione CI: [controlli GitHub riproducibili](docs/it/fase-1-sinapsi/21-controlli-github-actions.md),
con lint e test Python/JavaScript su runner Ubuntu e Windows espliciti.

Manutenzione: [semplificazione e commenti interni in inglese](docs/it/fase-1-sinapsi/20-revisione-codice-e-commenti.md).
235 test Python con CUDA/tokenizer reali e 19 JavaScript superati. Nessuna modifica
a comportamento, dipendenze, configurazione o Bibbia. Riavviare Luca ordinatamente
e aggiornare la pagina per caricare il codice rivisto.

Correzione mappa: [centratura dopo trascinamento e cambio vista](docs/it/fase-1-sinapsi/19-correzione-centratura-mappa.md).
10 test JavaScript e 219 test Python superati. Aggiornare la pagina per
caricare il frontend corretto, senza riavviare il server.

Novità: [mappa interattiva della memoria](docs/it/fase-1-sinapsi/18-mappa-grafica-memoria.md),
viste globale/focus, famiglie espandibili, colori dei livelli e richiamo separato
dall'esplorazione. Nessuna nuova dipendenza. 219 test Python con CUDA/tokenizer
reali e 5 test JavaScript superati. Riavviare Luca ordinatamente per le nuove API.

Ultima revisione della Bibbia: [memoria acquisita e conoscenza generale](docs/it/fase-1-sinapsi/17-bibbia-conoscenza-integrata.md).
210 test automatici superati con tokenizer nativo e CUDA reale; nuovo dialogo
di integrazione 8/8 nei controlli lessicali/letture. Stile e dettagli aggiunti
restano imperfetti: vedere il resoconto. Iniziare una nuova conversazione;
la Bibbia viene riletta a ogni richiesta senza riavviare Luca.

Contratto attuale: [bibbia unica, nessun filtro semantico e letture multiple](docs/it/fase-1-sinapsi/16-ragionamento-libero.md).
Istruzioni solo da `runtime.bible`; il ragionamento del modello non viene più
disabilitato forzatamente. Opzioni di generazione e budget operativi nel file YAML.
206 test automatici superati con tokenizer nativo e CUDA reale.
Prova sintetica live finale: 8/8. Dialogo sulla pioggia: 7/8; resta inaffidabile
l'esplorazione spontanea ulteriore. Dettagli e limiti nel resoconto.

Contesto attuale: [70.000 token del modello, configurabili in YAML](docs/it/fase-1-sinapsi/15-contesto-in-token.md).
Conteggio nativo LM Studio, cronologia limitata dai token senza tetti fissi agli
scambi; memoria fisica sempre in byte. Nessuna dipendenza aggiuntiva. 182 test
superati con tokenizer reale e CUDA. Riavviare Luca con `python run_luca.py`.

Fase 1.11 implementata: [famiglie canoniche, indici completi, navigazione LLM e manutenzione atomica](docs/it/fase-1-sinapsi/12-implementazione-memoria-navigabile.md).
La [specifica confermata](docs/it/fase-1-sinapsi/11-memoria-sinaptica-riorganizzabile.md) resta il riferimento concettuale.
Avvio: `python run_luca.py`; configurati `memory_planner: llm` e limiti esterni 50/45.
Ultimo intervento: [ingresso nella memoria e dialogo](docs/it/fase-1-sinapsi/14-ingresso-memoria-e-dialogo.md). Suite automatica: 158 test superati, anche CUDA reale; prova sintetica live: 8/8. Nel dialogo completo restano spiegazioni inventate e problemi di provenienza/stile: accettazione non conclusa. Conservate le [evidenze precedenti](docs/it/fase-1-sinapsi/13-verifica-live-lmstudio.md).

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
al servizio di un modello linguistico. L'LLM contribuisce con ragionamento e
conoscenza generale; Luca gestisce la memoria navigabile. Ogni tesi importante deve
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

Luca espone famiglie canoniche, rubriche complete di primo grado, modifiche
atomiche, livelli fisici di memoria e riorganizzazione protetta nel sonno.
Chat e cruscotto sono utilizzatori di prova. Contratto d'integrazione e verifiche
controllate del sonno definiscono la consegna attuale; qualità semantica dei
raggruppamenti non garantita. Produzione dei contenuti, importazione documenti,
suddivisione automatica, biblioteche e integrazione Cesare sono fuori ambito.
Bibbia chiusa salvo problemi di contesto/interfaccia che impediscano l'uso della memoria.
