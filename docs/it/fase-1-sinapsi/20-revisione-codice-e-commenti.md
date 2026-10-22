# Revisione del codice e dei commenti interni

> **Documento storico — non guida operativa attuale.** Specifiche, default, risultati e passi successivi qui descritti appartengono alla fase registrata. Per ambito, API e comportamento vigenti leggere il [contratto attuale](28-contratto-utilizzo-memoria.md). Le evidenze originali sono conservate.

2026-10-22. [English](../../code-maintenance-review.md). Base: commit `291189f`.

## Obiettivo e perimetro

Ridurre duplicazioni e lavoro ripetuto, rendendo leggibili i passaggi interni
dei moduli più estesi. Non è una riscrittura dell'architettura o delle regole
di Luca. Bibbia, configurazione, dipendenze, formati persistenti, ranking SQL,
interfacce pubbliche e comportamento della memoria restano invariati.
Nessuna cancellazione di percorsi storici ancora coperti dai test.

## Semplificazioni effettive

- `api.py`: un solo ciclo per famiglie prefisso/suffisso, un caricamento invece
  di due per risolvere ciascun titolo, un unico lettore dei corpi JSON.
  Rimangono le diverse validazioni, limiti ed errori delle singole rotte.
- `store.py`: `dataclasses.replace` conserva i campi del risultato durante
  l'annotazione del richiamo; un solo filtro per le alternative. Nessuna modifica
  alle strategie di convergenza, alle query o alle migrazioni storiche.
- `session.py`: `handle` passa da **132 a 48 righe fisiche**, separando gestione
  del turno, risposta del modello e risposta deterministica. I due helper sono
  privati e restano sotto il lock del turno. Non si genera una seconda risposta
  quando il navigatore ha già risposto; priorità degli adapter e cronologia
  conservate.
- `navigation.py`: costruzione e nuovo turno usano la stessa inizializzazione.
- `reading_workspace.py`: offset UTF-8 incrementali invece di ricostruire e
  ricontare tutti i prefissi per ogni lettura. Serializzazione e intervalli byte
  identici, anche con accenti ed emoji; nessuna confusione con i token.
- `tiers/carousel.py`: deduplicazione ordinata dei vicini tramite dizionario,
  evitando ricerche ripetute nella lista; rimosso un aggiornamento ridondante
  dell'insieme dei nodi espansi; unificati i due versi del rinforzo. Ordine di
  richiamo, transazioni, capacità e trasferimenti fisici conservati.
- `web/app.js`: preparazione POST JSON e apertura/chiusura dei gruppi della
  navigazione condivise; elenco pagine derivato dai metadati già esistenti.
  Restano distinti effetti sul transcript, gestione degli errori e conferme.
- `web/graph.js`: ricerca dei titoli in un passaggio, invece di scandire tutti
  i nodi per ogni nodo visibile; eliminato il doppio ridisegno dopo la centratura
  e l'aggiornamento duplicato del viewBox. Conservata la correzione DOMPoint.

Le riduzioni di complessità riguardano operazioni locali: non costituiscono una
misura di accelerazione dell'LLM o una prova di prestazioni su biblioteche grandi.

## Commenti e responsabilità

Commenti/docstring in **inglese**, vicino alle funzionalità interessate, non
solo nell'intestazione. Coprono lock rientranti, transazioni annidate/savepoint,
ordine delle migrazioni, indici e self-loop, revisioni e famiglie canoniche,
serializzazione, letture effettive contro precaricamento, bytes contro token,
continuità dei compiti, proposte/conferma/ripristino, annullamento del sonno,
lifecycle del cruscotto e geometria del grafo.

Sono commentati anche `adapters.py`, `budget.py`, `maintenance.py`,
`planning.py` e `synaptic_schema.py`: in particolare le euristiche legacy
rules/hybrid non vanno confuse con il navigatore LLM. Nessuna istruzione
semantica aggiunta al codice o ai prompt.

Il criterio è spiegare responsabilità, invarianti e motivazioni; non descrivere
ogni assegnazione ovvia. Non sono stati creati helper generici per parti simili
solo nell'aspetto, come i budget nativi in token e quelli conservativi in byte.

## Dimensione e verifica

Su nove file con riorganizzazioni funzionali (`api`, `store`, `session`,
`adapters`, `navigation`, `reading_workspace`, `tiers/carousel`, `web/app`,
`web/graph`), le righe operative non vuote passano da **3424 a 3388**.
La misura esclude commenti a riga intera e docstring Python, non comprime
artificialmente le istruzioni. Le righe fisiche passano invece da **3864 a
3940**, perché sono state aggiunte spiegazioni e separati i compiti. Non si
presenta quindi questa revisione come un drastico taglio della dimensione.
Test e documentazione aggiunti sono esclusi da questi conteggi.

Prima: **219 test Python e 10 JavaScript**. Dopo: **235 Python e 19 JavaScript**,
tutti superati; suite Python con CUDA e tokenizer reali, senza skip.

```powershell
$env:LUCA_TEST_CUDA='1'
$env:LUCA_TEST_LMSTUDIO='1'
.venv/Scripts/python.exe -m unittest discover -s tests
node --test tests/test_graph_frontend.js tests/test_cockpit_frontend.js
```

Le nuove regressioni verificano formati HTTP e payload, titoli/limiti delle
famiglie, transazioni e copie dei risultati, priorità della generazione,
assenza di doppia risposta, intervalli Unicode, ricerca delle parti compresse,
busy/errori/conferme, inizializzazione e polling del frontend. I quattro nuovi
test pubblici di sessione/workspace passano anche caricando il codice precedente;
gli otto test VM del cruscotto sono stati verificati anche sul codice originale.

I test JavaScript del cruscotto usano un DOM simulato: nessuna nuova prova
manuale nel browser o certificazione del layout in questa revisione. Nessun
dialogo libero con il modello è stato usato per affermare un miglioramento
semantico. Le prove non usano la memoria personale e non riavviano l'app.

Per caricare le modifiche Python, arrestare Luca ordinatamente e rilanciare
`python run_luca.py`; aggiornare poi la pagina. Non reinstallare dipendenze.
