# Contratto di utilizzo e integrazione della memoria di Luca

2026-10-22. [English](../../memory-integration-contract.md).

Questa è la guida attuale per produttori e utilizzatori esterni.
Politica automatica attuale: [classificazione e pianificazione algoritmica](32-classificazione-e-pianificazione-archi.md).
I documenti
precedenti rimangono testimonianze storiche. Il pacchetto applicativo è alla
versione 0.1.0: questa guida non introduce una versione indipendente del
protocollo né promette una retrocompatibilità non ancora stabilita dal progetto.

## 1. Confine delle responsabilità

Luca conserva, indicizza, collega, apre e riorganizza conoscenza. **Non produce
i nodi**, non importa PDF, non divide libri, non distilla contenuti e non
costruisce biblioteche. Queste operazioni e le relative decisioni semantiche
appartengono ai programmi esterni. Chat e cruscotto sono utilizzatori di prova,
non la logica della memoria. La Bibbia configura l'interfaccia LLM, non è un
formato di acquisizione; modificarla non rientra in questo intervento.

Il produttore deve fornire identificatori validi, titoli significativi, contenuti
completi, appartenenze familiari esplicite e archi orientati intenzionali. Luca
garantisce le operazioni strutturali descritte, non la verità dei contenuti, la
verifica delle fonti, una tassonomia ottimale o il ragionamento dell'LLM consumer.

## 2. Rappresentazione del nodo

Utilizzare `KnowledgeNode` di `luca_memory.node` e salvarlo con
`SynapticMemory.update_node`. È un record Python, non un file JSON da scrivere
direttamente dentro SQLite.

| Campo | Contratto del produttore / significato attuale |
| --- | --- |
| `id` | Intero positivo, stabile nel singolo DB. Leggere `store.next_cell_id()` e inserire mantenendo la stessa transazione/lock. La funzione calcola il prossimo ID: non lo prenota. |
| `slug` | Chiave testuale stabile non vuota, con namespace distinguibile. Diversamente dagli slug dei seed, l'unicità generale non è imposta. |
| `title` | Nome significativo non vuoto, utilizzato nell'ingresso e nelle rubriche. Può non essere unico: l'identità è l'ID intero. |
| `content` | Testo Unicode completo, fonte persistente della conoscenza. Può essere vuoto per un indice, ma non sostituisce un archivio esterno di contenuti. |
| `keywords` | Tupla opzionale di stringhe ricercabili. Slug, titolo e parole chiave alimentano alias normalizzati e indice d'ingresso. |
| `summary` | Testo opzionale, non distillato automaticamente né necessariamente usato dal navigatore in sostituzione del contenuto. |
| `sections` | Tupla opzionale di `KnowledgeSection(key, title, content)` con chiavi non vuote e uniche. Le sezioni non sono nodi: niente ID o archi indipendenti. |
| `created_at` | Secondi Unix; zero assegna l'ora corrente in serializzazione. Negli aggiornamenti preservare il record esistente. |
| `last_recalled_at`, `recall_count` | Informazioni d'uso gestite dal runtime, non verità dichiarate dal produttore né revisioni semantiche. |
| `content_complete`, `full_content_bytes` | Metadati delle viste di cache. Una vista parziale (`content_complete=False`) non può sovrascrivere il nodo persistente. Non sono un'interfaccia di suddivisione. |

Sono requisiti d'integrazione, non una dichiarazione che il costruttore della
dataclass convalidi ogni campo. Alcuni percorsi bassi accettano titoli vuoti o
chiavi duplicate: il produttore non deve affidarsi a questa permissività.
Persistenza di viste parziali e vincoli strutturali sono controllati dal Core.
Per modificare senza perdere campi opzionali usare `load_node` e
`dataclasses.replace`.

Non esistono campi strutturati dedicati a fonte, pagina, data o confidenza.
Registrare identificativo della fonte, revisione, pagina/sezione e ambito in
`content` o nelle sezioni quando necessari. Luca li conserva come testo: non
risolve automaticamente conflitti tra versioni. Un arco non certifica una fonte.

## 3. Archi orientati e famiglie canoniche

Un arco è la coppia ordinata `(source_id, target_id)`, concettualmente
`prefisso:suffisso`. Non richiede un'etichetta semantica o un peso. I contatori
d'uso sono metadati del runtime. Entrambi i nodi devono esistere. La coppia è
unica: reinserirla non duplica l'arco; invertirla crea un arco distinto.
Sono supportati autoarchi: A→A conta una volta tra gli entranti e una tra gli
uscenti, quindi grado due. Il focus stesso non può diventare membro di un gruppo.

Un nodo centrale con vicini **non è automaticamente una famiglia di contenuto**.
Creare A, A1 e A2 indipendenti, poi `attach_part(A, A1)` e `attach_part(A, A2)`.
La famiglia è la stella esplicita A più le sue parti:

- `root(A1) == A`; `parts(A)` elenca le parti. Le famiglie non possono essere
  annidate; una parte già collegata non può avere parti o appartenere a due famiglie.
- Leggere A1 mantiene `reading_id=A1`, ma identità esterna/focus A. Padre e parti
  espongono la stessa rubrica esterna completa e lo stesso elenco delle parti.
- Gli archi esterni sono su A, non copiati in liste indipendenti su A1/A2.
  Collegare A1 a B tramite il Core memorizza A→B; anche una destinazione che sia
  parte di famiglia viene ricondotta alla propria radice.
- Collegare come parte un nodo indipendente già esistente trasferisce i suoi
  archi esterni su A e deduplica le coppie: è una modifica reale, non un'etichetta
  grafica. I precedenti collegamenti interni padre/parte diventano la stella canonica.
- Le parti non contano nel grado esterno di A, ma ID/titolo occupano spazio nella
  rubrica e nel prompt. Non esiste un limite configurato al numero di parti.

I nodi di raggruppamento G sono differenti: A→G→B oppure B→G→A riduce il grado
esterno di A. G ha identità e rubrica proprie, non appartiene all'identità della
famiglia A. Un G generato ancora attivo non può diventare frammento di contenuto.
Può servire un'apertura in più: non assumere che l'arco diretto originario resti.

Valido: chiedere A1→B con `memory.connect`, ottenendo A→B.
Non valido: annidare figli sotto A1 già parte di A; estremi inesistenti;
scritture SQL di archi esterni sulle parti; salvataggio di una vista troncata.
Non c'è una migrazione pubblica per separare/eliminare famiglie: niente SQL inventato.

## 4. Indici, letture e limiti

L'indice globale d'ingresso usa titolo/slug/parole chiave. La ricerca esplicita
`global_lookup` usa alias e ricerca testuale sul testo memorizzato. Restituiscono
candidati ID/titolo limitati, non garanzie di completezza semantica o contenuti
già letti. Gli alias normalizzano maiuscole, accenti e spazi; collisioni possono
restituire più nodi.

`directory(node_id)` restituisce `focus_id`, `revision`, `incoming`, `outgoing`,
`parts`; ogni voce ha solo `id` e `title`. Include tutti gli indirizzi di primo
grado indipendentemente dalla residenza dei contenuti su SSD, RAM o VRAM.
Vedere un titolo o precaricare un vicino non equivale a leggerne il contenuto.
L'indice di secondo grado non fa parte del contratto attuale. Dopo una modifica,
aggiornare rubriche e risultati di ricerca.

| Configurazione (`config.yaml`) | Valore distribuito attuale | Effetto |
| --- | ---: | --- |
| `runtime.synaptic.edge_upper` / `edge_target` | 50 / 45 | Somma entranti + uscenti esterni. Sonno automatico solo oltre il superiore; pianificazione da categorie all'obiettivo esatto se la capacità compatibile basta. I gruppi concreti espliciti conservano la selezione intera più vicina. Sforamento temporaneo ammesso. |
| `navigation_steps` / `global_candidates` | 8 / 20 | Massimo azioni del modello per turno / risultati globali. Non sono dimensioni massime del grafo. |
| `fast_index_bytes` | 65536 | Spazio serializzato della rubrica completa in byte UTF-8. Nessun taglio silenzioso degli archi. |
| `automatic_sleep` / `idle_seconds` | true / 60 | Abilitazione sonno / soglia d'inattività. |
| `sleep_poll_seconds` / `sleep_retry_seconds` | 5 / 300 | Intervallo controlli / attesa dopo proposta fallita con rubrica invariata. |
| `maintenance_output_tokens` | 8192 | Generazione massima del modello per proposta di raggruppamento. |
| `runtime.context_budget.unit` / `context_window` | tokens / 70000 | Conteggio nativo del modello e budget di contesto configurato. |
| `memory_limit` / `per_node_limit` | 20000 / 16000 | Budget dell'area delle letture e del testo di una lettura: non dimensioni massime del nodo persistente. |
| `history_limit` / `task_limit` | 40000 / 2048 | Budget cronologia e compito. |
| `output_reserve` / `framing_reserve` | 4096 / 512 | Riserve risposta e cornice; l'output può cambiare secondo l'operazione. |
| `runtime.vram_capacity` / `ram_capacity` | 5 / 12 | Slot dei contenuti. |
| `runtime.vram_bytes` / `ram_bytes` | 8000000 / 32000000 | Capacità serializzate dei livelli in byte, distinte dai token del prompt. |

Le impostazioni sinaptiche richiedono interi positivi, `edge_upper>=3` e
`2<=edge_target<edge_upper`. Altre installazioni possono scegliere altri valori.
Gli oggetti Core usati senza config applicativa hanno default propri: la tabella
non è un insieme di limiti universali hardcoded.

Nessuno splittaggio automatico per parole o limite in token al nodo persistente.
Il produttore decide la suddivisione rispetto a tokenizer/budget del consumer.
Il testo lungo può apparire come estratto marcato parziale, ma resta completo
su SSD. La rubrica completa ha priorità: se non entra, errore esplicito anziché
archi nascosti. I livelli CUDA conservano payload serializzati completi, non
nodi arbitrariamente ridotti: non presumere caricabile un contenuto più grande
della capacità del singolo livello. In modalità host sono possibili viste
compattate. Nessuna promessa di SSD indipendente dalle dimensioni o contesto infinito.

## 5. Scritture, atomicità e proprietà

Un solo runtime/connessione possiede lo store. Il lock rientrante serializza
lettori, modifiche e manutenzione. Transazioni/savepoint SQLite confermano insieme
contenuti, catalogo, alias, indici testuali/d'ingresso, revisioni ed eventi.
Usare `with store.transaction():` per un lotto di nodi/archi/famiglie.
Richieste HTTP separate non formano una transazione unica.

`expected_revision` delle modifiche Core è la revisione **globale**
`store.revision`, non quella della rubrica del focus. Se obsoleta, viene sollevato
`StaleRevision`: aggiornare i dati e riconsiderare la modifica, non forzarla.
Il Core può omettere il controllo solo quando il chiamante possiede
intenzionalmente la serializzazione. HTTP lo richiede. Diversamente,
`validate_step(reading_id,target,directory_revision)` controlla la revisione
locale della rubrica. Rinforzi d'uso non sono modifiche strutturali.

Gli ID confermati non vengono riciclati, neppure dopo il ripristino dei gruppi.
Un'allocazione annullata dal rollback non è mai stata confermata e può essere
riutilizzata. Cambiare titolo aggiorna anche indici e rubriche interessate;
le copie dei livelli obsolete sono invalidate prima dell'uso. Un errore di
allocazione GPU non annulla un contenuto già confermato né deve far riapparire
la vecchia vista. SQL diretto, scrittori esterni sul file attivo, runtime
indipendenti che scrivono insieme e prenotazioni ID tra processi non sono
interfacce d'integrazione supportate.

## 6. Esempio eseguibile per il produttore

[examples/memory_contract.py](../../../examples/memory_contract.py) crea indice,
due parti e un riferimento esterno in una transazione, poi mostra un aggiornamento
che preserva i metadati. Rifiuta store non vuoti. Dalla radice del repository,
con pacchetto installato/editabile e file d'uscita **nuovo**:

```powershell
python -m examples.memory_contract --database D:/Test/Luca/contract-example.sqlite
```

L'esempio stabilisce l'identità del seed biblioteca vuota; l'avvio con lo stesso
seed può così conservare i nodi aggiunti. `ensure_knowledge_seed` controlla
l'identità del seed esistente: non importa contenuti in modo incrementale.
Non utilizzare `load_knowledge_seed` per aggiungere un documento: quel caricatore
esplicito **sostituisce** i contenuti del grafo. Il JSON dei seed è un formato
di inizializzazione/prova, non il contratto incrementale dei produttori, e non
codifica l'appartenenza esplicita alle famiglie.

## 7. Interfaccia HTTP locale esistente

Base predefinita `http://127.0.0.1:8765`: è l'interfaccia locale dell'applicazione
di prova, non un servizio remoto multiutente autenticato. `GET /api/state`
espone `synaptic.revision` e focus/rubrica correnti. Gli endpoint seguenti sono
POST con oggetto JSON; le modifiche restituiscono `state`, salvo indicazione diversa.

| Percorso | Richiesta / risultato |
| --- | --- |
| `/api/memory/search` | `{ "query": "Atlas" }` → `{ "revision": ..., "candidates": [{"id":...,"title":...}] }`. |
| `/api/recall` | `{ "node_id": 1 }` → apre un ingresso esplicito noto, restituisce stato. |
| `/api/memory/navigate` | `{ "target_id": 2, "directory_revision": 123 }`; servono focus di lettura e indirizzo locale valido e aggiornato. |
| `/api/memory/node` | `{ "node_id": 1, "title": "Atlas", "content": "...", "expected_revision": 123 }`; crea/aggiorna titolo e contenuto. |
| `/api/memory/edge` | `{ "source": 1, "target": 4, "expected_revision": 123 }`; aggiunge; `"remove":true` rimuove. |
| `/api/memory/family` | `{ "root": 1, "part": 2, "expected_revision": 123 }`; entrambi i nodi devono esistere. |
| `/api/maintenance/preview` | `{ "node_id": 1 }` interpella l'adapter; oppure fornire `"groups":[{"title":"Tema","direction":"outgoing","members":[2,3]}]`. Restituisce `plan_id`, `plan`. |
| `/api/maintenance/apply` | `{ "plan_id": "...", "confirmed": true }` → `operation_id`, `state`. |
| `/api/maintenance/restore` | `{ "operation_id": 1, "confirmed": true }` → stato dopo il ripristino protetto. |

I numeri sono segnaposto: ottenere ID/revisioni correnti, non copiarli come
precondizioni. L'HTTP non espone tutti i campi di `KnowledgeNode`, allocazione ID,
lotti atomici o separazione famiglie. I nuovi nodi HTTP ricevono `slug=node_<id>`;
gli aggiornamenti preservano gli altri campi già presenti. Non aspettarsi che
campi JSON aggiuntivi importino metadati. Per l'interfaccia completa e gli ID
coordinati usare il Core nel runtime proprietario.

Richieste non valide e revisioni obsolete restituiscono HTTP 400
(`{"error":"..."}`), non 409; errori inattesi del backend restituiscono 500.
Modifiche cross-origin rifiutate con 403. Limite corpo memoria/manutenzione:
2.000.000 byte, non un limite al contenuto in token. Una nuova anteprima
sostituisce quella pendente; le operazioni confermate sopravvivono al riavvio.

## 8. Semantica del sonno e dei fallimenti

La manutenzione manuale richiede anteprima e conferma esplicita; può intervenire
sopra l'obiettivo anche sotto/al limite superiore. Il sonno automatico seleziona
solo identità canoniche indipendenti con grado esterno **maggiore** del limite
superiore. I collegamenti familiari interni non lo attivano. Al limite obiettivo
o sotto, la manutenzione manuale non fa nulla.

L'LLM riceve la rubrica completa (ID/titoli), non contenuti o calcoli sugli archi.
Servono titoli informativi. Restituisce una `ClassifiedDirectory` completa:
ogni ID esterno per direzione ha titolo di categoria da 1 a 256 caratteri o
null esplicito se incerto. Le omissioni non sono valide. Focus e parti interne
sono esclusi. Le categorie possono avere qualunque dimensione: non sono nodi
di navigazione. Il Core riconvalida copertura, etichette, ID e revisione locale.

Il Core costruisce gruppi disgiunti da 2 a `edge_upper-1` membri della stessa
categoria e direzione, lasciando diretti indirizzi inutilizzati, null o singoli.
Riduzione `sum(numero_membri-1)`. L'ultimo gruppo può usare parte della categoria
per arrivare esattamente a `edge_target`. Capacità compatibile insufficiente
a un livello: errore senza scritture, mai mescolando temi. Nessun contenuto
diviso. Anteprima e ripristino descrivono solo i gruppi operativi applicati.

Un utilizzatore Core può chiamare `classification_from_assignments(value,
directory)` da `luca_memory.classification` e passare il risultato a
`MemoryMaintenance.plan`. Esempio e limiti di capacità nella
[specifica del pianificatore](32-classificazione-e-pianificazione-archi.md).
L'anteprima locale predefinita usa automaticamente questo percorso. Liste HTTP
`groups` e adapter personalizzati che restituiscono gruppi concreti restano un
percorso compatibile distinto: selezione di gruppi interi con minimo scarto,
senza dividerli. Validità strutturale e copertura completa non certificano la semantica.

Un controllo del worker tenta al massimo un candidato. Gli errori restano visibili;
i tentativi falliti hanno un'attesa basata sulla revisione della rubrica. Nessuna
proposta invalida modifica il grafo. Il lock proprietario serializza chiamate LLM
e scritture; la ripresa dell'attività viene segnalata **prima** dell'attesa del lock
e annulla la proposta automatica pendente prima dell'applicazione. Anche l'arresto
annulla una proposta restituita ancora pendente e attende il worker. Non interrompe
forzatamente la generazione HTTP in corso: l'attesa può durare fino al timeout del
provider. Una transazione atomica già avviata termina prima della richiesta in coda.

L'applicazione conserva archi originali e dati di ripristino nella stessa
transazione. Il ripristino richiede conferma e rifiuta di cancellare modifiche
a gruppi generati, alias, appartenenze familiari o rotte incidenti. Conserva il
rinforzo d'uso delle rotte. Non è un rollback universale delle modifiche successive
alla conoscenza. Eseguire backup SQLite coerenti con WAL o a runtime arrestato,
non copiando solo il file `.sqlite` attivo. Testato il recupero dopo crash del
processo, non certificata la resistenza alla perdita di alimentazione:
lo store usa attualmente `synchronous=NORMAL`.

## 9. Accettazione e ambito

Eseguire `python -m unittest discover -s tests -v`. `test_memory_contract.py`
esegue l'esempio e controlla identità familiare, archi canonici, revisioni e
rifiuto delle viste parziali. `test_sleep_simulation.py` verifica la riorganizzazione
su dati isolati, compresa terminazione brusca prima del commit. Esperimento con
LLM reale: `python -m luca_memory.sleep_check --repeat 2`.
Vedere [verifica del sonno](29-verifica-riorganizzazione-sonno.md) per evidenze
e limiti. Non diventano responsabilità di Luca conversione PDF, biblioteche,
addestramento LLM, ottimizzazione della Bibbia o integrazione Cesare.
