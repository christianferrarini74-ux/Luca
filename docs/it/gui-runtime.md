# Runtime della dashboard di Luca

La dashboard è un frontend, non fa parte del runtime cognitivo di Luca.

```text
browser GUI → API HTTP locale → LucaSession / MemorySearch / LLM Connector
```

L'API Python si avvia con:

```powershell
python run_luca.py
```

Il percorso opzionale Gemma si seleziona impostando
`runtime.language_adapter: gemma` in `config.yaml`; il punto di avvio resta lo stesso:

```powershell
python run_luca.py
```

Il punto di avvio avvia il frontend Vite come processo figlio e apre
automaticamente l'URL configurato nel browser. Quando si chiude il punto di
avvio, vengono chiusi runtime e frontend.

## Confine API

- `GET /api/health` segnala la disponibilità del backend.
- `GET /api/state` restituisce uno snapshot del runtime in sola lettura.
- `POST /api/chat` accetta `{ "text": "..." }` e restituisce risposta verificata,
  traccia e snapshot aggiornato.

Il frontend non può accedere a SQLite, attraversare il grafo, scegliere un LLM
o scrivere memoria. Invia il testo dell'utente e rende visibili le risposte del
backend. Lo stesso Core resta così utilizzabile da CLI, test o altri frontend.
