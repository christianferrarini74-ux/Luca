# Fase 1.11 — Esecuzione e accettazione

> **Documento storico — non guida operativa attuale.** Specifiche, default, risultati e passi successivi qui descritti appartengono alla fase registrata. Per ambito, API e comportamento vigenti leggere il [contratto attuale](28-contratto-utilizzo-memoria.md). Le evidenze originali sono conservate.

[English](../../phase-1-11-implementation.md)

Seguito: la [verifica reale con LM Studio](13-verifica-live-lmstudio.md) registra
correzioni successive e limiti residui su richiamo e nomi dei gruppi. I checkpoint
seguenti conservano le evidenze del momento dell'implementazione.

Ambito: realizzare la [specifica confermata](11-memoria-sinaptica-riorganizzabile.md),
non importazione libri, distillazione o integrazione Cesare. I test automatici e
gli script di sviluppo non utilizzano né riscrivono i database personali.

1. Fondamenta persistenti: famiglia a stella esplicita, identità canonica,
   modifiche transazionali, revisioni, alias correnti e ricerca globale.
   Verifiche: rollback, rinomina, riavvio e compatibilità dei nodi ordinari.
2. Rubrica rapida completa di primo grado, indipendente dalla residenza dei
   contenuti. Verifiche: entranti/uscenti, continuità familiare e invalidazione
   delle copie obsolete, anche quando fallisce un'allocazione GPU. Nessun taglio
   silenzioso dei riferimenti di navigazione.
3. Navigazione LLM: protocollo limitato cerca/apri/rispondi; il Core verifica ID,
   revisioni e percorsi, senza sostituirsi nella scelta semantica. La modalità
   precedente a regole resta disponibile come configurazione esplicita di test.
4. Manutenzione: soglie configurabili, piani manuali con conferma e avvio automatico
   in inattività, raggruppamenti orientati, verificabili e reversibili. Verifiche:
   rotte originali, piani obsoleti, rollback e riduzione del grado locale.
5. Integrazione: visibilità API/cruscotto, test deterministici completi, suite
   portabile e verifiche CUDA reali opzionali. Registrare qui e nei README bilingui
   risultati e limiti residui; commit dei passaggi verificati.

Stato implementativo e risultati vengono registrati di seguito durante il lavoro.

Checkpoint fondamenta: implementati famiglie canoniche, rubrica completa,
migrazione additiva revisioni/catalogo, modifiche atomiche e slot host/device
consapevoli della revisione. Suite portabile: 116 test, 3 verifiche hardware
saltate. Il vecchio test che equiparava primo grado e contenuti precaricati ora
verifica separatamente le due proprietà. Nessun database personale aperto.

## Runtime implementato

I cinque blocchi esecutivi sono implementati. Questo non significa che la qualità
dei raggruppamenti o la navigazione del modello siano già validate su una biblioteca.

- `SynapticMemory`: famiglia canonica esplicita, rubrica esterna condivisa, alias
  generati correnti, ricerca globale FTS/esatta e modifiche atomiche.
- `MemoryNavigator`: ricerca/apertura/risposta decise dall'LLM, rubriche orientate
  complete ID/titolo, scelta dell'ingresso, verifica delle rotte e passi limitati.
- Slot con revisione: le copie host/device obsolete sono scartate prima della
  lettura. Un fallimento GPU non annulla la conoscenza confermata né espone la
  vecchia copia.
- `MemoryMaintenance`: piani verificati per revisione, conferma manuale, gruppi
  entranti e uscenti separati, registro delle rotte originali e ripristino protetto.
  I nodi G hanno identità propria e non possono diventare frammenti di contenuto.
- `IdleMaintenance`: worker posseduto e arrestabile, serializzato con chat/LLM.
  Ammessi solo gradi esterni > limite superiore. Se arriva attività durante la
  generazione della proposta, il piano non viene applicato. Una transazione atomica
  già iniziata termina prima della chat. La generazione HTTP del modello in corso
  non viene interrotta forzatamente: ingresso utente/arresto possono attendere il
  timeout configurato del provider.
- Il cruscotto Python mostra indici, focus canonico/di lettura, anteprima/conferma
  e ripristino. L'aggiornamento della vista non richiama l'LLM né conta come attività
  dell'utente. Le vecchie viste prefisso/suffisso restano diagnostica dei vicinati,
  non deducono appartenenze alle famiglie di contenuto.

## Configurazione e utilizzo

Unico avvio: `python run_luca.py`. Avviare prima il server di LM Studio; il
connector esistente continua a caricare il modello installato configurato.
La memoria runtime resta in `D:/Test/Luca`. Nessun nuovo pacchetto introdotto.

`runtime.memory_planner: llm` attiva il nuovo protocollo. `rules` e `hybrid`
mantengono il planner precedente; l'adapter a sole regole non supporta `llm`.
Tutti i nuovi parametri operativi sono in `runtime.synaptic`:

| Chiave | Valore distribuito | Significato |
| --- | ---: | --- |
| `edge_upper` / `edge_target` | 50 / 45 | Grado esterno familiare, entranti + uscenti |
| `navigation_steps` | 8 | Massimo chiamate cerca/apri/rispondi per turno |
| `global_candidates` | 20 | Risultati globali dichiaratamente limitati; affinare la ricerca |
| `fast_index_bytes` | 65536 | Budget serializzato della rubrica in RAM host |
| `automatic_sleep` | true | Abilita raggruppamento in inattività oltre il limite superiore |
| `idle_seconds` / `sleep_poll_seconds` | 60 / 5 | Soglia inattività / controllo worker |
| `sleep_retry_seconds` | 300 | Attesa prima di ritentare una proposta fallita invariata |

Il primo grado non viene tagliato per adattarlo agli slot o al prompt. Superare
il budget della rubrica/contesto produce un errore esplicito: aumentare il budget
o riorganizzare il nodo. Solo il contenuto selezionato può essere mostrato per
estratti; la fonte completa rimane persistente. Splittaggio in parole e indice
opzionale di secondo grado restano rinviati. Il prompt usa ancora byte UTF-8
conservativi, non token esatti.

Nel cruscotto, “Rubrica sinaptica” consente ricerca globale e navigazione locale.
Per la manutenzione manuale, scegliere il nodo, preparare l'anteprima e confermare
il piano. Alla soglia obiettivo o sotto è un no-op. L'automatica interviene solo
oltre il limite superiore, non per il semplice superamento dell'obiettivo.
Proposte LLM non valide non modificano nulla. Al prossimo avvio avviene la
migrazione additiva di schema/catalogo: non sostituisce la conoscenza personale
con il seed né deduce famiglie da stelle già esistenti.

## Confini Core/API

Un solo runtime possiede la connessione allo store; modifiche e letture Core nello
stesso processo condividono un lock rientrante. Contenuto, catalogo/ricerca, alias,
revisioni ed eventi vengono confermati insieme in SQLite. Le revisioni sono marcatori
monotoni delle modifiche, non contatori delle operazioni utente. Il rinforzo d'uso
non invalida i contenuti. Scritture SQL dirette e runtime indipendenti che scrivono
contemporaneamente non sono interfacce supportate di modifica.

| Endpoint POST | Contratto |
| --- | --- |
| `/api/memory/search` | `query` → candidati globali ID/titolo limitati |
| `/api/memory/navigate` | `target_id`, `directory_revision` → passo locale verificato |
| `/api/memory/node` | `node_id`, `title`, `content`, `expected_revision` → upsert atomico |
| `/api/memory/edge` | `source`, `target`, `remove` opzionale, `expected_revision` |
| `/api/memory/family` | `root`, `part`, `expected_revision` → famiglia a stella esplicita |
| `/api/maintenance/preview` | `node_id`, `groups` opzionali → piano e `plan_id` temporaneo |
| `/api/maintenance/apply` | `plan_id`, `confirmed: true` → raggruppamento atomico |
| `/api/maintenance/restore` | `operation_id`, `confirmed: true` → ripristino protetto |

Creare nodi con ID nuovi (`store.next_cell_id()` nel Core). Gli ID allocati
automaticamente non sono riutilizzati dopo il ripristino. Revisioni e piani
obsoleti vengono rifiutati. Una nuova anteprima sostituisce quella pendente;
le operazioni confermate restano persistenti dopo il riavvio (il cruscotto ne
mostra le ultime 20). Il ripristino rimuove soltanto i gruppi originali non
modificati: si rifiuta se contenuto, alias, famiglia o rotte incidenti sono cambiati.
Conserva il rinforzo delle rotte sostitutive. Richieste di modifica cross-origin
sono rifiutate.

## Verifiche e limiti

Suite portabile: 148 test, con quattro test CUDA opzionali saltati normalmente.
L'ultima esecuzione hardware e le verifiche aggiuntive vengono registrate nel
checkpoint di consegna sotto. Sintassi JavaScript verificata con `node --check`:
Node serve soltanto come controllo di sviluppo, non per avviare Luca.

Coperti migrazione senza sostituire le fonti, rollback atomico, lettori concorrenti,
fallimento ricarica cache, rubrica oltre il precaricamento, continuità familiare,
richieste reali dell'adapter, navigazione invalida/ciclica, gruppi orientati, piani
obsoleti, conferma, annullamento/backoff in inattività, ripristino protetto e HTTP.
Nessun database personale aperto. LM Studio su `127.0.0.1:1234` non era in ascolto:
le nuove decisioni sono state verificate con adapter controllati e risposte simulate
del connector, non dichiarate come conversazione Gemma reale riuscita. Quest'ultima
prova resta da fare con LM Studio disponibile; la biblioteca reale resta lavoro
congiunto. Non inclusi PDF, distillazione dei contenuti o integrazione Cesare.

### Checkpoint di consegna — 2026-10-21

`LUCA_TEST_CUDA=1 python -m unittest discover -s tests`: **148 test superati**, senza
skip, comprese quattro prove NVIDIA CUDA reali sulla GPU separata configurata.
Superati anche `python -m compileall -q luca_memory`,
`node --check luca_memory/web/app.js` e `git diff --check`. Queste verifiche non
dichiarano una conversazione LLM reale né una verifica visiva nel browser.
Entry point e insieme delle dipendenze applicative invariati.
