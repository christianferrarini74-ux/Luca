# Ripristino con l'esito desiderato dichiarato per primo

> **Documento storico — non guida operativa attuale.** Specifiche, default, risultati e passi successivi qui descritti appartengono alla fase registrata. Per ambito, API e comportamento vigenti leggere il [contratto attuale](28-contratto-utilizzo-memoria.md). Le evidenze originali sono conservate.

2026-10-22. [English](../../goal-first-recovery.md).

## Modifica controllata

La nuova domanda è:

> Voglio che la centralina IRIS-17 torni a irrigare davvero: la valvola deve aprirsi e l'acqua deve uscire. Al momento non irriga: è comparso E42 e il segnale del sensore è tornato normale, ma l'irrigazione non riparte. Qual è la procedura completa per ripristinare il funzionamento, dalla situazione attuale fino all'effettiva apertura della valvola? Indica tutti i passaggi e le condizioni necessarie.

Il testo esatto è in `tests/fixtures/goal_framing_questions.json`. Non contiene
capitoli, ID, soglie, conteggi di campioni o nomi dei comandi. La griglia separata
viene usata dopo la generazione, mai come input al modello.

Due conversazioni nuove con Qwen3.8 27B Q4_K_M, Bibbia originale, seed IRIS-17
originale, budget di 70.000 token e uno slot VRAM/uno RAM, come nelle interviste.
Nessuna correzione successiva, lettura imposta o visibilità dei nodi modificata.
Gli input pubblici della navigazione vengono registrati per distinguere candidati
visibili, indirizzi locali legali e letture effettive.
Nessuna intervista, ammissione o spiegazione precedente viene passata al modello:
ogni prova parte con cronologia vuota.

```powershell
python -m luca_memory.autonomy_check --profile current --model qwen/qwen3.8-27b --questions tests/fixtures/goal_framing_questions.json --capture-inputs --vram-capacity 1 --ram-capacity 1 --repeat 2
```

Il programma diagnostico accetta ora file di domande, modello/slot sperimentali
e registrazione degli input: modifiche applicate solo alla copia della
configurazione in memoria, con default precedenti invariati. Memoria personale
e config dell'app non cambiano. La vecchia domanda e le sue evidenze restano:
questa prova non le sostituisce.

## Risultato osservato

Report: `D:/Test/Luca/autonomy-check-20261022-134703-161319.json`.
Entrambe le conversazioni nuove producono la procedura completa, leggendo
`5 → 2 → 3 → 4`: ripristino, modalità, sensore/soglie, allarme E42.
Prima apertura globale, successive tre aperture locali scelte dal modello.
Tutti i dieci input registrati hanno cronologia della conversazione vuota.

Entrambe le risposte includono quattro campioni validi consecutivi e CONFERMA,
permanenza in OSSERVA fino ad AVVIA, assenza di allarmi e tre letture consecutive
strettamente inferiori al 28% per aprire. Spiegano anche l'azzeramento del
conteggio con valori almeno pari al 28% e la chiusura al 41% o superiore.
È copertura del manuale fittizio, non una prova su hardware reale.

Durate totali: 183,286 e 218,459 secondi, cinque chiamate al modello ciascuna.
Storage CUDA reale dei contenuti sul dispositivo 1, quattro caricamenti per
prova e retrocessioni RAM/SSD con i limiti di uno slot. Al termine è stato
scaricato solo Qwen; Gemma è rimasto caricato. Memoria GPU tornata a
6.935/14/14 MiB, utilizzo zero.

Ordine iniziale precedente: `[4,2,5,6,1,3,7]`; nuovo: `[1,4,3,5,2,6,7]`.
Stesso insieme di candidati, ma ranking diverso. Soprattutto, sul nodo modalità
2 il contenuto e la rubrica effettivamente presentati coincidono con quelli
precedenti: entranti 1/5, uscenti 3/4, destinazioni locali legali `[1,3,4,5]`.
Il nodo sensore prima ignorato era già disponibile: ora Qwen percorre proprio
quel collegamento locale esistente.

Il risultato sostiene l'ipotesi di un'interpretazione troppo ristretta della
domanda e mostra che la visibilità attuale basta in queste due prove. Non
emerge qui la necessità di modificarla. Non dimostra la causa interna della
precedente interruzione né l'affidabilità generale con richieste ambigue.

Verifiche: 259 test Python (sette verifiche opzionali saltate), 19 test
JavaScript e Ruff superati. Navigazione di produzione, Bibbia e config invariati.

## Limiti interpretativi

Confronto con i turni iniziali di
`D:/Test/Luca/memory-interview-20261022-092111-026346.json`, che si fermavano
su ripristino/modalità senza leggere le soglie. Sono controlli storici con
configurazione corrispondente, non prove randomizzate/intercalate.

Cambiare le parole può cambiare naturalmente il ranking dell'indice: confrontare
ordine e insieme dei candidati oltre alle rubriche locali, senza affermare che
ogni input visibile sia identico. Verificare in particolare se viene percorso
l'indirizzo locale modalità → sensore già disponibile prima, senza introdurre
un suggerimento o un'apertura del nodo scelti dal programma.

Un risultato positivo sarebbe coerente con la spiegazione del modello sul
perimetro del compito, non prova della causa privata o della sua «sincerità».
Può dimostrare che la visibilità esistente basta per questo caso, non che sia
sempre sufficientemente evidente su grafi grandi o domande diverse.
