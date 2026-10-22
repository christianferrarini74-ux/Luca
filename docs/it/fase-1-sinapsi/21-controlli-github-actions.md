# Controlli GitHub riproducibili — 2026-10-22

[English](../../github-actions-checks.md)

Il precedente controllo remoto falliva in Ruff, prima di eseguire i test.
La deprecazione di Node.js 20 e la migrazione di `ubuntu-latest` erano avvisi
distinti. Il workflow aggiunto direttamente su GitHub è stato integrato nella
cronologia locale non ancora pubblicata, senza scartare nessuno dei due percorsi.

## Modifiche

- Ruff 0.17.1 è fissato nella CI e richiesto dalla configurazione dello strumento,
  con Python 3.11 come destinazione. Correzioni automatiche sicure e interventi
  manuali verificati allineano codice e test alle regole già presenti.
- Restano invariati i contratti di validazione `ValueError` e le catture generali
  intenzionali ai confini HTTP, nei worker e nelle verifiche diagnostiche:
  le eccezioni al lint sono puntuali e motivate nei commenti.
- Checkout/setup-python/setup-node passano alla versione 6; i test frontend usano
  Node.js 24. La matrice seleziona esplicitamente Ubuntu 24.04 e Windows 2025.
- La CI installa il progetto con `pip install -e .`, compresa PyYAML già dichiarata.
  Esegue la suite unittest della libreria standard, senza introdurre pytest,
  e successivamente entrambi i file di test JavaScript.
- Nessuna nuova dipendenza applicativa, modifica alla Bibbia o migrazione della
  memoria personale. Ruff è uno strumento di sviluppo; Node serve a questi test.

## Verifiche locali

Ruff non segnala errori. Passano tutti i 235 test Python con CUDA reale e
tokenizzazione nativa di LM Studio abilitate, oltre ai 19 test JavaScript.
Passa anche un'installazione editable separata: 235 test Python individuati,
sette dei quali intenzionalmente saltati perché dipendono da hardware/servizi,
e 19 test JavaScript. La CI cloud segue quest'ultimo contratto e non richiede
GPU o LM Studio. Queste verifiche non dimostrano qualità conversazionale o
prestazioni su biblioteche estese.
