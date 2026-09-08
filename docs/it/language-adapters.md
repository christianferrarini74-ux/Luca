# Adapter linguistici sostituibili

Il Core di Luca non deve dipendere da un particolare modello linguistico. La prima implementazione usa regole italiane deterministiche; un micro-LLM locale è una sostituzione opzionale di quel componente, non un nuovo Core cognitivo.

```text
testo utente
   |
   v
LanguageAdapter  ->  LanguageIntent  ->  Luca Core / MemoryEditor
                                                   |
                                                   v
                                             EvidenceBundle
```

## Contratto stabile

Un adapter può interpretare il linguaggio naturale in un `LanguageIntent`:

- `greet`, `ask`, `describe`, `remember` o `unknown`;
- soggetto, predicato e uno o più oggetti normalizzati per `remember`;
- confidenza e nota di ambiguità quando opportuno.

Solo `MemoryEditor.consolidate()` può trasformare la proposta in celle durevoli, celle-assertion, archi ed eventi append-only. L'adapter non può scrivere direttamente su SQLite, scegliere gli ID interni o modificare un fatto esistente.

Le risposte del Core sono fondate in un `EvidenceBundle`: testo, traccia del grafo e ID delle assertion usate. Un futuro adapter potrà rendere il testo più naturale, ma deve conservarne il significato e non introdurre fatti assenti dal bundle.

## Integrazione LM Studio

L'adapter `LMStudioAdapter` usa un modello servito da LM Studio solo per classificare l'enunciato nello schema stabile, estrarre una lezione normalizzata e, in futuro, rendere più naturale una risposta italiana del Core.

Non possiede la conoscenza durevole, non decide la persistenza, non esegue il traversal del grafo e non sintetizza informazioni non supportate. Se il modello viene rimosso o non è disponibile, `RuleAdapter` resta un fallback funzionante e il database resta valido.

## Politica di sicurezza

- Una lezione ambigua può richiedere conferma e non viene salvata silenziosamente.
- Un'estrazione a bassa confidenza viene segnalata come incerta.
- Ogni assertion conserva origine e traccia dell'evento.
- I test devono usare lo stesso contratto per adapter a regole e micro-LLM.
