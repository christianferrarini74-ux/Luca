# Luca: curriculum iniziale

> **Documento storico — non guida operativa attuale.** Specifiche, default, risultati e passi successivi qui descritti appartengono alla fase registrata. Per ambito, API e comportamento vigenti leggere il [contratto attuale](fase-1-sinapsi/28-contratto-utilizzo-memoria.md). Le evidenze originali sono conservate.

## Scopo

Luca non parte da una memoria completamente vuota. Riceve un seme linguistico e concettuale limitato, verificabile e separato dal motore di ragionamento.

Un'AI esterna può preparare materiale didattico, ma non entra nel ciclo di risposta di Luca. Il suo output è importabile solo se espresso in un formato leggibile e sottoposto a revisione.

## Principi

- Ogni elemento insegnato è una cella con contenuto, tipo e provenienza espliciti.
- Un fatto è una cella di tipo `assertion`, con indirizzi di soggetto, predicato e oggetto.
- Gli archi restano indirizzi senza semantica: soggetto → asserto e asserto → componenti.
- Le domande di prova sono separate dalle lezioni.
- Ogni risposta riporta la traccia delle celle che l'hanno resa possibile.

## Formato

Il file JSON contiene `version`, `language` e una lista ordinata di celle. Gli slug sono indirizzi leggibili solo nel curriculum; al caricamento diventano ID numerici compatti.

```json
{"slug": "fuoco", "kind": "concept", "label": "fuoco"}
{"slug": "calore", "kind": "concept", "label": "calore"}
{"slug": "fuoco_produce_calore", "kind": "assertion", "subject": "fuoco", "predicate": "produce", "object": "calore"}
```

Il caricatore crea gli archi:

```text
fuoco → fuoco_produce_calore
fuoco_produce_calore → produce
fuoco_produce_calore → calore
```

L'asserto è così una cella su cui Luca può lavorare, mentre gli archi servono soltanto alla navigazione.

## Primo confine linguistico

`ItalianSeedInterface` è intenzionalmente una piccola grammatica a regole. Riconosce poche domande italiane di identità e mondo fisico e le trasforma in obiettivi di recupero dal grafo. Non è un modello linguistico e non va presentata come comprensione generale del linguaggio.

Per eseguire il seme iniziale:

```powershell
python -m luca_memory.demo "Come ti chiami?"
python -m luca_memory.demo "Chi è il tuo creatore?"
python -m luca_memory.demo "Cosa produce il fuoco?"
```

Le verifiche, conservate separatamente dalle lezioni, si eseguono così:

```powershell
python -m luca_memory.evaluate
```

Il primo set include tre esperienze analoghe che convergono su `scalda` (`fuoco`, `sole`, `forno`) e due esperienze contrastive (`raffredda`, `bagna`). Questo permette di misurare la navigazione topologica prima di introdurre un indice associativo.

## Prossima espansione

Il prossimo curriculum deve aggiungere esperienze analoghe, controesempi, domande di verifica diverse dalle lezioni e provenienza per ogni asserto. Solo allora si potrà valutare il recupero associativo lontano senza confonderlo con la semplice ripetizione.

## Istruzione persistente nel dimostratore

`python -m luca_memory.chat --database .\luca.sqlite` avvia una sessione persistente. Per ora accetta un linguaggio di istruzione volutamente piccolo:

```text
Luca, ricorda che il sole produce luce.
Luca, ricorda che il ghiaccio raffredda bevanda.
```

Ogni istruzione crea o riusa celle-concetto, crea un asserto con provenienza `user`, aggiunge gli indirizzi e registra un evento append-only. La conoscenza è disponibile anche dopo il riavvio. La grammatica è un confine esplicito del primo dimostratore, non una pretesa di linguaggio libero.
