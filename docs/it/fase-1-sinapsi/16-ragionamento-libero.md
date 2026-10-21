# Una bibbia, ragionamento libero e letture multiple

[English](../../reasoning-contract.md)

2026-10-21. Supera le precedenti politiche di prompt e il filtraggio delle
risposte, senza riscrivere la storia degli esperimenti.

## Chi contiene le istruzioni

`runtime.bible: bible.md` è l'unica fonte del messaggio di sistema per
navigazione, conversazione, interpretazione/richiamo storici e manutenzione.
File mancante o vuoto produce un errore: nessun prompt di politica o copia
interna viene sostituito silenziosamente. Il file viene letto a ogni chiamata,
quindi una sua modifica non richiede di riavviare il modello. Per cambiare
configurazione occorre ancora riavviare Luca. La
[traduzione inglese](../../bible.en.md) è solo documentazione.

Tutte le informazioni del runtime sono un messaggio utente JSON con
`operation`, `question` e i dati pertinenti (`state`, `memory`, `task`,
`constraints`, `user_identity`). Nessuna istruzione comportamentale viene
aggiunta dal codice al messaggio di sistema. Gli schemi restano contratti
eseguibili del protocollo, non prompt di personalità nascosti. Il feedback
riporta errori/stati tecnici, non indicazioni su cosa rispondere.

I vecchi prompt experimental/grounded restano come reperti storici, ma non
vengono caricati. Il campo storico `memory_policy` descrive ora l'ambito della
memoria nei dati: non seleziona un'altra bibbia. `runtime.user_identity`
sostituisce l'assunzione incorporata che l'utente sia Christian.

La bibbia consente inferenze, spiegazioni, ipotesi creative e conoscenza generale
insieme ai ricordi acquisiti. Distingue quando serve osservazione e inferenza
e permette di correggere risposte precedenti. Non contiene vocaboli specifici
di formaggi, asini o altri casi usati nei test.

## Nessuna censura semantica dell'output

Eliminata la cancellazione di frasi/righe in base a espressioni come “memoria
locale”, “Legami diretti”, presentazioni o didascalie. Il testo restituito non
viene riscritto per nascondere come il modello si è espresso. Risultati vuoti o
malformati del provider producono ancora errori, non risposte inventate.
I test che imponevano la censura ora verificano risposta inalterata e separazione
istruzioni/dati; conservati i controlli indipendenti su topologia e isolamento.

## Ragionamento e parametri di generazione

Il connettore non inserisce più `reasoning_effort: none` e
`chat_template_kwargs.enable_thinking: false`. Con `generation: {}` si applica
il comportamento predefinito del provider: questo non certifica che il singolo
modello abbia effettivamente ragionato internamente. Le opzioni specifiche del
provider possono essere dichiarate nell'agente configurato:

```yaml
generation:
  reasoning_effort: high
  chat_template_kwargs:
    enable_thinking: true
```

Usare solo opzioni supportate dal provider/modello. `generation` non può
sovrascrivere indirizzi, messaggi, schema, streaming, temperatura o budget di
output controllato. La temperatura resta esplicitamente configurata a `0.0`:
migliorare l'uso della memoria non equivale ad aumentare la casualità.

Resta la finestra totale di 70.000 token. Navigazione e manutenzione hanno
8.192 token di output ciascuna nel file del progetto; la conversazione 4.096.
Interpretazione e richiamo storici sono configurabili separatamente a 1.024,
in sostituzione dei tetti incorporati 160/80. Eliminato il taglio silenzioso
delle domande di richiamo a 2.000 caratteri. `synaptic.search_query_characters`
controlla esplicitamente le query di ricerca generate e l'API, non tronca la
domanda dell'utente. Le riserve di output comprendono il lavoro di generazione
che il provider vi contabilizza: comportamento e latenza vanno misurati.

## Leggere, confrontare, rispondere

Il navigatore mantiene un `ReadingWorkspace` del turno con contenuti realmente
letti e rubrica completa di ogni nodo. Spostare il focus non elimina tutte le
letture precedenti del turno. Lo spazio è limitato da `memory_limit`; quando
serve, le letture più vecchie escono e vengono elencate in `omitted_ids`.
I contenuti possono essere estratti entro `per_node_limit`; le rubriche non
vengono tagliate silenziosamente. Sono dati temporanei del prompt in memoria
CPU, non un quarto livello persistente o una nuova copia sempre residente
della biblioteca. Payload fisici e trasferimenti della giostra restano invariati.

Ogni successiva decisione di navigazione vede le letture disponibili. L'azione
`answer` può contenere direttamente la `response` finale, generata con le
stesse letture e rubriche: nessun secondo risponditore perde il lavoro svolto.
Se un adattatore restituisce soltanto l'azione, per compatibilità con test o
interfacce precedenti, la chiamata conversazionale riceve comunque lo spazio
delle letture e la stessa bibbia.

Ogni azione ha un ramo dello schema: aprire richiede la sorgente corretta e un
ID appartenente a quella sorgente; rispondere richiede decisione sull'uso della
memoria e testo della risposta. Questo corregge un'ambiguità emersa dal vivo:
la mancanza di `source` causava aperture respinte ripetutamente. I candidati
globali rimangono disponibili dopo uno spostamento locale, per confrontare
altri risultati senza una nuova ricerca inutile. Il Core non sceglie comunque
gli obiettivi semantici e non obbliga a usare ogni candidato.

Quando un indirizzo è disponibile sia globalmente sia nella rubrica rapida,
lo schema offre una sola volta il percorso locale, senza duplicare l'indirizzo.
Questo conserva la navigazione sinaptica senza scegliere quale conoscenza usare.
La telemetria registra anche l'esposizione di letture effettive già uscite dalla
VRAM, senza promuovere i payload per fingere una residenza fisica inesistente.

Il raggruppamento usa assegnazioni direzione/ID → titolo, non liste indipendenti
di membri. Ogni indirizzo fornito può avere un solo titolo per direzione;
il Core converte titoli uguali in gruppi senza sceglierne il significato.
Indirizzi sconosciuti vengono respinti e limiti di grado/dimensione vengono
verificati prima di scrivere. Questo affronta le duplicazioni emerse nella
prima prova live senza aggiungere istruzioni comportamentali nel codice.

Budget dei passi, ID validi, revisioni, rubriche complete, limiti in token e
manutenzione atomica rimangono controlli di integrità/risorse. Esaurire i passi
produce lo stato `step_limit`, non un successo. La GUI mostra gli ID letti
distinti dalla residenza in VRAM. Il reset elimina letture e risposte pendenti.

## Verifiche

Test controllati su tutte le operazioni con sola bibbia nel messaggio di
sistema, output inalterato, bibbie personalizzate/mancanti/vuote, opzioni di
generazione configurabili, schemi per azione, letture multiple con un solo slot
fisico, oblio dello spazio di lettura e integrità della memoria esistente.

Prove riproducibili con database isolati e rilascio delle risorse CUDA:

```powershell
$env:LUCA_TEST_CUDA = '1'
$env:LUCA_TEST_LMSTUDIO = '1'
python -m unittest discover -s tests
python -m luca_memory.reasoning_check
python -m luca_memory.live_memory_check
```

La prova mirata con il modello reale ha aperto il nodo 2 e richiamato
correttamente il fenomeno in montagna e il suo collegamento esplicito al volo
degli asini. Entrambe le risposte sono state prodotte direttamente durante la
navigazione. È evidenza per quel caso, non una dichiarazione di risoluzione
delle allucinazioni o di ogni difetto di navigazione. Gli esiti delle prove
complete sono registrati sotto. Le prove non
riavviano l'applicazione dell'utente e non modificano il suo database personale.

### Risultati e limiti ancora aperti

206 test superati con `LUCA_TEST_CUDA=1` e `LUCA_TEST_LMSTUDIO=1`.
La ripetizione del dialogo è registrata in
`D:/Test/Luca/reasoning-live-20261021-191230.json`: **7/8 turni valutati superati**;
saluto e preferenze personali sono conservati per revisione, non conteggiati.
Richiamato il fenomeno in montagna, conservato il collegamento causale agli
asini, letti insieme i nodi 2 e 4 per la domanda sui nidi.
L'ultimo “c'è dell'altro?” non ha esplorato il nodo 5. Anche una ripetizione
mirata con la successiva indicazione generale sull'esplorazione si è fermata
presto. Rimane un limite di pianificazione del modello, non dichiarato risolto
dalla maggiore libertà di ragionamento.

La prima prova estesa (`phase11-live-20261021-191125.json`) ha dato 4/8:
un timeout, un percorso globale dove era richiesto quello locale e proposte
di gruppi duplicati. Dopo le correzioni del protocollo, la prova isolata di
manutenzione ha prodotto 17 membri entranti Astronomia, 17 uscenti Botanica e
17 uscenti Geologia: grado **51 → 3**, ripristino a **51**, nuovo raggruppamento
in inattività riuscito.

La prova completa successiva (`phase11-live-20261021-192755.json`) ha dato 7/8:
l'unico controllo fallito pretendeva il cursore ancora sul padre dopo averne
letto l'indice, benché l'indice restasse nello spazio delle letture mentre
il cursore passava a una parte della famiglia. Ora il controllo richiede
lettura effettiva del padre, identità canonica della famiglia e nomi corretti
delle sezioni, non una posizione artificiale del cursore. Test dedicati
respingono padre non letto e cursore estraneo.

Ultima prova completa seriale: `D:/Test/Luca/phase11-live-20261021-193004.json`,
**8/8**. Superati ingresso globale, parti della famiglia, percorso esterno
locale, richiamo spontaneo, aggiornamenti residenti, conoscenza generale,
raggruppamento/ripristino manuale e raggruppamento in inattività; risorse
rilasciate. In quest'ultima esecuzione la risposta sull'indice è arrivata
restando sul padre, soddisfacendo anche il vecchio controllo del cursore.
Questo esito non cancella il distinto turno di esplorazione fallito nel dialogo.

Le prime verifiche concorrenti di generazione hanno mostrato ritardi elevati
e un timeout da 180 secondi; nelle successive chiamate seriali la navigazione
ha richiesto circa 3–6 secondi. Sono osservazioni, non un benchmark controllato.
Il ragionamento predefinito può costare tempo e token di output: non limitarlo
con opzioni nascoste non garantisce rapidità o accuratezza dei fatti.

Chiudere l'applicazione attuale con **Esci**, poi eseguire `python run_luca.py`
per attivare adattatore e configurazione nuovi. Non avviare una seconda istanza
sopra quella esistente. Il modello in LM Studio può rimanere caricato.
Non sono state installate nuove dipendenze Python.
