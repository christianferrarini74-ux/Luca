# Contesto misurato in token del modello

[English](../../token-context.md)

2026-10-21. Questa modifica sostituisce i precedenti budget del prompt in byte
UTF-8, non la misura della memoria fisica. I resoconti storici restano invariati.

## Configurazione

I valori dentro `runtime.context_budget`, esclusa `unit`, nel file del progetto
sono ora espressi in **token del modello**:

```yaml
context_budget:
  unit: tokens
  context_window: 70000
  output_reserve: 4096
  framing_reserve: 512
  memory_limit: 20000
  per_node_limit: 16000
  history_limit: 40000
  task_limit: 2048
```

La finestra da 70.000 token comprende risposta e margine di sicurezza: l'input
completo può occupare al massimo **65.392 token**. I limiti sono massimali, non
spazi da riempire. Istruzioni obbligatorie, domanda corrente, compito esplicito e
rubrica completa hanno precedenza; conoscenza pertinente e scambi più recenti
usano lo spazio restante. La cronologia può quindi ricevere meno di 40.000 token
se gli altri contenuti necessari richiedono spazio.

Il timeout dell'orchestratore nel file di configurazione è portato a 180 secondi
per lasciare tempo a prefill e generazione più lunghi; non garantisce una
determinata latenza a finestra piena.

Rimossi il taglio fisso a quattro coppie nel prompt e quello a otto nella
sessione. La cronologia è limitata dal budget in token, conservando coppie
utente/assistente complete. Se la coppia più recente supera da sola il budget,
resta disponibile per produrre un estratto esplicitamente segnalato nel prompt;
le coppie precedenti escono quando il budget di conservazione viene superato.
Non è una sintesi automatica della conversazione né una persistenza durevole
della chat. Nella navigazione LLM cambiare argomento non azzera la conversazione.

## Conteggio nativo senza nuovi pacchetti

Il modello caricato in LM Studio espone `countTokens` e `applyPromptTemplate`
attraverso l'interfaccia RPC usata dal suo
[SDK Python ufficiale](https://github.com/lmstudio-ai/lmstudio-python/blob/main/src/lmstudio/sync_api.py).
Luca implementa soltanto queste due operazioni richiesta/risposta e un trasporto
WebSocket limitato, usando la libreria standard Python. Ogni operazione chiude
la connessione; non servono processi, thread di tokenizzazione o copie del
modello. La cache trattiene al massimo 256 hash e conteggi, non copie dei testi.
Un cambiamento del protocollo RPC costituisce un rischio di compatibilità e
produce un errore, mai un ripiego silenzioso su byte o caratteri per token.
La modalità token richiede attualmente questa interfaccia LM Studio, non basta
un endpoint genericamente compatibile con OpenAI.

Il conteggio preventivo usa il template della chat del modello, compresi ruoli
e separatori. La risposta conserva separatamente anche `usage.prompt_tokens` e
i token generati riportati dal server. Template e inferenza possono differire
leggermente: nella prova breve erano 28 token preventivi contro 27 del server.
`template_token_delta` registra lo scarto; resta il margine di 512 token. Sono
conteggi nativi, non una garanzia di identico trattamento dei token speciali tra
RPC del template e inferenza.

All'avvio vengono verificati sia il massimo supportato dal modello sia il
contesto con cui è caricato. Se non è caricato, Luca richiede
`context_length: 70000` e controlla l'esito. Se è già caricato con una finestra
inferiore, segnala come intervenire senza scaricare automaticamente un modello
che potrebbe essere usato da altri programmi. Il modello osservato
(`google/gemma-4-e2b`) era caricato con 131.072 token.

Resta disponibile `unit: utf8_bytes` per configurazioni storiche/di riferimento
e test a regole senza servizi esterni. Se manca il servizio di conteggio mentre
è selezionata la modalità token, viene segnalato un errore: non si attiva da sola
la modalità storica.

## La memoria fisica resta fisica

`vram_bytes`, `ram_bytes`, `fast_index_bytes`, payload serializzati, statistiche
dei trasferimenti CUDA e posizioni dei testi diagnostici rimangono in **byte**.
I budget del prompt per contenuto dei nodi, compito, navigazione e risposta
usano lo stesso contatore associato al modello. Le posizioni sono marcate
`span_unit: utf8_bytes`; `memory_bytes` evita di confrontarle con token quando
si registra la conoscenza esposta. Il cruscotto indica le unità e mostra sia il
conteggio preventivo sia il consumo del prompt confermato dal server.

## Verifiche

Suite completa, comprese verifiche del tokenizer nativo e CUDA reale:

```powershell
$env:LUCA_TEST_LMSTUDIO = '1'
$env:LUCA_TEST_CUDA = '1'
python -m unittest discover -s tests
```

182 test superati con entrambi i servizi disponibili. Coperti conservazione
delle coppie, sforamento, Unicode, integrità delle istruzioni obbligatorie,
budget del compito, caricamento del modello, cache limitata, letture e messaggi
WebSocket frammentati, ping, mascheratura dei messaggi client, frame grandi,
rifiuto di handshake non validi e chiusura delle connessioni.

Il tokenizer reale ha assemblato un input da 63.760 token con 44 messaggi
storici, 20.000 token di memoria e 38.807 token di contenuto della cronologia.
Comprese risposta e sicurezza: **68.368 / 70.000 token**. Domanda corrente
conservata integralmente. Questa prova verifica costruzione e conteggio di un
prompt ampio, **non** qualità della generazione o inferenza a finestra piena.

Un'inferenza breve separata ha risposto `Ciao`. Una sessione isolata SQLite/CUDA
ha richiamato correttamente il nodo 18 (topi intagliatori di formaggio), con 405
token preventivi contro 404 confermati dal server, rilasciando le risorse.
La memoria personale non è stata modificata. Queste verifiche non risolvono
automaticamente i problemi di fedeltà del dialogo descritti nel
[resoconto precedente](14-ingresso-memoria-e-dialogo.md).

La prova sintetica più ampia di navigazione/manutenzione ha restituito **7/8**:
`D:/Test/Luca/phase11-live-20261021-183304.json`. Superati navigazione della
famiglia, richiamo, aggiornamento residente, conoscenza generale,
raggruppamento/ripristino manuale e raggruppamento in inattività. Nel caso di
percorso esterno il modello ha oscillato tra i nodi 4 e 1, esaurito gli otto
passi e inventato un codice di accesso. Rimane un difetto aperto di navigazione
e aderenza della risposta ai dati: un contesto maggiore da solo non lo risolve.

Chiudere l'istanza attuale con **Esci** e riavviare con `python run_luca.py` per
caricare configurazione e codice nuovi. I processi esistenti non vengono
riavviati automaticamente; il modello in LM Studio non richiede modifiche se
ha già un contesto sufficiente.
