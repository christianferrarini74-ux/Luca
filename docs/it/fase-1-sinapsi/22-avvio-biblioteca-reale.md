# Separazione della biblioteca reale dagli esperimenti sintetici

> **Documento storico — non guida operativa attuale.** Specifiche, default, risultati e passi successivi qui descritti appartengono alla fase registrata. Per ambito, API e comportamento vigenti leggere il [contratto attuale](28-contratto-utilizzo-memoria.md). Le evidenze originali sono conservate.

2026-10-22. [English](../../real-library-start.md).

La configurazione principale usa ora `seed/library_empty_v1.json` e il nuovo
database `D:/Test/Luca/luca_library.sqlite`. Il grafo iniziale ha zero nodi e
zero archi: non sostituiamo gli esempi assurdi con una raccolta inventata.
`memory_policy` passa a `grounded`; Bibbia, ragionamento del modello, budget
e giostra fisica restano invariati. Questa impostazione è un metadato, non
un nuovo filtro sulle risposte.

Il precedente database `D:/Test/Luca/luca_v1.sqlite` rimane intatto, comprese
eventuali aggiunte fatte durante gli esperimenti. Il seed sintetico resta
nel repository per regressioni e prove live su archivi temporanei separati.
I vecchi resoconti restano evidenze storiche, non conoscenza attiva.

Un processo già avviato continua a usare database e cronologia precedenti.
Chiudere con **Esci**, rilanciare `python run_luca.py` e iniziare una nuova
conversazione. Il nuovo database viene creato a quell'avvio, non tramite una
migrazione del processo in esecuzione. Non copiarvi sopra il vecchio database.

Le regressioni verificano navigazione a vuoto con adapter programmato,
conservazione delle conoscenze aggiunte dopo reset/riavvio e rifiuto di
inizializzare un archivio sperimentale con il nuovo seed. Sono verifiche
strutturali, non una nuova valutazione conversazionale del modello.

Il passo successivo è scegliere insieme la prima fonte reale, costruire nodi
titolo/indice/capitoli e riferimenti a fonte/pagine, quindi confrontare le
risposte con la fonte. Questo intervento non realizza importazione PDF o
strutturazione automatica dei documenti.
