# Chiedere a Luca perché si è fermato nella lettura

2026-10-22. [English](../../memory-stopping-interview.md).

## Protocollo

Qwen3.8 27B Q4_K_M, Bibbia originale e documento controllato IRIS-17 invariati.
Ogni prova indipendente mantiene **una sola sessione reale** per tre turni:

1. Domanda originale sul ripristino dopo E42.
2. Domanda neutra: ritiene di aver risposto completamente alla prima domanda?
   C'è qualcosa che avrebbe dovuto approfondire?
3. Se nel primo turno non ha letto il capitolo del sensore, si comunica quel
   fatto osservato e si chiede perché si sia fermato; se l'ha letto, si chiede
   cosa lo abbia portato ad approfondirlo.

La terza domanda si riferisce sempre al turno **iniziale**, anche se la domanda
neutra ha già prodotto nuove letture. Non afferma falsamente che una lettura
manchi e non fornisce soglie, conteggi di campioni o ID da aprire. Nessun richiamo
scelto dal programma e nessuna politica di lettura obbligatoria.

```powershell
python -m luca_memory.memory_interview_check --model qwen/qwen3.8-27b --repeat 2
```

Eseguire dalla cartella del progetto. Database temporanei e copia temporanea
della Bibbia originale. Uno slot VRAM e uno RAM, come nel precedente confronto
dei modelli, stessi budget di token e dispositivo CUDA configurati. Applicazione
principale e biblioteca personale non modificate.

## Evidenze e interpretazione

`D:/Test/Luca/memory-interview-*.json` registra risposte, letture effettive,
azioni, cronologia reale prima di ogni turno e stato completo della navigazione
mostrato al modello, oltre a tempi e consumi di generazione. I turni conclusi
restano nel rapporto parziale anche se un turno successivo fallisce.

L'app conserva tra i turni messaggi utente/assistente, non una trascrizione
di tutte le precedenti scelte di navigazione. Durante un turno lo stato espone
letture e ID visitati; il turno nuovo ricrea lo spazio di lettura includendo
inizialmente il focus corrente. Chiedere «perché non l'hai aperto?» produce
quindi una spiegazione retrospettiva a partire da cronologia/stato disponibili,
non accesso a un registro causale privato conservato. La domanda esplicita
fornisce un fatto osservato sulla mancata lettura; quella neutra no.

Confrontare le dichiarazioni con rubriche/indirizzi e contenuti effettivamente
ricevuti. Distinguere ammissione d'incompletezza, motivazione dell'arresto,
eventuale dichiarazione di impossibilità d'accesso e apertura reale del capitolo
mancante. Una spiegazione fluente da sola non dimostra il meccanismo. Nuova
conoscenza acquisita dopo una domanda umana è evidenza utile, ma non completamento
spontaneo della richiesta iniziale.

L'intervista non modifica pesi, API di memoria o Bibbia e non stabilisce se
il modello percepisca soggettivamente il contenuto come «conoscenza propria».

## Prima intervista: spiegazione e comportamento effettivo

Riprodotta la prima risposta incompleta: legge allarme (4), ripristino (5) e
modalità (2), ma non le soglie del sensore (3). Alla fine rimanda alle condizioni
di apertura senza esplicitarle.

Alla domanda neutra riapre il ripristino, riconosce di aver risposto solo in
parte e individua il capitolo 2 / le soglie come parte mancante. Non lo apre:
in quel turno le letture sono 2 e 5.

Alla domanda esplicita dichiara di aver interpretato il compito come procedura
immediata di ripristino dopo E42. Nella sua spiegazione, il capitolo non serviva
alla cancellazione dell'allarme, ma serviva a completare la risposta sull'apertura
della valvola. Ammette l'incompletezza e non apre il capitolo 2: nel turno legge
solo il nodo 5. Le domande chiedono autovalutazione/motivazione, non l'esecuzione
esplicita della procedura mancante: la mancata lettura non è di per sé rifiuto
di un comando di lettura.

Questo sostiene l'ipotesi di **perimetro del compito/criterio di arresto**, non
dimostra la causa interna: l'obiettivo effettivo potrebbe essere diventato
«cancellare l'allarme» invece di «tornare a irrigare». Non emerge un'impossibilità
tecnica dimostrata: lo stato effettivamente ricevuto sul nodo modalità espone
il sensore come destinazione locale legale. Il modello non dichiara un divieto
di accesso né di non poter usare la memoria come conoscenza acquisita.

Un esperimento discriminante successivo dovrebbe esplicitare in linguaggio
ordinario l'esito desiderato (effettiva apertura, comprese le condizioni
necessarie), senza nominare il capitolo, dare soglie o imporre percorsi.
Il presente protocollo di tre turni non esegue questa prova ulteriore.

## Ripetizione ed evidenza salvata

Rapporto: `D:/Test/Luca/memory-interview-20261022-092111-026346.json`.
Due conversazioni indipendenti, sei turni utente totali, entrambe con lo stesso
arresto. Nella seconda legge inizialmente 4/5/2, durante l'autovalutazione
2/4/5, nella spiegazione esplicita soltanto 5; il nodo 3 non viene mai letto
in nessuna delle due prove. Nell'ultimo input di navigazione iniziale di entrambe,
il nodo 3 è tra le destinazioni locali legali `1,3,4,5`. La cronologia realmente
trasmessa all'inizio dei tre turni contiene 0, 2 e 4 messaggi: sono domande
successive nella stessa conversazione, non richieste isolate.

La seconda motivazione esplicita è:

> Perché ho dato per scontato che la tua domanda riguardasse solo il ripristino dopo E42, e il capitolo 4 che avevo letto bastava per quello. Non ho riconosciuto che “riprendere a irrigare” richiedesse anche le condizioni di apertura della valvola; in realtà sì, e avrei dovuto aprire il capitolo 2.

È coerente con la prima intervista, ma non è evidenza indipendente del processo
causale interno. Nessuna delle due descrive un divieto di accesso o un rifiuto
della conoscenza esterna.

Entrambe riconoscono la lacuna già alla domanda neutra, senza ricevere la soglia
mancante, ma non la colmano in questi turni esplicativi. La distinzione utile è
tra riconoscere una lacuna e attivarsi per colmarla; domande sulla spiegazione
non misurano da sole l'esecuzione di una richiesta esplicita di completamento.
Due prove sullo stesso documento non giustificano conclusioni di affidabilità
generale.

Tempi dei turni in secondi: prima prova 92,023 / 131,591 / 46,962; seconda
91,748 / 143,653 / 44,789. Nessun errore esecutivo; risorse rilasciate da entrambe
le sessioni. Qwen scaricato dalla memoria dopo la prova, Gemma originale intatto;
memoria GPU tornata ai 6.935/14/14 MiB iniziali. Suite: 258 test Python individuati
con esito positivo (sette skip opzionali), 19 JavaScript superati, Ruff pulito.
Nessuna modifica al comportamento dell'applicazione principale.
