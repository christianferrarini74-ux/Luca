# Bibbia: conoscenza acquisita e conoscenza generale

> **Documento storico — non guida operativa attuale.** Specifiche, default, risultati e passi successivi qui descritti appartengono alla fase registrata. Per ambito, API e comportamento vigenti leggere il [contratto attuale](28-contratto-utilizzo-memoria.md). Le evidenze originali sono conservate.

Data: 2026-10-22. [English](../../integrated-knowledge-bible.md).

## Intervento

La riscrittura di `bible.md` assume i contenuti letti come conoscenza vera nel
contesto, senza disabilitare la conoscenza generale del modello. Conserva
condizioni e direzione causale, distingue contenuti da indirizzi ID/titolo e
chiede di leggere un nodo pertinente prima di spiegarlo. Invita a enunciare
direttamente i fatti e a chiarire fonti e attendibilità quando richiesto,
senza inventare esperienze o verifiche. Consente deduzioni, senza trasformarle
automaticamente in fatti letti o reinterpretare i ricordi come leggende.

Non sono cambiati Core, configurazione, modello, generazione, giostra fisica
o database personale. Nessun filtro semantico aggiunto, nessuna nuova dipendenza.
Le regole restano nella Bibbia, non in decisioni hardcoded. La traduzione
`docs/bible.en.md` è documentazione, non un secondo prompt.
La precedente versione modificata dall'utente è salvata in
`D:\Test\Luca\bible-before-revision-20261022.md`.

## Evidenze

Suite completa: **210 test superati**, con tokenizer LM Studio e CUDA reali.
Prova live con `google/gemma-4-e2b`:

```powershell
python -m luca_memory.reasoning_check --scenario integration
```

**8/8 controlli** nella sequenza che alterna dieta degli asini, volo, pioggia
naturale, pioggia particolare e collegamento causale. Luca usa conoscenza
generale anche dopo la lettura, apre il nodo 3 sul volo e il nodo 2 sulla
pioggia particolare, invece di spiegarne il solo titolo. Il test usa storage
sintetico temporaneo e chiude le risorse. Risposte, letture, tracce, conteggi
e copia della Bibbia sono nel rapporto:

`D:\Test\Luca\reasoning-live-20261022-003635.json`

SHA-256 del testo normalizzato dal lettore della Bibbia:
`979c4b83dfd710be5853849b0872da3d1d251458df209512d594ee79cc7c0ecc`.

Una prova aggiuntiva in memoria usa un manuale tecnico inventato: Luca legge
il nodo 100, risponde che R17 attiva la modalità dopo il codice BRINA-624,
corregge l'ipotesi che R18 la attivi (la disattiva), poi risponde alla domanda
generale sulla dieta assente dal manuale. Tre scambi riusciti; evidenza
nell'output della sessione, non in un rapporto separato. Sessione chiusa.

## Limiti e utilizzo

Gli otto controlli sono lessicali e sulle letture reali, non certificano tutta
la semantica o lo stile. Resta la premessa «Secondo le informazioni disponibili»
in una risposta; nell'approfondimento compare «meno densa», dettaglio assente
dal nodo. Il collegamento causale finale è fedele al seed, non una verifica
della realtà delle affermazioni sperimentali.

Le prime stesure hanno ottenuto 5/8 e 7/8: allungare la Bibbia non bastava.
La versione finale chiarisce soprattutto la scelta leggere/rispondere.
Il precedente scenario `weather`, prima 7/8 per esplorazione ulteriore, non
è stato rieseguito: quel limite non è dichiarato risolto.

La Bibbia viene riletta a ogni richiesta: nessun riavvio necessario per questo
intervento su un'app già aggiornata. Iniziare una **nuova conversazione** per
non trascinare vecchie risposte restrittive. Le prove non hanno modificato la
memoria personale. Restano da valutare insieme naturalezza e fedeltà su
dialoghi più ampi e documenti reali.
