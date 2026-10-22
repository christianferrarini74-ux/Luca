# Fase 1.08 — Roadmap per l'utilizzo della memoria, punti 1–5

> **Documento storico — non guida operativa attuale.** Specifiche, default, risultati e passi successivi qui descritti appartengono alla fase registrata. Per ambito, API e comportamento vigenti leggere il [contratto attuale](28-contratto-utilizzo-memoria.md). Le evidenze originali sono conservate.

Data: 2026-10-19. Ambito: solo Luca; integrazione con Cesare rinviata.

Milestone successivo: [memoria fisica](09-memoria-fisica.md), che supera le cache
soltanto logiche e protegge la conoscenza esistente durante avvio/reset.
Le note seguenti registrano i precedenti punti 1–5.

[English](../../memory-development-roadmap.md)

1. Rendere eseguibile il dialogo dei sommergibili: riferimento ai mezzi gialli,
   cambio laterale di animale, enumerazione della famiglia, accenti, parafrasi,
   esclusioni e argomenti sconosciuti.
2. Introdurre un pianificatore con baseline deterministica e proposte LLM
   facoltative e limitate. Il Core verifica ID e percorsi; condividere vicini
   nel grafo non dimostra pertinenza semantica. Gli archi restano indirizzi puri.
3. Distinguere precaricamento, apertura, attraversamento ed esposizione nella
   risposta. L'attività recente ha durata limitata; aprire un hub non rinforza
   tutti i nodi aperti in passato. Conservare conoscenza SSD e invarianti dei livelli.
4. Limitare contesto e cache anche per dimensione. Conservare l'identità del
   documento e permettere l'accesso alle sezioni. Separare metadati d'uso dal
   contenuto evitando reindicizzazioni al richiamo. Limitare l'intera richiesta
   al modello: cronologia, domanda, istruzioni e riserva per la risposta.
5. Conservare obiettivo, vincoli, decisioni e focus riprendibile separatamente
   dai cluster. Le modifiche del compito sono esplicite, limitate e visibili nell'API.

Accettazione: test deterministici e planner simulato, rifiuto di piani invalidi,
oblio e cache piccole, contenuti grandi, ripresa fra cluster scollegati,
contratti HTTP e prova reale con modello locale. Documentare i limiti e separare
prompt sperimentali e conversazione libera. Acquisizione e Cesare sono esclusi.

## Punti 1–3 implementati

Il dialogo di riferimento conserva gli attributi dell'oggetto, cambia membro
lateralmente e apre la famiglia per enumerarla. Il planner ibrido accetta
proposte del modello soltanto fra candidati verificati sul grafo e si astiene
quando restano alternative indistinguibili. Le negazioni sono delimitate per
proposizione; `Perché` e `Perche` sono normalizzati coerentemente. È una baseline,
non una comprensione semantica senza limiti.

L'attività distingue precaricamento, apertura, attraversamento, associazione,
esposizione e retrocessione. La priorità recente scade entro una finestra
limitata. Rinforzano gli archi solo attraversamenti effettivi o collegamenti che
giustificano il richiamo scelto. Esposizione significa contenuto fornito per una
risposta riuscita, non prova di utilizzo corretto da parte del modello.
La tabella SQLite `node_usage` conserva l'utilizzo separato dal testo indicizzato.

## Punto 4 implementato

`runtime.context_budget` configura l'intera richiesta e i sotto-budget di memoria
e cronologia. L'accounting usa byte UTF-8 in modo conservativo: non è il tokenizer
del provider né una garanzia per template arbitrari. La finestra va impostata
entro quella reale del modello sul server. Le domande troppo grandi sono
rifiutate, non tagliate silenziosamente.
VRAM e RAM limitano anche il payload serializzato conservato (`vram_bytes`,
`ram_bytes`), non RSS del processo o allocazione fisica GPU. I nodi troppo grandi
hanno viste parziali in cache che non possono sovrascrivere la conoscenza SSD.
Caricare una sorgente completa per estrarne una sezione può ancora allocarla
temporaneamente.

I nodi supportano `summary` e `sections` con `key`, `title`, `content`.
Il backend verifica `/api/section` mantenendo l'ID del documento come focus ed
esponendo la sezione scelta. Gli estratti sono marcati come parziali. La GUI
mostra budget e controlli per le sezioni, senza eseguire logica di memoria.
Contenuto sorgente e indice non cambiano quando si aggiorna soltanto l'utilizzo.

## Punto 5 implementato

Lo stato del compito è esplicito e limitato: obiettivo, fino a otto vincoli e
decisioni, punto di ripresa con eventuale sezione, sospensione e ultimi otto
focus. SQLite lo conserva separatamente dal grafo. Un cluster scollegato può
sospendere il compito senza cancellarne l'obiettivo o sostituire il punto di
ripresa. “Riprendi il compito” ripristina quel focus e la sezione scelta.
Nuova Sessione azzera intenzionalmente il compito; un cambio di argomento no.

Usare il modulo nella GUI, `POST /api/task`, oppure i messaggi `Obiettivo: ...`,
`Vincolo: ...`, `Decisione: ...`, `Nuovo compito: ...`. Gli aggiornamenti oltre
`task_limit` sono rifiutati atomicamente, senza eliminare vincoli in silenzio.
Il compito ha spazio riservato nelle richieste al modello, prima di memoria e
cronologia sacrificabili. Non vengono salvate automaticamente decisioni inventate
dal modello. La cronologia conversazionale conserva al massimo sedici messaggi.

`runtime.memory_planner` accetta `rules` e `hybrid`. La baseline ibrida utilizza
anteprime limitate e può chiedere all'LLM di scegliere un vicino ambiguo; il Core
rifiuta ID sconosciuti e salti non verificati sul grafo. Non è ancora un planner
universale del linguaggio naturale o un correttore di ogni possibile refuso.
`recent_window` conta passi di attività e passaggi di turno, non secondi reali.

`runtime.memory_policy: experimental` mantiene il dominio controfattuale del seed
nelle prove correnti. Per conoscenze ordinarie usare `grounded`: i dettagli locali
restano utili mentre il modello può impiegare la conoscenza generale. Le politiche
separano il controllo dell'esperimento dalla conversazione e non modificano pesi.

La GUI resta un frontend. Piani, budget, sezioni, attività e compito sono gestiti
da Python. Il punto 6 e ogni integrazione con Cesare rimangono rinviati.

## Verifica del 2026-10-19

Superati 77 test automatici: suite originaria, dialogo di riferimento, rifiuto di
piani invalidi, esclusioni, varianti con accenti e refusi, scadenza dell'attività,
conservazione dei contatori precedenti, richiamo senza reindicizzazione, documenti
grandi e cache limitate, sezioni, riavvio/ripresa del compito, aggiornamenti atomici
e contratti HTTP con errori e arresto. Verificati sintassi JavaScript e rendering
dei dati della dashboard, compreso escaping di titoli/chiavi delle sezioni,
stato del compito e budget. Non è stata eseguita un'ispezione visiva completa nel browser.

Le prove reali con LM Studio hanno usato database temporanei in `D:/Test/Luca`,
rimossi dopo l'arresto ordinato, senza aprire il database personale. Il dialogo
di riferimento ha raggiunto i focus `7, 7, 19, 14`: risposte con mezzi gialli di
cartone, mezzi rossi di biscotto e periscopio a osso, quindi le altre specie della
flotta. Le richieste finali hanno usato 1255–2476 unità conservative su 7424
disponibili. Una prova separata ha verificato matematica generale fuori memoria
e ripresa del compito dopo un argomento scollegato. Sono verifiche funzionali,
non una dimostrazione generale dell'affidabilità delle risposte dell'LLM.

I prompt restano personalizzabili nel progetto (`bible.md` e
`prompts/memory-experiment.it.md`), con fallback inclusi nel pacchetto.
Le etichette tecniche del focus restano nella diagnostica del Core e sono rimosse
dal testo rivolto al modello. Una risposta interamente filtrata non restituisce
più come fallback il testo tecnico originale.

Limiti noti: il planner usa euristiche italiane limitate con scelta LLM facoltativa
nelle ambiguità; non è un ragionatore semantico universale. I compiti si aggiornano
con comandi espliciti o API: non si consolidano decisioni inferite dal modello.
Il loader del seed resta un ripristino sperimentale, non una migrazione di
biblioteca. La lettura di sorgenti grandi può ancora allocare memoria transitoria.
Non sono stati introdotti cache GPU fisiche, acquisizione documentale o adapter Cesare.
