# Luca: protocollo sperimentale

## Metodo

Ogni componente nasce come esperimento controllato. Prima di considerarlo parte di Luca definiamo dati, risultato atteso, baseline di confronto, budget delle risorse e condizione di fallimento.

## Esperimento 1 — navigazione diretta del grafo

**Tesi:** le celle collegate da archi indirizzati possono essere recuperate ed espanse rapidamente su scala.

**Dati:** celle sintetiche e archi diretti bilanciati.

**Operazioni:** lookup esatto `(A,B)`, scansione uscente `A:*`, scansione entrante `*:B` ed espansione locale delimitata da uno o più semi.

**Misure:** velocità di ingestione, latenza di lookup e scansione, latenza del pensiero locale, dimensione del contesto RAM, dimensione su disco e correttezza dei percorsi restituiti.

**Superamento:** gli indici diretti restituiscono il vicinato atteso completo e l'espansione resta entro il budget dichiarato. I risultati prestazionali vengono registrati senza inventare un target fisso prima di osservare la macchina.

## Esperimento 2 — indirizzo associativo solo CPU

**Tesi:** un indirizzo appreso dal grafo e dalla storia di attivazione di Luca può recuperare candidati lontani utili meglio della sola navigazione diretta.

**Confronto:**

```text
A. solo grafo diretto
B. grafo diretto + indirizzo associativo appreso
```

Misurare recall@k, precision@k, falsi salti, tempo di aggiornamento dell'indice, uso disco/RAM e latenza. Se B non supera A o introduce troppi falsi salti, si modifica il segnale di apprendimento invece di nascondere il risultato con un modello più grande.

## Esperimento 3 — politica dei livelli senza dipendenza GPU

Eseguire la baseline CPU variando indipendentemente capacità del contesto RAM e del focus VRAM simulato. Misurare percorsi rilevanti conservati, tempo di espansione, dimensione del focus, espulsioni e stabilità del risultato.

## Esperimenti 4 e 5 — una o più GPU

Portare su GPU una singola operazione provata sulla CPU, alimentando entrambe con snapshot identici. Per più GPU, dividere rami indipendenti e consolidare attraverso un solo processo CPU/RAM. Il successo richiede parità semantica, miglioramento misurato dopo i trasferimenti e tracce riproducibili.

## Registrazioni obbligatorie

Ogni esperimento deve salvare o stampare seme dati, configurazione, budget, versione software, tempi, risorse, risultato atteso, risultato effettivo e decisione derivata dalle evidenze.
