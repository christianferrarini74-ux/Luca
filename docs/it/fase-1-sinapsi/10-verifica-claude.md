# Fase 1.10 — Consolidamento dopo la verifica di Claude

> **Documento storico — non guida operativa attuale.** Specifiche, default, risultati e passi successivi qui descritti appartengono alla fase registrata. Per ambito, API e comportamento vigenti leggere il [contratto attuale](28-contratto-utilizzo-memoria.md). Le evidenze originali sono conservate.

Data: 2026-10-19

[English](../../review-hardening.md)

Ambito: verificare la proposta di Claude sull'hardware locale, preservare la
conoscenza personale e correggere costi misurati senza nuove dipendenze né Cesare.
I dati sono sintetici e temporanei, nella directory configurata per i test.

## Identità e topologia del seed

I metadati del seed includono ora un'impronta SHA-256 della mappa canonica
slug-ID e dell'insieme degli archi orientati. L'ordine dei nodi conta perché
determina gli ID; l'ordine della lista degli archi e le sue ripetizioni identiche
non cambiano il grafo. L'impronta è strutturale, non riguarda il testo modificabile
della conoscenza o le aggiunte personali.

I nuovi eventi seed salvano versione e impronta. L'apertura controlla entrambe
e rifiuta strutture incompatibili senza rigenerare o riscrivere il database.
La stessa versione non autorizza più nodi seed riordinati, aggiunti o rimossi.
I nodi personali oltre il seed restano ammessi, indipendentemente dal totale.
Slug duplicati/vuoti ed estremi degli archi sconosciuti sono rifiutati prima
che il caricamento sperimentale esplicito possa cancellare qualcosa.

Per gli eventi precedenti privi d'impronta si verifica lo slug memorizzato a
ciascun ID atteso, senza aggiornare l'evento. Non inventiamo un'impronta storica:
la topologia originaria non è dimostrabile da una biblioteca che può aver
legittimamente acquisito o perso archi. Il controllo legacy delle identità è
quindi meno forte del confronto con un'impronta salvata all'origine.

I test coprono seed invariato, ordine degli archi, aggiunta/rimozione/riordino
dei nodi e modifica degli archi a versione invariata, accettazione/rifiuto legacy
senza scritture, crescita personale e conservazione con seed non valido.
Anche cambiare versione richiede una migrazione esplicita o un database
sperimentale separato: non ordina la sostituzione della conoscenza esistente.

## Ordinamento alias materializzato ed esatto

`cells_by_alias` legge i contatori per cella da `cell_degrees` invece di aggregare
tutti gli archi incidenti a ogni ricerca. Una migrazione transazionale aggiunge
le colonne, le inizializza e soltanto dopo crea i trigger. Gli indici ordinati
degli archi vengono creati dopo l'aggiunta delle colonne usage negli schemi legacy.

Diversamente dal massimo storico proposto, la recenza rimane il massimo esatto
degli archi incidenti ancora presenti. Cancellare l'arco più recente o ridurne
il timestamp può quindi cambiare il risultato come prima. Ogni aggiornamento
legge le due teste degli indici ordinati per cella, senza scansioni dell'hub.
Inserimento, aggiornamento e cancellazione mantengono i contatori senza dipendere
dall'ordine dei trigger dei gradi. Un auto-collegamento contribuisce una sola
volta all'utilizzo, come nel vecchio join `OR`, ma resta un grado entrante e uno
uscente. Gli estremi sono indirizzi immutabili: per cambiarli si rimuove e
inserisce l'arco.

I test confrontano contatori e graduatoria con l'aggregazione originale dopo
100 operazioni casuali riproducibili, oltre a pareggi, celle isolate, inserimenti
con utilizzo già valorizzato, auto-collegamenti, rollback, cancellazione del
massimo, timestamp ridotti, schemi vecchi e riaperture senza doppi conteggi.

## Benchmark locale degli alias

`python -m luca_memory.review_benchmark --mode aliases --repeats 15`

Database temporaneo su D:, 500.000 celle sintetiche, hub con 100.000 archi e una
cella isolata con lo stesso alias. Due riscaldamenti e 15 letture misurate.
La query di riferimento è quella originale; il percorso attuale costruisce
anche gli oggetti Cell.

| Ricerca | Mediana | p95 |
| --- | ---: | ---: |
| Aggregazione originale | 43,491 ms | 44,294 ms |
| Contatori materializzati | 0,0166 ms | 0,0205 ms |

Su 100 aggiornamenti in una transazione aperta, mediana SQL di 0,00520 ms con
manutenzione e 0,00175 ms senza: circa 0,00345 ms aggiuntivi. Il benchmark
disabilita i trigger solo nel database usa e getta e annulla la transazione
dopo la misura. Non sono tempi di commit/fsync o migrazione iniziale, né una
garanzia prestazionale generale.

## Trasferimenti GPU: prima misurati, poi ridotti

Il costo iniziale non era trascurabile, quindi siamo intervenuti. DeviceSlot
riusa un'allocazione soltanto se dimensione serializzata e SHA-256 coincidono
con il payload verificato. Il rilascio esclude le allocazioni riusate. Cambiare
i metadati di richiamo cambia il payload e richiede ancora un upload. Le nuove
allocazioni conservano verifica di andata/ritorno; le letture controllano l'hash.
I test coprono riuso del puntatore, modifica dei metadati ed errore su un upload
vicino senza liberare il puntatore riusato.

Non abbiamo aggiunto una cache host per turno con regole d'invalidazione.
La componente connessa usa soltanto ID e metadati degli archi, senza leggere
payload. Il contesto scarica soltanto i nodi aperti da esporre; la risposta
deterministica legge il solo focus, non tutti i nodi. Eliminiamo lavoro inutile
alla fonte senza trattenere una seconda cache host. Gli snapshot del cruscotto
continuano a leggere i nodi e i relativi trasferimenti restano visibili.

`python -m luca_memory.review_benchmark --mode turns --repeats 15`

Cinque nodi sintetici, stesso dialogo di cinque domande, due dialoghi di
riscaldamento, cinque slot, budget attivo di 16 MB e caldo di 32 MB, GPU 1.
Il budget maggiore permette di contenere gli stessi cinque nodi completi da
1,65 MB nei due backend: è un parametro del benchmark, non una modifica al
`config.yaml`. Prima: cinque dialoghi misurati, 25 turni per caso; dopo: quindici,
75 turni. Hash dei contesti esposti e tracce di richiamo coincidono fra HOST/CUDA.
L'adapter è deterministico e non chiama LLM. Si misurano planner, storage,
serializzazione e preparazione del prompt, non importazione seed, creazione
iniziale del contesto CUDA, inferenza, HTTP o cruscotto.

| Byte per nodo | Backend | Prima mediana / p95 | Dopo mediana / p95 |
| --- | --- | ---: | ---: |
| 64.000 | HOST | 2,837 / 3,335 ms | 2,531 / 2,961 ms |
| 64.000 | CUDA | 6,145 / 6,559 ms | 2,372 / 2,801 ms |
| 1.650.000 | HOST | 81,471 / 83,225 ms | 71,512 / 74,164 ms |
| 1.650.000 | CUDA | 152,414 / 154,221 ms | 54,086 / 55,440 ms |

Nella prova CUDA passa da 3 upload/26 download per turno a 1/6. Per i nodi da
1,65 MB i download scendono da circa 42,9 MB a 9,9 MB per turno. Il riferimento
HOST svolge ancora un diverso lavoro di serializzazione/compattazione: questi
risultati non dimostrano superiorità generale CUDA o qualità sulla biblioteca
reale. Giustificano la rimozione di questa ridondanza conservando la giostra
fisica. Sono misure locali su un campione limitato, non soglie prestazionali nei
test automatici. `--mode all` esegue entrambe le prove.

## Verifiche e confini

105 test superati con CUDA reale, comprese regressioni su migrazioni e riuso
delle allocazioni. L'esecuzione ordinaria salta i tre test hardware espliciti.
Nessun pacchetto installato e nessuna apertura del database personale.
La biblioteca reale sarà verificata insieme a Christian; Cesare resta escluso.

Una prova live separata con il modello LM Studio configurato e database seed
temporaneo ha mantenuto i focus 7 → 7 → 19 → 14 nelle quattro domande sui
sommergibili, con risposte pertinenti non vuote e rilascio di tutti i buffer CUDA.
Non trasforma il benchmark sintetico dei tempi in un benchmark d'inferenza.
