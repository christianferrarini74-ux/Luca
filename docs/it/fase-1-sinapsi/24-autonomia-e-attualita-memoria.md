# Autonomia di lettura e attualità della conoscenza: indagine

> **Documento storico — non guida operativa attuale.** Specifiche, default, risultati e passi successivi qui descritti appartengono alla fase registrata. Per ambito, API e comportamento vigenti leggere il [contratto attuale](28-contratto-utilizzo-memoria.md). Le evidenze originali sono conservate.

2026-10-22. [English](../../memory-autonomy-investigation.md).

## Perimetro e diagnosi

Questa è un'indagine, non un rilascio. Bibbia principale, configurazione, schema
dei nodi, navigatore e database personali restano invariati. Le istruzioni
sperimentali sono in `experiments/`, con traduzioni documentali inglesi, e vengono
usate soltanto da sessioni temporanee. Nessuna nuova dipendenza runtime.

Il navigatore espone già rubriche locali complete, candidati globali, letture
effettive e indirizzi non letti; consente più aperture prima della risposta.
Nella precedente prova IRIS-17 il modello non esauriva gli otto passi: decideva
di rispondere prima. Non abbiamo quindi evidenza di un difetto di archi mancanti,
trasferimento fisico o capacità del contesto. Vedere un titolo o precaricare un
vicino non significa leggerne il contenuto. Le rubriche attuali sono ID/titolo.

`content_revision` e revisioni del grafo invalidano le cache, ma non rappresentano
validità del documento, approvazione, decorrenza o autorità della fonte. La data
di creazione/importazione del nodo non è la data di validità di un'affermazione.

## Esperimenti

```powershell
python -m luca_memory.autonomy_check
python -m luca_memory.autonomy_check --profile audited
python -m luca_memory.autonomy_check --profile addressed --case incomplete,paraphrase --repeat 2
python -m luca_memory.autonomy_check --case incomplete,stale_history --profile audited --repeat 2
```

Il primo comando confronta la Bibbia attuale con una copia temporanea più
indicazioni generiche su completezza, archi locali e revisioni applicabili.
Il secondo aggiunge una revisione del modello sulla prima risposta proposta
in ogni sessione: riceve domanda, stato e `draft_response`, mai la griglia delle
risposte attese. Può approvare, cercare o aprire; il Core normale valida gli archi.
La revisione aggiuntiva è imposta dal protocollo sperimentale: non significa che
il modello l'abbia chiesta spontaneamente. L'app non usa questo adapter.

Il profilo `addressed` conserva la Bibbia originale e aggiunge i numeri dei
capitoli soltanto ai titoli del manuale controllato. Fatti, keyword, ID e archi
restano identici. Isola la difficoltà di associare rimandi ai capitoli con
indirizzi ID/titolo, senza sostituire il documento sperimentale precedente.

Sei prove coprono ripristino incompleto, parafrasi delle condizioni di apertura,
revisione attiva contro archivio/bozza, cronologia obsoleta, fonti di pari autorità
in conflitto e aritmetica generale senza necessità di lettura. Sessioni e archivi
sono nuovi. La cronologia obsoleta è un dato inserito esplicitamente nel test,
non una convinzione pregressa misurata nei pesi. Laboratori, date, approvazioni
e porte sono dati immaginari controllati, non istruzioni tecniche reali verificate.

I rapporti `D:/Test/Luca/autonomy-check-*.json` conservano istruzioni integrali,
hash, domande/griglie, aperture effettive, decisioni, risposte, token nativi,
tempi e misure CUDA. L'ordine dei profili è fisso; campioni piccoli non dimostrano
affidabilità. Gli indicatori lessicali non sono voti semantici.

## Modello operativo proposto, non implementato

Un ciclo limitato: individuare la parte mancante del compito, scegliere un
indirizzo promettente, leggere e verificare se la domanda è sufficientemente
coperta. Titolo, valore plausibile e rimando a un capitolo non sostituiscono
un dettaglio necessario. Non serve obbligare a cercare per ogni domanda generale.
Un eventuale revisore della completezza deve essere misurato anche per costo
aggiuntivo e lasciare visibile ciò che resta irrisolto quando termina il budget.

Per fatti modificabili, la familiarità con una risposta non ne dimostra
l'attualità: consultare versioni/configurazioni pertinenti anche quando il modello
conosce un valore abituale. Preferire la fonte approvata ed effettiva a quella
esplicitamente sostituita nello stesso ambito; non dare precedenza automatica a
ogni nodo esterno o all'ultima importazione. Conservare le versioni storiche per
le domande sul passato.

Prima di scalare questa politica occorrono fonte, ambito, revisione documentale,
inizio/fine validità, stato di approvazione/verifica e collegamenti di sostituzione
espliciti, con un processo controllato di acquisizione. Etichette affermate nel
testo importato non provano da sole l'autorità della fonte. Conflitti irrisolti
tra fonti equivalenti richiedono trasparenza o chiarimento, non un vincitore
inventato. Un aggiornamento locale non modifica regole generali fuori ambito
né cambia i pesi del modello.

## Criterio di accettazione

Servono insieme letture utili osservate, fedeltà/completezza della risposta e
assenza di confusione d'ambito. Scartare il valore vecchio senza cercare quello
nuovo è solo un progresso parziale. Seguire archi locali ma rispondere male non
basta. Prima di promuovere una variante servono altri documenti, parafrasi e
ordine delle fonti invertito.

## Esiti osservati: attuale, indicazioni e revisione di una bozza

Primo confronto: `D:/Test/Luca/autonomy-check-20261022-082433-714791.json`
(12 esecuzioni). Prova con revisione:
`D:/Test/Luca/autonomy-check-20261022-082759-285587.json` (sei esecuzioni).
Entrambe con `google/gemma-4-e2b`, tokenizzazione nativa e CUDA reale sulla GPU 1.

| Prova | Bibbia attuale | Indicazioni generiche | Indicazioni più revisione |
| --- | --- | --- | --- |
| Ripristino | Legge il ripristino, risposta incompleta | Include quattro campioni/CONFERMA, ma non le soglie di apertura | Incompleta; approva la propria bozza incompleta |
| Parafrasi apertura | Secondo capitolo sbagliato, incompleta | Passi locali ma arresto prematuro | Legge indice → modalità → soglie via archi locali; condizioni corrette |
| Revisione attiva | Risponde per il laboratorio sbagliato | Legge Primula attiva, 1502 corretta | 1502 corretta, conservando l'ambito locale |
| Cronologia obsoleta | Scarta 502, ma dice falsamente che il sostituto non è specificato | Scarta 502 senza cercare il sostituto | Regressione: conferma 502 senza leggere nulla |
| Fonti equivalenti in conflitto | Legge A e sceglie 2502 | Stesso fallimento | Stesso fallimento nonostante la revisione |
| Aritmetica generale | 42, nessuna lettura | 42, nessuna lettura | 42, nessuna lettura ma una chiamata in più |

Nella parafrasi con revisione, il modello aveva già scelto di leggere le soglie
prima della bozza: non è la revisione aggiuntiva ad aver provocato quel passo.
Questi confronti non isolano la formulazione dall'effetto di un contesto più
lungo. La revisione costa tempo (aritmetica circa 6,8 s contro 3,6 s) e non dà
miglioramenti monotoni. Le letture locali osservate dimostrano che il percorso
è tecnicamente disponibile, ma **non abbiamo raggiunto** completamento autonomo
e scoperta affidabile dei conflitti. Nessuna variante passa nell'applicazione.

La cronologia è il caso più insidioso: «non ho visto aggiornamenti» non equivale
a «non esistono aggiornamenti» quando restano candidati pertinenti da leggere.
La prova riguarda fonti storiche/attive esplicite e ancoraggio alla conversazione,
non una convinzione obsoleta dimostrata nei parametri del modello. Il meccanismo
proposto per pesi contro memoria richiede ancora una verifica distinta.

## Controllo sui titoli e prossimo esperimento

`D:/Test/Luca/autonomy-check-20261022-083056-705997.json` aggiunge quattro
esecuzioni: ripristino e parafrasi ripetuti due volte, Bibbia originale, numeri
di capitolo espliciti nei titoli. In tutti e quattro mancano soglie o dettagli
di ripristino necessari. I titoli da soli non risolvono il completamento.
La prima parafrasi compie un passo locale, poi torna a ingressi globali non
pertinenti. Totale dell'indagine: 22 esecuzioni live, senza modificare l'app.
Le ripetizioni non dimostrano stabilità su altri modelli o documenti.

Il prossimo esperimento limitato dovrebbe separare **pianificazione delle
informazioni necessarie** e **risposta**. Chiedere al modello una breve lista
di fatti richiesti e punti irrisolti prima della bozza, conservandola insieme
alle letture effettive. Un'operazione distinta di copertura classifica gli
elementi come sostenuti, mancanti o in conflitto, riferendoli ai nodi letti.
Il modello sceglie ricerca/apertura successiva; il Core valida indirizzi e
budget; alla fine i punti irrisolti restano visibili. Nessuna regola specifica
per dominio né richiesta di ragionamento interno privato: sono requisiti del
compito osservabili, non una spiegazione della catena di pensiero interna.

Non è ancora provato e non è una soluzione garantita. La semplice revisione
della bozza sopra non basta a dimostrarlo. Confrontare la copertura esplicita
con una normale chiamata aggiuntiva di pari costo; usare documenti non utilizzati
per mettere a punto le istruzioni e fonti in ordine invertito. Verificare fonte
attiva contro bozza più recente dopo averle lette entrambe, non soltanto aver
scelto il titolo che sembra attivo. Per l'attualità servono provenienza/validità
strutturate prima di dichiarare un protocollo autorevole di aggiornamento:
conservare i contenuti storici, esporre sostituzioni/conflitti e non riscrivere
le risposte con filtri semantici nascosti.

Verifiche automatiche: 249 test Python individuati, sette opzionali hardware/
servizi saltati; 19 JavaScript superati e Ruff pulito. Le prove live hanno
esercitato separatamente tokenizzazione nativa e allocazioni CUDA effettive.
