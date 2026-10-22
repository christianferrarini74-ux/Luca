# Modello, lettura obbligatoria e convivenza multi-GPU

> **Documento storico — non guida operativa attuale.** Specifiche, default, risultati e passi successivi qui descritti appartengono alla fase registrata. Per ambito, API e comportamento vigenti leggere il [contratto attuale](28-contratto-utilizzo-memoria.md). Le evidenze originali sono conservate.

2026-10-22. [English](../../model-and-required-read.md).

## Modello scelto e caricamento

Il catalogo installato di LM Studio offre `qwen/qwen3.8-27b` Q4_K_M: 27B,
file da 16,52 GiB e supporto al contesto configurato. La CLI installata stima
26,56 GiB di memoria GPU con 70.000 token, offload completo e una predizione
parallela; caricamento completato in 55,52 secondi. Nessun download.
Il contesto caricato risulta 70.144 token per arrotondamento del backend;
il budget del prompt di Luca rimane 70.000.

Il confronto è con `google/gemma-4-e2b` Q4_K_M. Il catalogo lo indica come
**4,6B**: il nome E2B non dimostra che sia un semplice modello denso da 2B.
Confrontiamo due combinazioni modello/runtime, non isoliamo il solo numero
di parametri.

L'istanza Gemma esistente resta intatta: contesto caricato 131.072 e limite
parallelo quattro, contro uno per Qwen. Richieste sequenziali, stesso budget
Luca, temperatura, copia della Bibbia, domande e cronologia. Impostazioni di
caricamento, famiglie di modelli, tokenizer e gestione della grammatica differenti
limitano i confronti di latenza. Ragionamento non disabilitato forzatamente.
Configurazione dell'applicazione invariata.

La gestione è stata verificata sulla
[documentazione ufficiale di caricamento LM Studio](https://lmstudio.ai/docs/developer/rest/load)
e su `lms load --help` installato; le stime non sono allocazioni misurate.

## Politica esatta sotto esame

L'indice globale iniziale viene già consultato da Luca. La politica sperimentale
`required` **non** aggiunge una seconda ricerca generica: se esistono indirizzi
ma non ci sono letture effettive nel turno, limita lo schema delle azioni alle
aperture `open` legali. L'ID lo sceglie l'LLM e il Core normale lo valida.
Dopo una lettura tornano tutte le scelte. Senza candidati resta possibile
rispondere con conoscenza generale. Non significa leggere tutta la biblioteca
né garantire completezza: il primo nodo può essere sbagliato o insufficiente.

`free` e `required` usano la stessa Bibbia invariata. L'ordine si alterna tra
le domande; ogni esecuzione ha adapter, conversazione e database temporaneo nuovi.
La prova della cronologia obsoleta inserisce lo stesso dialogo precedente in
entrambi i casi. Nessuna risposta attesa passata al modello. Navigatore principale
non modificato.

```powershell
python -m luca_memory.model_memory_check --models google/gemma-4-e2b,qwen/qwen3.8-27b --case incomplete
python -m luca_memory.model_memory_check --models google/gemma-4-e2b,qwen/qwen3.8-27b --case updated,stale_history,conflict,general
python -m luca_memory.model_memory_check --models google/gemma-4-e2b,qwen/qwen3.8-27b --case generic_revision
```

Eseguire dalla cartella del progetto. La CLI usa modelli installati e il loro
stato di caricamento; non scarica dalla memoria altri modelli per forzare la
disposizione sulle schede.

## Hardware e misure

Tre RTX 5060 Ti da circa 16 GiB. Prima di Qwen la memoria usata sulle GPU 0/1/2
era 6.935/14/14 MiB; dopo il caricamento circa 14.440/551/13.011 MiB. Durante
la generazione Qwen si osserva attività sia sulla 0 sia sulla 2, per esempio
40%/44%. La GPU 1 contiene le allocazioni CUDA reali dei nodi di Luca, ma LM
Studio vi crea anche alcune allocazioni: non è dichiarata esclusiva.

Dimostriamo convivenza e lavoro multi-GPU, non uno specifico algoritmo tensor-
parallel o un'accelerazione. La giostra seleziona ancora **una GPU per sessione**:
non distribuisce i nodi fra tutte le schede. I contenuti letti diventano input
serializzato del modello, non integrazione semantica diretta fra VRAM o un
percorso peer-to-peer GPU.

Entrambe le politiche usano volutamente uno slot VRAM e uno RAM per rendere
visibile l'oblio. Budget in byte e token invariati. Un ciclo deterministico
separato apre i nodi 1–7 e poi ancora 1, controllando hash e rilascio dei buffer
CUDA. Avviene con entrambi i modelli residenti, non dimostra calcolo LLM
contemporaneo a ogni trasferimento. Le cache SQLite/sistema operativo restano
attive: è una prova di integrità/residenza, non di prestazioni del disco a freddo.

I rapporti `D:/Test/Luca/model-memory-check-*.json` registrano campioni GPU,
tutte le richieste e i token cumulativi del provider, letture, percorsi, eventi
di discesa RAM/SSD e trasferimenti fisici. Il tempo del turno esclude l'avvio
dell'adapter; quello complessivo lo include, ma non comprende il caricamento
iniziale del modello già residente. Non misuriamo energia elettrica o costo
monetario. Documenti piccoli e singole prove non dimostrano affidabilità generale
o scalabilità su biblioteche grandi.

Il contatore delle richieste riguarda le generazioni, compresa un'eventuale
risposta finale di fallback; chiamate HTTP di gestione e tokenizzazione sono
distinte e non vengono contate come generazioni.

## Risultati: 24 esecuzioni live

Evidenze:

- `D:/Test/Luca/model-memory-check-20261022-084939-505201.json`: ripristino, quattro esecuzioni.
- `D:/Test/Luca/model-memory-check-20261022-085358-131429.json`: revisione attiva, cronologia, conflitto e aritmetica, sedici esecuzioni.
- `D:/Test/Luca/model-memory-check-20261022-090205-117666.json`: definizione generale con corrispondenze lessicali sui titoli delle revisioni, quattro esecuzioni.

Nessun errore esecutivo/provider. Revisione umana, non voto lessicale:

| Prova | Gemma E2B | Qwen 27B |
| --- | --- | --- |
| Ripristino | Incompleto con entrambe le politiche; con obbligo legge allarme e limiti non pertinenti | Entrambe leggono allarme → ripristino → modalità, con due passi locali; procedura migliore, ma soglie finali non lette/esplicitate |
| Revisione Primula attuale | Entrambe rispondono per il laboratorio sbagliato | Entrambe leggono la revisione attiva di Primula e rispondono 1502 |
| Cronologia obsoleta | Libera legge 1502 ma apre con un «sì» errato sul mantenere la porta vecchia; obbligatoria legge solo l'indice e non trova il sostituto | Entrambe scartano la vecchia 502 e danno la nuova 1502 |
| Fonti equivalenti in conflitto | Entrambe leggono soltanto A e scelgono 2502 | Entrambe attraversano A → B localmente e riconoscono il conflitto irrisolto 2502/3502 |
| Aritmetica | Entrambe rispondono 42 senza leggere | Entrambe rispondono 42 senza leggere |

Il confronto cambia la diagnosi: esplorazione locale utile, aggiornamento
correttamente circoscritto e scoperta del conflitto compaiono con il modello
più grande e la **Bibbia originale**. I fallimenti del modello piccolo non
dimostrano che i percorsi di Luca non possano funzionare. Qwen però si ferma
ancora prima delle soglie nel ripristino: autonomia completa non risolta.
Non ha letto tutte le fonti archiviate/bozze: non è una certificazione completa
della gerarchia delle fonti né una prova diretta di conoscenza obsoleta nei pesi.

### Costo misurato di una lettura non necessaria

«Che cosa significa revisione di un documento?» trova titoli di revisioni
specifiche, ma non richiede fatti su IRIS-17. Entrambi i modelli liberi
rispondono senza aprire nodi. Con l'obbligo leggono un nodo e Qwen aggiunge
anche un esempio IRIS-17 non necessario.

| Modello / politica | Generazioni | Secondi del turno | Token totali provider |
| --- | ---: | ---: | ---: |
| Gemma libera | 1 | 6,655 | 2.227 |
| Gemma obbligatoria | 2 | 7,847 | 4.411 |
| Qwen libera | 1 | 60,597 | 2.914 |
| Qwen obbligatoria | 2 | 67,702 | 5.219 |

In questo caso controllato la lettura costa una generazione aggiuntiva:
2.184/2.305 token in più e circa 1,2/7,1 secondi per Gemma/Qwen. Sono osservazioni,
non costo fisso o garanzia di latenza. Quando Qwen legge già spontaneamente,
le due politiche spesso hanno lo stesso numero di chiamate. Sul conflitto,
libera impiega 122,6 s e obbligatoria 67,5 s con le stesse tre chiamate, ma
lunghezze di generazione molto diverse: non dedurne un'accelerazione generale.

Totali delle sei domande selezionate, non sei ripetizioni della stessa domanda:

| Modello / politica | Chiamate | Somma secondi dei turni | Token totali provider |
| --- | ---: | ---: | ---: |
| Gemma libera | 11 | 65,336 | 27.088 |
| Gemma obbligatoria | 13 | 75,247 | 32.206 |
| Qwen libera | 14 | 347,291 | 36.604 |
| Qwen obbligatoria | 15 | 319,108 | 38.207 |

Questa combinazione modello/runtime è sensibilmente più lenta su diverse
richieste. Impostazioni di generazione, compreso l'eventuale ragionamento,
conservate ai valori originali; tempo di ragionamento non isolato. Il
cambio di modello ha un effetto qualitativo maggiore del solo obbligo della
prima lettura. Accesso obbligatorio non garantisce selezione pertinente né
uso completo: mantenerlo sperimentale/configurabile, non dichiararlo risolutivo.

## Evidenza della giostra e pulizia finale

Nel primo ciclo deterministico di otto passi, sette richiami fanno scendere
nodi in RAM e sei li lasciano soltanto nell'archivio persistente: otto letture
dal database, otto upload CUDA e 23 download. Hash dei contenuti identici e
buffer CUDA posseduti interamente rilasciati. Anche il percorso autonomo di
Qwen sui tre nodi del ripristino produce discese RAM/SSD: il movimento fisico
si osserva nella navigazione, non solo nel ciclo separato imposto dal test.
I campioni del primo rapporto arrivano all'81% sulla GPU 0 e al 99% sulla 2;
sono misure del dispositivo, non attribuzione esclusiva a un processo.

Terminati i test, scaricato dalla memoria soltanto Qwen, caricato per questa
prova. Gemma e le sue impostazioni originali restano caricati. Memoria GPU
tornata ai 6.935/14/14 MiB iniziali, utilizzo zero nell'ultima lettura.
Config/Bibbia principali e memoria personale invariate. Verifiche automatiche:
254 test Python individuati (sette skip opzionali), 19 JavaScript, Ruff pulito.
