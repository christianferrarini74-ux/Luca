# Luca

[English](README.md) | [Italiano](README.it.md)

Luca è un **sistema sperimentale di memoria sinaptica esterna per LLM**.
Gestisce nodi di conoscenza persistenti, indirizzi orientati, famiglie canoniche
e insiemi di lavoro limitati su SSD/RAM/VRAM. L'LLM fornisce linguaggio e
ragionamento; Luca fornisce memoria esplicita navigabile. Non è un nuovo LLM.

## Ambito

Luca gestisce storage, indici, focus/navigazione, modifiche atomiche e
riorganizzazione locale degli archi in inattività. I produttori esterni creano
e suddividono la conoscenza. Importazione PDF, distillazione, costruzione di
libri/biblioteche, addestramento LLM e integrazione Cesare sono fuori ambito.

Chat, mappa e cruscotto sono utilizzatori di prova: visualizzano e richiedono
operazioni del Core, senza implementare la memoria o certificare le risposte.

## Come funziona la memoria

- Il nodo contiene testo articolato, non necessariamente una parola. L'arco è
  la coppia orientata `(source_id, target_id)`, non un'asserzione semantica.
- Una famiglia è un padre A con parti An esplicite. Leggere una parte mantiene
  l'identità esterna A e la sua rubrica completa condivisa. I vicini ordinari
  non diventano automaticamente membri di famiglia.
- L'indice globale offre possibili ingressi ID/titolo. La rubrica rapida espone
  tutti gli indirizzi entranti/uscenti di primo grado e le parti, indipendentemente
  dalla residenza dei contenuti. Vedere un indirizzo non significa leggerne il nodo.
- SQLite conserva la fonte persistente; RAM host e, con backend CUDA, allocazioni
  GPU reali ospitano contenuti di lavoro limitati. La residenza GPU non equivale
  a conoscenza dell'LLM: il testo scelto deve comunque entrare nel prompt.
- Un runtime proprietario esegue modifiche atomiche con revisioni. SQL diretto e
  scrittori concorrenti indipendenti non sono interfacce d'integrazione supportate.

Nel sonno automatico sono candidati solo i padri oltre la soglia del grado
esterno. Con i valori distribuiti 50/45, l'LLM classifica tutto il vicinato per
argomento e un algoritmo deterministico costruisce i soli gruppi necessari
per arrivare a 45 esatto, se la capacità compatibile a un livello basta.
Classificazioni incerte o insufficienti non autorizzano mescolamenti.
Sono disponibili conferma manuale, annullamento alla ripresa dell'attività e
ripristino protetto.

Prima di produrre nodi leggere il [contratto](docs/it/fase-1-sinapsi/28-contratto-utilizzo-memoria.md);
prima di cambiare manutenzione leggere il [pianificatore](docs/it/fase-1-sinapsi/32-classificazione-e-pianificazione-archi.md).
L'[esempio eseguibile del produttore](examples/memory_contract.py) usa un DB nuovo,
non la memoria personale esistente.

## Avvio dell'applicazione di prova

Serve Python 3.11+. PyYAML è l'unica dipendenza applicativa dichiarata;
setuptools costruisce il pacchetto. Node.js non serve per avviare la GUI.

Dalla radice del repository, su Windows è consigliato un ambiente virtuale:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe run_luca.py
```

L'unico punto di avvio applicativo è `run_luca.py`: legge `config.yaml`, avvia
il server HTTP Python e apre il cockpit incluso su `http://127.0.0.1:8765/`.
Non serve una seconda shell per frontend, Vite o server Node. Usare **Esci**
per fermarsi ordinatamente; riavviare dopo modifiche a Python/configurazione.

Prima di avviare con la configurazione distribuita:

- Avviare il server locale LM Studio su `http://127.0.0.1:1234` e installare
  `google/gemma-4-e2b`. Luca chiede il caricamento del modello installato, ma non
  scarica modelli e non avvia LM Studio autonomamente.
- Verificare `storage.directory`, attualmente `D:/Test/Luca`, per questa macchina.
- Verificare `runtime.memory_backend` e `gpu_device`: il config usa storage CUDA
  reale sulla GPU con ordinale 1. Scegliere un dispositivo disponibile oppure
  `host` per livelli solo host; in tal caso non si prova la VRAM fisica.

Dettagli in [configurazione](docs/it/configuration.md), [cruscotto/API](docs/it/gui-runtime.md)
e [connettore LLM](docs/it/llm-connector.md). Il DB distribuito è
`luca_library.sqlite` con seed vuoto; dati sintetici separati.
Non aggiornare una biblioteca popolata tramite caricamento sostitutivo del seed.

## Verifiche e limiti

```powershell
python -m unittest discover -s tests -v
```

Ultimo checkpoint portabile: **300 test Python, OK con sette verifiche opzionali
hardware/servizi saltate**; 19 JavaScript e Ruff superati. Node serve soltanto
per i test di sviluppo frontend:

```powershell
node --test tests/test_graph_frontend.js tests/test_cockpit_frontend.js
```

Diagnostici opzionali su database temporanei:

```powershell
python -m luca_memory.sleep_check --repeat 2
python -m luca_memory.hardware_check
```

Il primo richiede LM Studio; il secondo un driver NVIDIA CUDA e dispositivo
adeguati. Prerequisiti nel contratto e precedenti prove hardware nei resoconti
storici. Verifiche saltate non equivalgono a una nuova esecuzione GPU.

Con la pipeline attuale, due prove E2B e due 26B A4B sul grafo controllato hanno
ottenuto tutte **52→45**, con rotte integre e riapertura/ripristino riusciti.
Non dimostrano correttezza semantica per qualunque argomento, storage infinito,
vantaggi universali di velocità o equivalenza al cervello umano. Titoli ambigui,
navigazione decisa dal modello e capacità di raggruppamento a un livello restano
limiti espliciti. Altri modelli/provider non sono automaticamente certificati.

## Documentazione

[Indice inglese](docs/README.md) | [Indice italiano](docs/it/INDICE.md).
Le guide attuali sono separate da progetti datati, esperimenti e istruzioni
d'avvio archiviate. I vecchi comandi demo ed esperimenti di apprendimento di
asserzioni rimangono nello storico, non come avvio raccomandato o scopo del prodotto.
