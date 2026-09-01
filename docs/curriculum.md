# Luca: curriculum iniziale

## Scopo

Luca non parte da una memoria completamente vuota. Riceve un seme linguistico e concettuale limitato, verificabile e separato dal motore di ragionamento.

Un'AI esterna potrà preparare materiale didattico, ma non entrerà nel ciclo di risposta di Luca. Il suo output sarà importabile solo se espresso in questo formato leggibile e sottoposto a revisione.

## Principi

- Ogni elemento insegnato è una cella con contenuto, tipo e provenienza espliciti.
- Un fatto è una cella di tipo `assertion`; contiene gli indirizzi di soggetto, predicato e oggetto.
- Gli archi restano indirizzi senza semantica: soggetto → asserto e asserto → componenti.
- Le domande di prova sono separate dalle lezioni.
- Ogni risposta deve riportare la traccia di celle che l'ha resa possibile.

## Formato

Il file JSON contiene un `version`, una `language` e una lista ordinata di celle. Gli `slug` sono indirizzi leggibili solo nel curriculum; al caricamento diventano ID numerici compatti.

```json
{"slug": "fuoco", "kind": "concept", "label": "fuoco"}
{"slug": "calore", "kind": "concept", "label": "calore"}
{"slug": "fuoco_produce_calore", "kind": "assertion", "subject": "fuoco", "predicate": "produce", "object": "calore"}
```

Il caricatore crea gli archi seguenti:

```text
fuoco → fuoco_produce_calore
fuoco_produce_calore → produce
fuoco_produce_calore → calore
```

In questo modo l'asserto è una cella su cui Luca può lavorare, mentre gli archi servono soltanto alla navigazione.

## Primo confine linguistico

`ItalianSeedInterface` è intenzionalmente una grammatica a regole piccola. Riconosce poche domande italiane di identità e mondo fisico e le trasforma in un obiettivo di recupero dal grafo. Non è un modello linguistico e non deve essere presentata come comprensione generale del linguaggio.

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

Il primo set include tre esperienze analoghe che convergono su `scalda`
(`fuoco`, `sole`, `forno`) e due esperienze contrastive (`raffredda`,
`bagna`). Questo permette già di misurare la navigazione topologica prima
di introdurre un indice associativo.

## Prossima espansione

Il prossimo curriculum deve aggiungere esperienze analoghe, controesempi, domande di verifica non identiche alle lezioni e provenienza per ogni asserto. Solo allora potremo valutare il recupero associativo lontano senza confonderlo con la semplice ripetizione.

## Istruzione persistente nel dimostratore

`python -m luca_memory.chat --database .\luca.sqlite` avvia una sessione
persistente. Per ora accetta un linguaggio di istruzione volutamente piccolo:

```text
Luca, ricorda che il sole produce luce.
Luca, ricorda che il ghiaccio raffredda bevanda.
```

Ogni istruzione crea o riusa le celle-concetto, crea un asserto con
provenienza `user`, aggiunge gli indirizzi, e registra un evento append-only.
La conoscenza è poi disponibile anche dopo il riavvio. La grammatica è un
confine esplicito del primo dimostratore, non una pretesa di linguaggio libero.
