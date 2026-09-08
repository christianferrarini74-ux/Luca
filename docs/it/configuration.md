# Configurazione di Luca

Luca ha un solo file di configurazione del runtime: `config.yaml` nella radice
del repository. Il punto di avvio configurato è:

```powershell
python run_luca.py
```

Il file controlla percorsi di storage, indirizzo API, directory e URL del
frontend, adapter linguistico e runtime LLM selezionato dal connector. Il
runtime lo carica una volta e costruisce il resto del sistema a partire da quella
configurazione.

La configurazione predefinita seleziona l'adapter Gemma locale:

```yaml
runtime:
  language_adapter: gemma
```

Avviare LM Studio e configurare il provider OpenAI-compatible nella sezione
`llm.runtimes` prima di inviare il primo messaggio. Impostare `rules` solo per
i test deterministici offline.

Le demo CLI possono ancora usare flag espliciti; il runtime della dashboard no.
In questo modo le scelte di avvio restano in un unico file ispezionabile.

I file della memoria runtime sono mantenuti fuori dal codice sorgente. La
configurazione attuale usa `D:/Test/Luca` per il database SQLite e per i futuri
file persistenti della memoria; il seed versionato resta nella cartella `seed/`
del repository.
