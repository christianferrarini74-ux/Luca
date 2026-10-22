# Correzione della centratura dopo il trascinamento

> **Documento storico — non guida operativa attuale.** Specifiche, default, risultati e passi successivi qui descritti appartengono alla fase registrata. Per ambito, API e comportamento vigenti leggere il [contratto attuale](28-contratto-utilizzo-memoria.md). Le evidenze originali sono conservate.

2026-10-22. [English](../../memory-graph-centering.md).

Nella pagina segnalata tutti i nodi avevano trasformazioni `translate(NaN,NaN)`
e il `viewBox` conteneva quattro `NaN`. Cambiare vista o premere «Centra mappa»
non poteva recuperare la geometria.

Il trascinamento conservava un `DOMPoint`. Il successivo layout lo copiava con
`{...point}`, ma le coordinate del browser sono proprietà del prototipo, non
campi enumerabili: la copia perdeva `x` e `y`, contaminando poi gli altri nodi.
Un test di regressione con getter non enumerabili è fallito prima della correzione.

Ora il trascinamento salva numeri in un oggetto semplice; il layout copia
esplicitamente `x`/`y` e scarta coordinate non finite. La centratura ricostruisce
eventuali posizioni corrotte, considera solo i nodi della vista corrente,
annulla il trascinamento pendente e calcola il riquadro dal centro reale e
dalle dimensioni disponibili, con margini in pixel per etichette e bersagli.
Il `viewBox` ha inoltre una protezione contro dimensioni invalide.

Verifiche: **10 test JavaScript**, compresi trascinamento→cambio vista,
coordinate invalide, singolo nodo negativo, proporzioni strette/larghe e
recupero di una mappa corrotta. **219 test Python superati** con CUDA e tokenizer
reali, senza skip. Nel browser su database temporaneo: trascinamento reale,
passaggio completato globale→focus, «Centra mappa» e controllo DOM che tutti
i tre nodi siano nel riquadro con coordinate finite. Schermata:
`D:\Test\Luca\memory-graph-fit-20261022.png`.

Non sono cambiati memoria, API, modello o dipendenze. La pagina dell'utente
è stata ispezionata senza ricaricarla, inviare chat o cambiare il focus del Core.
Per caricare il JavaScript corretto basta aggiornare la pagina (Ctrl+F5), senza
arrestare il server. Il frontend attuale rinizializza la trascrizione visibile
al caricamento e invia il saluto iniziale; non usare «Nuova Sessione» per questa
correzione. Il server di prova separato viene chiuso a fine verifica.
