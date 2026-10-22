# Adapter linguistici e conversazione libera

> **Documento storico — non guida operativa attuale.** Specifiche, default, risultati e passi successivi qui descritti appartengono alla fase registrata. Per ambito, API e comportamento vigenti leggere il [contratto attuale](fase-1-sinapsi/28-contratto-utilizzo-memoria.md). Le evidenze originali sono conservate.

Il Core di Luca non deve dipendere da un particolare modello linguistico. L'interpretazione a regole resta un fallback deterministico, mentre l'LLM può conversare liberamente e ricevere memoria recuperata come contesto.

```text
testo utente → recupero memoria → conversazione LLM → risposta naturale
     └─────────────────────────→ estrazione intento → validazione Core → memoria
```

## Contratto stabile

Un adapter può interpretare il linguaggio naturale in un `LanguageIntent` per il percorso della memoria:

- `greet`, `ask`, `describe`, `remember` o `unknown`;
- soggetto, predicato e uno o più oggetti normalizzati per `remember`;
- confidenza e nota di ambiguità quando opportuno.

Solo `MemoryEditor.consolidate()` può trasformare la proposta in celle durevoli, celle-assertion, archi ed eventi append-only. L'adapter non può scrivere direttamente su SQLite, scegliere gli ID interni o modificare un fatto esistente.

Il percorso conversazionale è distinto. `LMStudioAdapter.respond()` riceve un contesto di memoria limitato e la cronologia dialogica, poi restituisce una risposta naturale senza uno schema JSON obbligatorio. Il Core mantiene comunque ricerca, persistenza e tracciamento.

## Integrazione LM Studio

`LMStudioAdapter` usa un modello servito da LM Studio per due operazioni separate:

1. generare una risposta naturale usando memoria recuperata e cronologia;
2. estrarre la conoscenza durevole fornita dall'utente in una proposta strutturata.

L'LLM non possiede la conoscenza durevole, non scrive SQLite, non sceglie gli ID delle celle e non esegue il traversal del grafo. Il Core valida e consolida ogni proposta. Se il modello viene rimosso o non è disponibile, `RuleAdapter` resta un fallback funzionante e il database resta valido.

## Politica di sicurezza

- Una lezione ambigua può richiedere conferma e non viene salvata silenziosamente.
- Un'estrazione a bassa confidenza viene segnalata come incerta.
- Ogni assertion conserva origine e traccia dell'evento.
- I test devono usare lo stesso contratto per adapter a regole e micro-LLM.
