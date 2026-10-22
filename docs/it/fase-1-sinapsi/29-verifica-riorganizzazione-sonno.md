# Verifica della riorganizzazione nel sonno

> **Documento storico — non guida operativa attuale.** Specifiche, default, risultati e passi successivi qui descritti appartengono alla fase registrata. Per ambito, API e comportamento vigenti leggere il [contratto attuale](28-contratto-utilizzo-memoria.md). Le evidenze originali sono conservate.

2026-10-22. [English](../../sleep-reorganization-verification.md).
Accompagna il [contratto della memoria](28-contratto-utilizzo-memoria.md).

Checkpoint storico: la [successiva correzione dell'arresto all'obiettivo](30-arresto-riorganizzazione-obiettivo.md)
supera l'applicazione indiscriminata di tutti i gruppi validi qui registrata.
Le osservazioni originali, compreso il risultato tematicamente misto, restano intatte.

## Ambito e metodo

Simuliamo conoscenza e topologia, non l'implementazione della manutenzione.
`sleep_fixture.py` costruisce grafi temporanei tramite `SynapticMemory`;
`sleep_check.py` avvia il **vero** thread periodico `IdleMaintenance.start()`
con l'adapter LM Studio configurato. Nessun server applicativo, DB personale,
importatore PDF, distillatore o biblioteca. `maintenance.py`, config e Bibbia
di produzione restano invariati. Nessuna nuova dipendenza.

Il grafo ha 153 nodi originali: radice/indice, tre parti di contenuto, 52 vicini
esterni e due controlli indipendenti con 50 e 45 archi uscenti e relativi vicini.
Solo la radice con grado 52 è candidata al sonno. Gli archi familiari interni
non contano. I vicini alternano Botanica/Astronomia in entrambe le direzioni;
le categorie sono volutamente esplicite nei titoli. È una tassonomia facile e
controllata, non una biblioteca ambigua realistica. Gli input LLM contengono
solo rubrica e vincoli di produzione: nessuna istruzione con le categorie attese.

Soglie sempre 50/45. Il diagnostico riduce attesa d'inattività e controllo a un
secondo nella sola copia di configurazione, poi attende tempo realmente trascorso.
Non sostituisce il worker con `apply` e non inventa un orario d'inattività.
Il ripristino è una successiva operazione diagnostica esplicitamente confermata.
Il programma attende applicazione/errore del worker prima di arrestarlo e fare
join: il semplice ritorno della proposta non dimostrerebbe il commit.

```powershell
python -m unittest discover -s tests -p test_sleep_simulation.py -v
python -m luca_memory.sleep_check --repeat 2
```

Rapporti in `D:/Test/Luca/sleep-check-*.json`; i DB di prova sono temporanei e
rimossi al termine. `--model` modifica solo la configurazione diagnostica.
Lo script usa il caricamento LM Studio esistente e non scarica modelli dell'utente.
Campo `passed` e codice d'uscita riguardano i controlli strutturali, **non**
l'accettazione tassonomica: leggere `thematically_pure` e i titoli dei gruppi.
L'indicatore di purezza confronta i membri con le categorie controllate, non
certifica la correttezza del titolo assegnato: rimane necessaria l'ispezione umana.

## Accettazione strutturale

Per ogni operazione confermata, l'oracolo verifica:

1. Grado finale <=45; grado dei gruppi generati <=50.
2. Contenuto serializzato di tutti i nodi originali invariato.
3. Ogni rotta orientata originale conservata direttamente o attraverso un
   intermediario generato; identica raggiungibilità orientata fra **tutti** i
   nodi originali, non soltanto i vicini del focus.
4. Appartenenza familiare invariata e stessa rubrica completa dalle tre parti.
5. Controlli di grado 50/45 intatti.
6. Gruppi generati nel catalogo/indice d'ingresso, metadati originali invariati.
7. Stesse proprietà dopo chiusura e riapertura SQLite.
8. Ripristino confermato dopo riapertura: identica fotografia originale di
   contenuti, archi, uso, famiglia, catalogo, alias e indici di ricerca. Revisioni,
   audit e limite degli ID già confermati intenzionalmente non tornano indietro.
9. Worker arrestato con join, nessun thread diagnostico lasciato appeso.

## Evidenze con modello reale

Modello già caricato: `google/gemma-4-e2b` Q4_K_M. Nessun cambio di modello,
prompt o percorso semantico imposto. SHA-256 della Bibbia:
`a7326f92b597976edc837233fd5da81f6cd03d70db625e9a29901ac074b2f7c4`.

Coppia finale registrata:
`D:/Test/Luca/sleep-check-20261022-143525-384407.json`.

| Prova | Grado esterno | Gruppi | Durata worker | Struttura | Purezza tematica controllata |
| --- | --- | --- | ---: | --- | --- |
| 1 | 52 → 4 | 4 | 15,345 s | Tutto superato, compresi riapertura/ripristino | Membri omogenei; Botanica/Astronomia separate per direzione |
| 2 | 52 → 18 | 2 | 16,702 s | Tutto superato, compresi riapertura/ripristino | **Fallita**: tutti i 26 vicini uscenti in “Astronomia”, mescolando le due categorie |

La seconda prova ha anche raggruppato dieci Botanica entranti, lasciando altri
entranti diretti. Il Core accetta correttamente la riduzione strutturalmente
valida: non sa che il titolo del gruppo uscente è fuorviante. Un test di
regressione riproduce una proposta valida ma mista, verificando questa distinzione.

Evidenze preliminari conservate in
`D:/Test/Luca/sleep-check-20261022-142643-660994.json`: due prove strutturalmente
corrette, quattro gruppi omogenei ciascuna (16,196/15,329 s). Successivamente il
diagnostico è stato reso esplicito nell'attesa commit/errore prima dell'arresto,
ripetendo la coppia sopra. Non sostituire il risultato misto con le migliori
prove preliminari né trasformare pochi casi in una percentuale d'affidabilità.

L'obiettivo attuale significa **<=45**, non “fermarsi esattamente a 45” o
“modificare il minimo possibile”. Sia 4 sia 18 rispettano il contratto
implementato. Non c'è un ottimizzatore di raggruppamento minimo: caratteristica
esplicita, non vantaggio misurato. Questa prova sui metadati non dimostra
trasferimenti CUDA o prestazioni con contenuti grandi.

## Verifiche di guasti e concorrenza

Dodici nuovi test deterministici coprono soglie 50/45, polling reale,
annullamento per attività prima di una modifica in coda, arresto del worker
durante la proposta, sonno disabilitato, proposta invalida/attesa/nuovo tentativo,
piano obsoleto per modifica di un titolo vicino, rifiuto del ripristino dopo
modifica di un gruppo, rollback di eccezioni precommit e cicli ripetuti senza
riciclare ID confermati. Una parte familiare già residente aggiorna anche la
propria rubrica in cache dopo il raggruppamento e attraversa un gruppo generato
fino al contenuto originale, con livelli host da uno slot. È navigazione
strutturale, non un test della qualità delle risposte dell'LLM.

Un test avvia un processo Python separato sul DB temporaneo e termina con
`os._exit(73)` dopo tutte le scritture di riorganizzazione ma **prima del commit**.
Alla riapertura fotografia originale e revisione sono intatte,
`PRAGMA integrity_check` restituisce `ok`, nessuna operazione è confermata e
la manutenzione successiva funziona. È un crash del processo, non una prova di
perdita di alimentazione o guasto del dispositivo. L'attesa per l'annullamento
del provider mantiene la semantica reale dei timeout: nessuna cancellazione
HTTP forzata inventata.

Due ulteriori test del contratto eseguono l'esempio produttore, verificano archi
familiari canonici e rifiutano confusione fra revisioni globali/locali o
salvataggio di viste parziali. Risultati della suite nel checkpoint di consegna sotto.

## Conclusione

Il sonno esistente funziona strutturalmente nelle esecuzioni controllate: si
attiva, riduce il grado, conserva conoscenza/navigabilità, sopravvive alla
riapertura e consente ripristino protetto esatto. Non è servita una correzione
dell'algoritmo di produzione. **La qualità semantica dei gruppi non è garantita**,
neppure con titoli facili: una proposta reale ne mostra il limite. L'automatismo
convalida la struttura, non una valutazione semantica indipendente. Dove questa
distinzione conta è disponibile l'anteprima con conferma manuale. Migliorare
i gruppi o aggiungere una revisione opzionale richiederebbe un lavoro progettuale
distinto, non una modifica nascosta della Bibbia per far passare il test.

## Checkpoint di consegna

`python -m unittest discover -s tests -q`: 273 test, OK, sette verifiche opzionali
hardware/servizi saltate. `node --test tests/test_graph_frontend.js
tests/test_cockpit_frontend.js`: 19 superati. Ruff e `git diff --check` superati.
I 14 nuovi test sono 12 sul sonno e due sul contratto. Le chiamate al modello
reale sono separate dalla suite portabile e non annullano quelle esclusioni.
Gemma è rimasto caricato e inattivo; nessun modello dell'utente scaricato.
Questi diagnostici non hanno aperto database di memoria personali.
