# Fase 1.07 — Completamento del runtime della memoria sinaptica

Data: 2026-10-19

Milestone successivo: [giostra fisica SSD/RAM/GPU](09-memoria-fisica.md).
I limiti delle cache logiche e del ripristino seed descritti sotto appartengono
alla Fase 1.07, non al backend CUDA e all'avvio non distruttivo attuali.

[English](../../synaptic-memory-runtime.md)

Questo documento registra il completamento del runtime di Fase 1. I documenti
precedenti restano testimonianze storiche. Il milestone riguarda l'utilizzo
della conoscenza articolata, non la sua acquisizione dalla conversazione.

## Richiamo e convergenza

Gli indirizzi orientati generano catene, famiglie di prefisso (`P:*`) e di
suffisso (`*:S`). Le ancore della domanda sono distinte da quelle ereditate
dalla conversazione. La convergenza cerca su SSD indipendentemente dal limite
di precaricamento. La modalità strict richiede tutte le ancore della domanda;
quella associativa ammette anche risultati parziali. La pertinenza precede
recenza e frequenza.

Per impostazione predefinita viene aperto soltanto il candidato migliore.
Le aperture multiple procedono dal meno al più pertinente, lasciando il
migliore al focus. Graduatoria, candidati aperti e alternative sono distinti.
VRAM e RAM sono cache logiche Python a capienza limitata: non è ancora presente
un'allocazione fisica sulla GPU. SSD conserva il grafo persistente.

## Ricerca rapida e completa

In `config.yaml`, impostare `runtime.memory_search_policy`:

- `fast` (predefinita): cerca prima fra i collegamenti più utilizzati e può
  fermarsi al ritrovamento di un candidato esatto. Se non ne trova, amplia
  la ricerca all'intero dominio pertinente.
- `complete`: disattiva la scorciatoia hot-first ed esamina il dominio completo
  delle famiglie richieste. Il numero di risultati restituiti resta limitato.

Un candidato esatto soddisfa i collegamenti richiesti; una ricerca limitata ai
candidati caldi non garantisce la migliore graduatoria globale. `search_scope`
e `ranking_is_global` espongono questa distinzione nell'API. Non rappresentano
una certificazione semantica. Attualmente la convergenza considera collegamenti
incidenti nelle due direzioni e l'ingresso linguistico usa alias espliciti,
con un massimo di tre ancore per domanda.

I contatori dei gradi sono aggiornati dai trigger SQLite e letti tramite indice,
evitando scansioni soltanto per contare gli archi. I tempi di selezione, query e
richiamo completo sono separati. `estimated_seed_edges` è una stima del lavoro
di generazione candidati, non una misura di pagine lette o I/O fisico.
`recall_ms` comprende selezione e query: i tre tempi non vanno sommati.

## Turni e apertura esplicita delle alternative

A ogni turno di chat l'esito della ricerca viene archiviato e rimosso dal
prompt corrente. VRAM, RAM, nodi aperti e grafo restano disponibili. Un vecchio
avvertimento di intersezione vuota non accompagna quindi domande successive.
L'ultima ricerca precedente rimane visibile come diagnostica storica.

Il pannello “Richiamo della memoria e alternative” mostra ambito, strategia,
candidati aperti, tempi e alternative. Il click richiede un'operazione al
backend: la GUI non esegue la selezione. Le alternative parziali sono indicate
come tali e richiedono un'apertura esplicita.

`POST /api/alternative`, con `{"node_id": 19}`, accetta soltanto nodi ancora
disponibili fra le alternative registrate. Il backend apre il nodo, sincronizza
il focus dialogico e lo rimuove dalle alternative. `POST /api/recall` resta il
richiamo manuale generale. Entrambi rimuovono gli avvertimenti correnti.

`GET /api/state` distingue `convergence` da `previous_convergence`. Una nuova
sessione azzera entrambi conservando la politica di ricerca configurata.

## Verifica e passi successivi

Eseguire `python -m unittest discover -s tests -v`. Le prove coprono candidati
freddi oltre il precaricamento, pertinenza e recenza, aperture multiple con cache
piccole, intersezioni vuote, ciclo del turno, contatori e fallback hot-first.
Il test del candidato freddo rinforza gli altri archi, evitando che l'ID del
bersaglio lo faccia rientrare accidentalmente nei primi risultati.
Le verifiche HTTP comprendono alternative, risorse statiche e arresto ordinato.

Verifica del 2026-10-19: superati 58 test automatici. Controllati sintassi
JavaScript e rendering dei dati, compresi escaping dei titoli e disabilitazione
delle alternative durante le richieste. Una conversazione HTTP reale con
`google/gemma-4-e2b` su LM Studio ha restituito risposte non vuote e spostato il
focus dalla flotta al sommergibile dei cani (nodo 19). È stato usato un database
temporaneo in `D:/Test/Luca`, rimosso dopo l'arresto; il database personale non
è stato aperto né ricaricato. È una verifica funzionale, non una valutazione
estesa della qualità delle risposte né un'ispezione visiva nel browser.

Il loader del seed rimane un sistema di ripristino dei dataset sperimentali,
non una politica di migrazione per una biblioteca personale crescente.
Budget di token, segmentazione dei documenti grandi, pianificazione semantica
e integrazione in Cesare appartengono ai milestone successivi. Questa versione
non dimostra equivalenza con un cervello né capacità hardware illimitata.
