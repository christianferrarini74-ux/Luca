# LLM Connector

[English](../llm-connector.md) · [Indice](INDICE.md)

Guida attuale del confine, verificata il 2026-10-22.
L'esempio precedente è [archiviato](../history/llm-connector.it.md).

`luca_memory.llm.LLMConnector` risolve un ruolo configurato in profilo
provider/modello e crea un client chat. Client neutri e adapter applicativo sono
livelli distinti: configurare un client non certifica navigazione strutturata,
conteggio nativo dei token o gestione del modello per quel provider.

L'app distribuita usa `LMStudioAdapter`, scelto dal nome storico
`runtime.language_adapter: gemma`. Il modello configurato non deve
necessariamente essere Gemma. L'adapter richiede attualmente provider di tipo
`openai_compatible`, gestione modelli compatibile LM Studio e, con budget in
token, tokenizer nativo. Le altre implementazioni del connector non sono
automaticamente sostituti intercambiabili per questo percorso applicativo completo.

## Profilo distribuito

`llm.active_runtime` è `local`. Sotto `llm.runtimes.local` il provider
`lm_studio` usa `base_url: http://127.0.0.1:1234/v1` e
`management_url: http://127.0.0.1:1234`. Il ruolo `orchestrator` sceglie quel
provider, `google/gemma-4-e2b`, temperatura 0, timeout 180 secondi e
`generation: {}`. Le scelte sono in `config.yaml`, non nel codice del consumer.

L'adapter individua modelli installati/residenti e chiede, se necessario,
di caricare quello configurato già installato. Non scarica modelli, non avvia
LM Studio e non certifica un modello solo perché compare nell'elenco.

## Richieste e proprietà

Le istruzioni arrivano da `runtime.bible`; fatti runtime, testo utente e
cronologia sono dati. Navigazione e classificazione di manutenzione usano
output strutturato; la risposta finale può essere parte del risultato di
navigazione. Il JSON non è usato soltanto nell'acquisizione di fatti.

Il classificatore etichetta la rubrica orientata completa; il Core calcola i
gruppi e possiede le scritture. Vedere [classificazione](fase-1-sinapsi/32-classificazione-e-pianificazione-archi.md)
e [API d'integrazione](fase-1-sinapsi/28-contratto-utilizzo-memoria.md).

Gli errori del provider restano visibili, senza passaggio silenzioso alle regole.
I profili remoti del connector devono rispettare autenticazione/HTTPS previsti:
niente segreti nello YAML versionato. Provider diversi richiedono validazione
esplicita di adapter e capacità prima dell'uso.
