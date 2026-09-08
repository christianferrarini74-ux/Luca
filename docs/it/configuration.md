# Configurazione di Luca

Luca ha un solo file di configurazione del runtime: `config.yaml` nella radice
del repository. Il punto di avvio configurato è:

```powershell
python -m luca_memory
```

Il file controlla percorsi di storage, indirizzo API, adapter linguistico e
runtime LLM selezionato dal connector. Il runtime lo carica una volta e costruisce
il resto del sistema a partire da quella configurazione.

Impostare:

```yaml
runtime:
  language_adapter: rules
```

su `gemma` solo dopo aver avviato LM Studio e configurato il provider
OpenAI-compatible nella sezione `llm.runtimes`.

Le demo CLI possono ancora usare flag espliciti; il runtime della dashboard no.
In questo modo le scelte di avvio restano in un unico file ispezionabile.
