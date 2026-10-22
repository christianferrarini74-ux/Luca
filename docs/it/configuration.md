# Configurazione di Luca

[English](../configuration.md) · [Indice](INDICE.md)

Guida operativa verificata su `config.yaml` e `luca_memory/config.py` il
2026-10-22. Versione precedente [archiviata](../history/configuration.it.md).

## Un avvio, una configurazione

Dalla radice del repository eseguire `python run_luca.py`. Legge `config.yaml`
una volta; `--config` permette di scegliere un file alternativo esplicito.
Riavviare dopo modifiche a Python/YAML. `runtime.bible` viene riletta nelle
richieste LLM, ma i cambi d'interfaccia vanno distribuiti con il Python corrispondente.

Il file distribuito è specifico della macchina, non una prescrizione hardware:

| Parametro | Valore distribuito / significato |
| --- | --- |
| `storage.directory` | `D:/Test/Luca`, esterno ai sorgenti |
| `storage.database` | `luca_library.sqlite`, relativo alla directory di storage |
| `storage.seed` | `seed/library_empty_v1.json`, relativo alla directory del config |
| `runtime.bible` | `bible.md`, relativo alla directory del config |
| `language_adapter` / `memory_planner` | `gemma` / `llm`, navigazione strutturata LM Studio |
| `memory_backend` / `gpu_device` | `cuda` / 1; storage reale sulla GPU con ordinale zero-based 1 |
| `vram_capacity` / `ram_capacity` | 5 / 12 slot dei contenuti |
| `vram_bytes` / `ram_bytes` | 8.000.000 / 32.000.000 byte serializzati |
| `context_budget.unit` / `context_window` | `tokens` / 70.000, conteggio nativo del modello |
| `synaptic.edge_upper` / `edge_target` | 50 / 45 archi esterni entranti + uscenti |
| `synaptic.automatic_sleep` / `idle_seconds` | true / 60 |
| `runtime.api.host` / `port` | `127.0.0.1` / 8765 |
| `frontend.enabled` | true; apertura automatica del cockpit incluso |
| `frontend.graph.node_limit` / `edge_limit` | 500 / 2.000, limiti grafici, non della memoria |

Nelle coppie la seconda chiave condivide il percorso padre della prima;
le altre chiavi abbreviate appartengono a `runtime`.
Su macchine senza CUDA adeguata scegliere `runtime.memory_backend: host`:
non prova la VRAM fisica. Non presumere che esista la GPU 1.
Adattare il percorso di storage su altre macchine o sistemi operativi.

Il ruolo LLM attivo è `runtime.adapter_role: orchestrator`, risolto tramite
`llm.active_runtime` e `llm.runtimes.<nome>.agents.<ruolo>`. Il profilo distribuito
usa `google/gemma-4-e2b` su `http://127.0.0.1:1234/v1`, gestione
`http://127.0.0.1:1234`, temperatura 0, timeout 180 secondi e nessuna opzione di
generazione forzata. Avviare il server LM Studio e installare prima il modello.

`rules` è un adapter esplicito di test deterministico, non un fallback automatico
quando l'LLM non risponde. Scegliere in tal caso un planner compatibile `rules` o
`hybrid`: il planner `llm` richiede un adapter con navigazione strutturata.

Tutti i budget di token, rubriche e manutenzione sono nel
[contratto](fase-1-sinapsi/28-contratto-utilizzo-memoria.md). I token limitano
il prompt, i byte i livelli fisici. Non sono un servizio di distillazione o
suddivisione automatica dei contenuti.

## Persistenza e frontend

Non usare il loader sostitutivo del seed per aggiungere conoscenza.
Inizializzazione vuota e verifica del seed conservano i nodi già presenti;
identità incompatibili richiedono migrazione esplicita o altro DB.
[Esempio produttore](../../examples/memory_contract.py).

Il server Python serve direttamente il frontend. Le vecchie chiavi
`frontend.directory`, `frontend.url` e `frontend.api_url` sono superate e
scartate dal loader. Nessun processo figlio Vite o porta frontend separata.
