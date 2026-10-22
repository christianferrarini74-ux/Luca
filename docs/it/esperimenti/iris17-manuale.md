# IRIS-17 — Manuale controllato, revisione 1.0

Dispositivo immaginario per verificare Luca. Non usare queste istruzioni su hardware reale.
La versione JSON in `seed/iris17_controlled_v1.json` contiene gli stessi titoli e contenuti, senza le domande di valutazione.

## 0. IRIS-17 — centralina di irrigazione: indice

Documento di prova controllato IRIS-17, revisione 1.0. Dispositivo immaginario: le specifiche valgono soltanto per questo manuale, non per apparecchi reali.
Indice: 1. Modalità e avvio; 2. Sensore e soglie; 3. Allarme E42; 4. Ripristino; 5. Manutenzione; 6. Limiti delle informazioni. Ogni capitolo è raggiungibile dal nodo indice.

## 1. IRIS-17 — modalità e avvio

Fonte: manuale IRIS-17, revisione 1.0, capitolo 1.
La centralina ha due modalità: OSSERVA e IRRIGA. All'accensione entra sempre in OSSERVA: misura l'umidità ma mantiene chiusa la valvola. Il comando AVVIA passa a IRRIGA soltanto se non vi sono allarmi attivi. Per il comando di apertura in IRRIGA si applicano le condizioni del capitolo 2. Se è attivo E42, consultare il capitolo 3 e la procedura del capitolo 4.

## 2. IRIS-17 — sensore e soglie

Fonte: manuale IRIS-17, revisione 1.0, capitolo 2.
Il sensore U7 misura l'umidità del terreno ogni 30 secondi. In modalità IRRIGA, con valvola chiusa e nessun allarme attivo, tre letture consecutive strettamente inferiori al 28% aprono la valvola. Una lettura pari o superiore al 28% azzera il conteggio. Con valvola aperta, una lettura pari o superiore al 41% la chiude. In OSSERVA la valvola resta chiusa. I segnali non validi sono gestiti secondo il capitolo 3.

## 3. IRIS-17 — allarme E42

Fonte: manuale IRIS-17, revisione 1.0, capitolo 3.
Due campioni consecutivi non validi del sensore U7 attivano E42. Un campione valido prima del secondo non valido azzera il conteggio degli errori. E42 chiude immediatamente la valvola e imposta OSSERVA. Un valore di umidità basso ma valido non è un campione non valido. Il ritorno del segnale valido non cancella E42. Seguire il capitolo 4 per il ripristino e il capitolo 5 per la manutenzione.

## 4. IRIS-17 — procedura di ripristino

Fonte: manuale IRIS-17, revisione 1.0, capitolo 4.
Dopo E42, controllare il collegamento del sensore U7; prima di intervenire sui collegamenti togliere alimentazione. Dopo il controllo e la riaccensione servono quattro campioni consecutivi validi e poi il comando CONFERMA per cancellare E42. Un campione non valido interrompe la sequenza dei quattro. La sola riaccensione non cancella l'allarme memorizzato. CONFERMA senza i quattro campioni validi non lo cancella. Dopo la cancellazione la modalità resta OSSERVA: per tornare a IRRIGA occorre AVVIA. L'apertura richiede poi le condizioni del capitolo 2.

## 5. IRIS-17 — manutenzione

Fonte: manuale IRIS-17, revisione 1.0, capitolo 5.
Ogni 14 giorni pulire la sonda U7 con un panno asciutto e controllare il suo collegamento. Togliere alimentazione prima della manutenzione. Non immergere la centralina. Se E42 persiste dopo il controllo e la procedura del capitolo 4, rivolgersi al servizio tecnico; il manuale non prescrive altre riparazioni.

## 6. IRIS-17 — limiti delle informazioni

Fonte: manuale IRIS-17, revisione 1.0, capitolo 6.
Questo manuale non specifica tensione di alimentazione, portata della valvola, supporto Wi-Fi o durata massima di irrigazione. Nessun valore può essere ricavato con certezza dalle soglie di umidità. Le procedure riguardano soltanto il dispositivo immaginario IRIS-17 revisione 1.0.
