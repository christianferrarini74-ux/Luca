# Cruscotto di prova e runtime di Luca

[English](../gui-runtime.md) · [Indice](INDICE.md)

Guida attuale, 2026-10-22. Le precedenti istruzioni d'avvio sono
[archiviate](../history/gui-runtime.it.md).

Unico avvio applicativo: `python run_luca.py`. Python serve API e cockpit statico
`luca_memory/web/` su `http://127.0.0.1:8765/`, aprendo il browser se
`frontend.enabled` è true. Non servono runtime Node/Vite, processi figli
frontend, porte frontend separate o ulteriori shell.

La GUI è un frontend di prova: invia richieste e mostra lo stato del Core.
Navigazione, persistenza, revisioni, scelta del modello, budget e sonno sono
nel backend. Ispezione della mappa e richiamo esplicito sono distinti.
Titolo visibile, contenuto in cache o colore del nodo non dimostrano che
l'LLM abbia letto o usato correttamente la conoscenza.

## Endpoint locali

- `GET /api/health`: disponibilità backend.
- `GET /api/state`: snapshot di runtime/livelli/focus/rubrica/manutenzione.
- `POST /api/chat` con `{"text":"..."}`: risposta LLM, traccia e stato. Il Core
  convalida struttura e percorsi, non la verità fattuale della risposta.
- `POST /api/recall` con `{"node_id":1}`: richiamo esplicito di un nodo noto.
- `/api/memory/*` e `/api/maintenance/*`: operazioni Core nel
  [contratto](fase-1-sinapsi/28-contratto-utilizzo-memoria.md).
- `POST /api/shutdown`: arresto ordinato, richiesto anche da **Esci**.

Usare host/porta configurati anziché assumere i default. API locale, non
servizio remoto/multiutente autenticato. Il frontend non modifica SQLite:
richieste di modifica e conferma vengono convalidate dal Core proprietario.
I limiti grafici non tagliano la rubrica completa di primo grado.

## Ciclo di vita

Avviare il server LM Studio prima di usare il config LLM distribuito.
Fermare con **Esci** o Ctrl+C nella shell d'avvio. Il worker del sonno viene
arrestato e atteso con join; sessione, DB e allocazioni dei livelli vengono
rilasciati. La richiesta al provider già in corso non è interrotta forzatamente
e può ritardare l'arresto fino al timeout. Una transazione iniziata termina atomicamente.

Riavviare dopo modifiche Python/config/interfaccia e aggiornare il browser
dopo modifiche agli asset. Documentazione e test non riavviano l'app dell'utente.
