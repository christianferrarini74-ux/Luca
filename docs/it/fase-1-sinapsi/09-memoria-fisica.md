# Fase 1.09 — Giostra sinaptica fisica

Data: 2026-10-19

[English](../../physical-memory.md) · [Verifica dipendenze](../dependency-audit.md)

Questo milestone supera il limite delle cache logiche delle Fasi 1.07 e 1.08.
L'obiettivo è trasferire realmente nodi completi, inizialmente piccoli o
sintetici. La biblioteca reale sarà verificata insieme a Christian.
L'integrazione con Cesare è esplicitamente esclusa.

## Contratto dei livelli

| Livello | Backend CUDA | Durata |
| --- | --- | --- |
| Disco / SSD | SQLite conserva nodi completi e grafo orientato. | Sopravvive a espulsione dalle cache e riavvio. |
| RAM | Oggetti Python contengono i nodi completi del parcheggio caldo. | Limiti sul numero di nodi e sul payload serializzato. |
| VRAM | Allocazioni esplicite `cuMemAlloc_v2` contengono i nodi serializzati completi, sezioni incluse. | Luca le libera durante espulsione, reset e arresto. |

In RAM il livello GPU conserva soltanto ID, puntatori, dimensioni e hash SHA-256,
non una seconda cache del contenuto. Planner, cruscotto e preparazione del prompt
ottengono copie temporanee tramite `cuMemcpyDtoH_v2`. Il caricamento usa
`cuMemcpyHtoD_v2` e verifica il ritorno effettivo dei byte prima di sostituire
le allocazioni precedenti. Ogni lettura controlla l'hash prima di decodificare.
L'LLM riceve ancora testo selezionato tramite connector: queste allocazioni non
sono pesi, cache KV o integrazione con il motore d'inferenza.

Un nodo presente in RAM evita il caricamento SQLite; un nodo in GPU viene letto
dall'allocazione. Altrimenti viene decodificato dal database e trasferito.
L'espulsione dalla GPU scarica il contenuto nel parcheggio RAM. Quando anche
questo livello trabocca, si elimina la copia residente: il contenuto persistente
è già su disco, quindi non si riscrive il documento a ogni espulsione.
Un successivo richiamo freddo lo carica nuovamente.

Il Core conserva tutte le decisioni su grafo, focus e LRU. Il backend GPU non
introduce nuove regole semantiche. Gli archi rimangono indicizzati in SQLite,
con metadati del grafo attivo in RAM: questo milestone trasferisce i payload
dei nodi, non gli indici o tutti gli oggetti del Core.

## Configurazione e dipendenze

```yaml
runtime:
  memory_backend: cuda
  gpu_device: 1
  vram_capacity: 5
  ram_capacity: 12
  vram_bytes: 8000000
  ram_bytes: 32000000
frontend:
  enabled: true
```

L'avvio resta `python run_luca.py`. Gli ordinali CUDA partono da zero. La macchina
attuale ha tre RTX 5060 Ti; è stata scelta la GPU 1 per separare queste allocazioni
dal processo d'inferenza attualmente sulla GPU 0. Su altre macchine scegliere
un ordinale disponibile in `config.yaml`. Non è implementato lo sharding multi-GPU.

PyYAML resta l'unico pacchetto Python esterno. Il collegamento usa `ctypes` della
libreria standard e il driver NVIDIA (`nvcuda.dll` su Windows, `libcuda.so.1` su
Linux). Per queste copie non servono CUDA Toolkit, PyTorch o CuPy. Windows/NVIDIA
è verificato su hardware; il percorso Linux non è stato provato su hardware.

`memory_backend: host` seleziona esplicitamente il riferimento CPU precedente,
segnalato come HOST dal cruscotto. Le vecchie configurazioni prive della chiave
mantengono quel valore di riferimento; il file del progetto seleziona CUDA
esplicitamente. Errori di inizializzazione, allocazione o copia CUDA non causano
mai un ripiego silenzioso su HOST.

## Limiti e gestione degli errori

- I payload CUDA completi non vengono sostituiti da estratti parziali. Un nodo
  singolo oltre `vram_bytes` viene rifiutato con un messaggio esplicito: occorre
  aumentare il budget, non troncare il nodo.
- Se il grappolo supera numero o byte disponibili, rimane il prefisso prioritario
  e gli altri nodi completi passano attraverso il parcheggio caldo. Un nodo oltre
  il budget RAM non viene trattenuto lì; la fonte rimane su disco.
- Si caricano e verificano le nuove allocazioni prima di sostituire quelle
  precedenti o rimuovere copie RAM. Errori di allocazione, copia o integrità
  liberano i buffer preparatori e preservano l'appartenenza precedente agli slot.
  Gli errori di rilascio o perdita del dispositivo sono esposti; non è implementato
  il recupero automatico dopo un reset del driver.
- La preparazione transazionale richiede temporaneamente VRAM aggiuntiva accanto
  alle allocazioni precedenti. Il budget limita il payload trattenuto, non il
  picco totale GPU. Contesti, granularità del driver e altri programmi consumano
  altra memoria. Il budget RAM non misura l'RSS del processo Python.
- Il riferimento al contesto primario viene attivato/ripristinato sul thread
  chiamante; l'API serializza il Core. Reset e arresto liberano i buffer e soltanto
  il riferimento al contesto posseduto da Luca, non le risorse dell'inferenza.
  Anche errori di avvio parziale o bind HTTP chiudono le risorse possedute.
- Le allocazioni GPU sono reali, ma WDDM e driver governano residenza fisica e
  paging. Non promettiamo VRAM bloccata e non paginabile. Analogamente, cache
  SQLite e sistema operativo possono evitare accessi fisici all'SSD a ogni lettura.

## Diagnostica

`GET /api/state` espone `physical_memory`: backend, GPU, numero e byte delle
allocazioni possedute, byte effettivamente copiati e numero delle operazioni,
memoria libera/totale riportata dal driver. Conta anche i caricamenti dei nodi
SQLite effettuati dalla giostra e i relativi payload serializzati; non è I/O
fisico del disco e non include altre query agli indici o al cruscotto.

Il cockpit mostra backend e GPU in evidenza e i trasferimenti nei controlli.
Anche la lettura degli snapshot scarica contenuti dalla GPU, inclusi nei contatori.
Una piccola allocazione può non cambiare i valori arrotondati di `nvidia-smi`:
conteggio puntatori/byte posseduti e memoria libera del dispositivo sono distinti.

## Verifiche riproducibili

```powershell
python -m unittest discover -s tests
$env:LUCA_TEST_CUDA = '1'
$env:LUCA_TEST_GPU = '1'
python -m unittest discover -s tests
python -m luca_memory.hardware_check
```

`hardware_check` legge la configurazione, ma non apre il database personale né
carica il seed. Crea un database temporaneo sotto la directory configurata e lo
elimina dopo la chiusura delle risorse. Trasferisce un capitolo sintetico di
1.650.000 byte, forza espulsioni GPU/RAM, lo ricarica dal disco e verifica gli hash.
L'output mostra contatori delle operazioni reali e rilascio finale.
`--device` cambia l'ordinale soltanto per questa verifica.

Verifica: 92 test superati con CUDA reale abilitato, di cui 89 portabili e tre
hardware. Coprono Unicode e sezioni, payload completi, espulsioni per numero/byte,
errori simulati di allocazione e corruzione, assenza di fallback, thread diversi,
riapertura del database, richiamo HTTP reale, reset, arresto e assenza di buffer
posseduti residui. Sintassi JavaScript e rendering mirato sono controlli separati.
Non si dichiara un audit visuale completo o un confronto prestazionale.

Avvio normale e reset non sostituiscono più la conoscenza quando cambia il numero
dei nodi. Una versione seed incompatibile produce un errore senza rigenerare il
database. Le funzioni esplicite di caricamento sperimentale del seed restano
distruttive e non sono migrazioni per biblioteche personali.

Passo successivo: verifica della biblioteca reale insieme a Christian. Durante
i test hardware di questo milestone il database personale non è stato aperto
o modificato.

Una prova live separata ha usato il modello LM Studio configurato e un database
sperimentale temporaneo con backend CUDA. Il dialogo dei sommergibili in tre
turni ha mantenuto il riferimento ai mezzi gialli prima di passare ai mezzi rossi
dei cani. Tutti i buffer di Luca sono stati liberati. È una verifica di
compatibilità, non una valutazione generale dell'LLM o della biblioteca reale.
