# Ingresso nella memoria e continuità del dialogo — 2026-10-21

> **Documento storico — non guida operativa attuale.** Specifiche, default, risultati e passi successivi qui descritti appartengono alla fase registrata. Per ambito, API e comportamento vigenti leggere il [contratto attuale](28-contratto-utilizzo-memoria.md). Le evidenze originali sono conservate.

[English](../../memory-entry-cues.md)

## Evidenze e correzioni

La conversazione segnalata non recupera “I Topi Intagliatori di Formaggio”, benché
il nodo esista nel seed configurato (ID 18). La lettura diagnostica dell'API attiva
mostra `answer`, nessun focus e `expose_memory: false`: evidenza di ingresso
mancato, non di conoscenza assente dall'archivio.

La ricerca globale dipendeva interamente dalla richiesta del modello. Inoltre,
quando rinunciava all'esposizione, il prompt dichiarava l'assenza di ricordi
pertinenti anche senza una ricerca. Infine, una risposta recente lunga poteva
far escludere tutta la coppia domanda/risposta dal budget `history_limit`.

Correzioni implementate:

- Prima di ogni navigazione viene consultata la proiezione di metadati dell'indice
  globale: titolo, slug e keyword. Al massimo `global_candidates` voci ID/titolo.
  Non si leggono né promuovono contenuti e il Core non sceglie semanticamente il
  nodo. L'LLM può cercare, aprire un candidato o rispondere in generale.
- Ricerca OR con token quotati, non AND dell'intera domanda colloquiale. Restano
  disponibili ricerca esplicita full-text/alias. È un accesso lessicale, non una
  comprensione automatica dei sinonimi.
- Aggiornamento della proiezione nella transazione del nodo, migrazione delle
  proiezioni mancanti senza sostituire contenuti, rimozione delle voci cancellate.
- Il prompt dice che la memoria **non è stata usata**, non che **non esiste**.
- L'ultima coppia conversazionale troppo grande viene mantenuta con estratti in
  byte esplicitamente segnalati, entro il budget esistente. Cronologia originale
  invariata: niente riassunti semantici, LLM compressore o nuova memoria persistente.
- Il navigatore vede tutta la rubrica; la chiamata di risposta vede soltanto la
  conoscenza selezionata. Il JSON di navigazione non è una provenienza della
  conoscenza. Diagnostica e intervalli di esposizione seguono i byte reali del testo.

API/cruscotto espongono `entry_candidate_ids`, `explicit_search_performed` e
`history_excerpted`: diagnostica, non punteggi di verità. Entry point e dipendenze invariati.

## Verifiche e limiti residui

**158 test automatici superati, comprese quattro prove CUDA reali.** Coperti
metadati senza lettura payload, rollback/rinomina/cancellazione, nessuna apertura
forzata, cronologia delimitata e separazione fra risposta e navigazione. Superati
compilazione e controllo delle modifiche.

La suite sintetica isolata ottiene **8/8** in
`D:/Test/Luca/phase11-live-20261021-180932.json`, incluso il richiamo spontaneo
prima fallito. È una singola esecuzione su fixture, non affidabilità generale.
Alcuni turni riusciti compiono ancora passaggi avanti/indietro ridondanti entro il
limite configurato: resta un problema di efficienza.

La riproduzione dei sette messaggi apre correttamente il nodo 18 e lo ritrova
dopo le domande generali. Tuttavia il report rigoroso finale **non è verde**:
`D:/Test/Luca/dialogue-live-20261021-181146.json`. Superati cinque dei sei controlli
lessicali/di ambito; una domanda concettuale resta esplicitamente a revisione
manuale. Il modello aggiunge ancora spiegazioni causali non supportate e formule
come “descrizione fornita” o “si dice”. Il comando registra separatamente questi
avvisi e termina con esito negativo, senza dichiarare accettazione completa.
I controlli lessicali non certificano l'accuratezza biologica o la fedeltà complessiva.

Riproduzione con LM Studio disponibile:

```powershell
python -X utf8 -m luca_memory.dialogue_check
python -X utf8 -m luca_memory.live_memory_check
```

Entrambi usano database temporanei nella cartella dati configurata, non quello
personale. L'applicazione attiva è stata ispezionata ma non riavviata né modificata
via API. Per caricare le correzioni: **Esci/Arresta Luca**, poi
`python run_luca.py`; la migrazione di schema/indice avviene all'avvio.

Resta da migliorare la fedeltà delle risposte, evitare cause inventate e mantenere
coerenza semantica/stilistica dopo digressioni di conoscenza generale. Non dichiariamo
questi problemi risolti con filtri o con un modello più grande. Architettura di
famiglie/rubrica invariata; nessuna integrazione Cesare.
