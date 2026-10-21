# Fase 1.11 — Verifica reale con LM Studio

Data: 2026-10-21

[English](../../phase-1-11-live-validation.md)

## Esito: 7/8, non accettazione completa

Ultima prova sintetica: `google/gemma-4-e2b` (Q4_K_M), CUDA reale sul dispositivo 1,
un solo slot residente e due slot RAM. Nessun database personale aperto.

| Controllo | Esito finale |
| --- | --- |
| Ricerca globale, scelta dell'ingresso e arresto per rispondere | Superato |
| Lettura di una parte mantenendo l'identità del padre | Superato |
| Uscita esterna attraverso la rubrica condivisa del padre | Superato |
| Richiamo spontaneo da domanda naturale | **Fallito** |
| Modifica della parte residente e risposta con il nuovo codice | Superato |
| Conoscenza generale senza esposizione forzata della memoria | Superato |
| Raggruppamento LLM e ripristino delle rotte Core | Superato strutturalmente |
| Percorso automatico in inattività con LLM reale e ripristino | Superato strutturalmente |

La traccia del fallimento mostra il modello scegliere `answer` senza aprire la
parte sulla chiusura e inventare `VENTO-113`. Il codice reale era disponibile in
quella parte. Il Core esegue l'azione scelta; `use_memory: true` non certifica la verità.

La verifica di freschezza porta esplicitamente il focus sulla parte 3 **prima**
di modificarla, per separare la coerenza della cache dal precedente errore di
navigazione. L'LLM usa poi `VELA-903`, non il vecchio `RAME-731`, anche con una
conversazione contraddittoria. Non è conteggiata come scelta autonoma dell'ingresso.

Il raggruppamento porta 51 archi esterni a 26, sotto l'obiettivo 45; il ripristino
recupera tutte le 51 rotte orientate. L'inattività è accelerata per quel controllo,
non un'attesa interattiva di 60 secondi. Superare il controllo strutturale **non
valida la semantica**: alcuni gruppi chiamati “Astronomia” contengono nodi della
fixture intitolati “Geologia”. I nomi possono sviare la navigazione anche se gli
indirizzi rimangono integri.

## Correzioni e limiti

- Questo server rifiuta `json_object`: le chiamate strutturate ora usano `json_schema`.
- Schemi degli ID/azioni ammessi e conferma dell'avvenuta apertura evitano la
  riapertura ripetuta senza effetto. Tornare su un nodo diverso già visitato resta
  possibile; `navigation_steps` continua a limitare il lavoro complessivo.
- Il vecchio limite di 160 token poteva esaurirsi nel ragionamento prima del JSON.
  Nuovi `runtime.synaptic.navigation_output_tokens` e `maintenance_output_tokens`,
  entrambi 2048. Le riserve riducono anche il budget d'ingresso senza tagliare la
  rubrica. Esaurimento e risposte vuote sono errori espliciti; il ragionamento non
  viene eseguito come azione.
- Nodo e rubrica sono JSON strutturato, non una stringa JSON annidata con escape.

Una configurazione intermedia ha ottenuto 8/8, ma il richiamo spontaneo è fallito
nelle ripetizioni. Il risultato finale riporta il limite residuo, non il miglior
tentativo. Più budget risolve il troncamento, non l'affidabilità semantica. Nessuna
pretesa di confronto fra modelli o validazione su biblioteca reale.

## Riproduzione

Con LM Studio avviato:

```powershell
python -X utf8 -m luca_memory.live_memory_check
```

Il comando carica `seed/phase11_validation.json` in un database temporaneo nella
cartella dati configurata, **non** nel database personale. Salva un report JSON
con timestamp, libera le proprie allocazioni CUDA e lascia caricato il modello
esistente in LM Studio. `--host-memory` seleziona gli slot host di riferimento.
Il codice di uscita 1 indica un controllo fallito, incluso il richiamo spontaneo
attualmente non risolto.

Report finale: `D:/Test/Luca/phase11-live-20261021-140838.json`.
Conservati nella stessa cartella anche i tentativi intermedi e falliti. Registrati
scelte, risposte, direzioni dei gruppi, tassonomia delle fonti e rilascio risorse.

Dopo le correzioni: **151 test automatici superati**, comprese quattro prove CUDA
reali: `LUCA_TEST_CUDA=1 python -m unittest discover -s tests`. Superati compilazione
Python e `git diff --check`. Nessuna nuova dipendenza. Non dichiarata verifica visiva browser.

Prossima accettazione: affidabilità del richiamo deciso dal modello e qualità dei
nomi dei gruppi. PDF, distillazione e integrazione Cesare restano fuori ambito.
