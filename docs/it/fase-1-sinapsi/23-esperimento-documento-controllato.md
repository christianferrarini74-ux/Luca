# Esperimento con documento controllato: IRIS-17

> **Documento storico — non guida operativa attuale.** Specifiche, default, risultati e passi successivi qui descritti appartengono alla fase registrata. Per ambito, API e comportamento vigenti leggere il [contratto attuale](28-contratto-utilizzo-memoria.md). Le evidenze originali sono conservate.

2026-10-22. [English](../../controlled-document-experiment.md).

## Materiale e isolamento

Il [manuale](../esperimenti/iris17-manuale.md) descrive una centralina di
irrigazione immaginaria ma coerente, non un prodotto reale. Il suo testo è
riprodotto nei sette nodi di `seed/iris17_controlled_v1.json`: ingresso/indice
e sei capitoli. L'indice collega tutti i capitoli; altri archi reali collegano
avvio, soglie, allarme, ripristino e manutenzione. Sono normali nodi collegati,
non frammenti artificiali di una famiglia.

La griglia di valutazione è separata in `tests/fixtures/iris17_questions.json`:
non viene mai passata al modello. I test verificano fedeltà documento/seed e
topologia. È un documento preparato manualmente, non un importatore PDF o uno
splitter automatico. Biblioteca principale vuota e database personali restano
intatti. La traduzione inglese è documentazione, non ulteriore contesto al modello.

## Confronto a coppie

Eseguire dalla cartella del progetto, con modello, Bibbia e budget configurati:

```powershell
python -m luca_memory.controlled_document_check --case all
# Una sola coppia, più breve:
python -m luca_memory.controlled_document_check --case chain
```

Ogni domanda viene posta in due sessioni nuove e indipendenti, con database
temporanei: prima memoria vuota, poi documento. Ogni sessione ha un adapter
nuovo, senza cronologia o focus ereditati. Le domande nominano il dispositivo,
non gli ID dei nodi e non impongono percorsi. Nessuna regola obbliga a leggere.
Impostazioni runtime, ID modello, copia della Bibbia, hash dei materiali,
letture effettive, decisioni di navigazione, memoria fisica, tempi e risposte
sono salvati in `D:/Test/Luca/iris17-check-*.json`. Il rapporto contiene anche
la griglia per la revisione umana, aggiunta dopo la generazione. Il codice di
uscita indica errori di esecuzione, non accettazione semantica.

## Sette prove

- Richiamo diretto: frequenza di campionamento.
- Parafrasi: terreno asciutto ma acqua assente; condizioni di apertura.
- Applicazione collegata: E42, segnale tornato valido, ripresa dell'irrigazione.
- Confine: letture 27%, 28%, 27% a valvola chiusa.
- Premessa falsa: spegnimento e riaccensione cancellano E42.
- Informazione assente: tensione di alimentazione.
- Procedura e frequenza della manutenzione.

Valutare separatamente fatti corretti, condizioni conservate, aggiunte non
giustificate e riconoscimento dei dati assenti. Confrontare risposte senza/con
documento e letture effettive. Corrispondenze lessicali e copertura dei nodi
attesi sono solo indicatori: una negazione può ingannarli e un capitolo può
ripetere un'informazione presente altrove. Leggere tutti i nodi attesi non è
di per sé necessario alla correttezza e non prova navigazione locale: nella
traccia distinguere ingressi globali e attraversamento degli archi.

L'ordine fisso vuoto-prima e i fatti deterministici limitano la prova. Una
singola esecuzione non è evidenza statistica; nodi piccoli non dimostrano
pressione di memoria, qualità dell'oblio o prestazioni su libri grandi.
Nessuna nuova istruzione al modello, filtro semantico o dipendenza runtime.

## Prima esecuzione live — accettazione non completata

Completate tutte le quattordici esecuzioni con `google/gemma-4-e2b`, conteggio
nativo dei token e CUDA reale sulla GPU 1. Evidenza:
`D:/Test/Luca/iris17-check-20261022-080943-175245.json`.
SHA-256 del documento: `99f7abad79d4a14ab5153b8cbc3929b9ee44638a7366fa118cf4db589bc43d16`.
Bibbia e runtime del grafo non sono stati modificati per migliorare gli esiti.

La lettura umana trova corrette frequenza, ragionamento sul confine delle soglie
e manutenzione. Nella parafrasi mancano le soglie di apertura: legge modalità
e poi manutenzione non pertinente. Per il ripristino legge il capitolo 4, ma
omette quattro campioni validi e CONFERMA e non approfondisce le condizioni di
apertura. Respinge la premessa sul riavvio senza leggere la procedura corretta.
Sulla tensione non inventa numeri, ma legge solo l'indice e usa erroneamente
la natura immaginaria del dispositivo come motivo dell'assenza del dato.

Tutte le aperture osservate sono ingressi globali: **nessun attraversamento
locale degli archi**. Vicini residenti/precaricati non equivalgono a capitoli
effettivamente letti dal modello. Senza documento, la manutenzione ripete
ricerche fino al limite di otto passi: nessun errore esecutivo, ma inefficienza.
Abbiamo dunque evidenza di recupero e uso dipendente dalla memoria su questo
documento, non di esplorazione affidabile tra capitoli. Non trasformare gli
indicatori lessicali in una percentuale di successo.

Verifica automatica: 244 test Python individuati, sette opzionali hardware/
servizi saltati; 19 test JavaScript superati e Ruff pulito. La prova live sopra
ha esercitato separatamente tokenizzazione nativa e memoria fisica CUDA.
