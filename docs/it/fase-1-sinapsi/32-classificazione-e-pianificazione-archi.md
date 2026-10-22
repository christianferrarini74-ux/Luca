# Classificazione semantica e riduzione algoritmica degli archi

2026-10-22. [English](../../category-routing-planner.md).
Supera l'interfaccia automatica del [selettore di gruppi interi](30-arresto-riorganizzazione-obiettivo.md)
e del [confronto Gemma](31-confronto-sonno-gemma26.md), conservati come storia.

## Separazione dei compiti

L'LLM assegna una categoria tematica a tutti gli indirizzi esterni, separando
entranti e uscenti. Non decide dimensioni, riduzioni o quali archi spostare.
La richiesta contiene rubrica completa e contratto di classificazione, senza
i precedenti calcoli su grado/obiettivo. Lo schema richiede ogni indirizzo;
null esplicito indica incertezza. Il parser rifiuta omissioni, ID sconosciuti,
etichette malformate, vuote o troppo lunghe. Non classifica autoindirizzi del
focus né parti familiari interne.

`ClassifiedDirectory` è un risultato immutabile legato a focus/revisione.
Prima di pianificare, il Core riconvalida completezza, unicità, etichette e
revisione corrente. Una categoria può contenere uno o molti membri: **non è
un nodo di navigazione indivisibile**. La correttezza semantica rimane compito
del classificatore: completezza non significa etichette giuste.

È stato necessario aggiornare il solo paragrafo tecnico `group` di `bible.md`
e la traduzione inglese: prima imponeva al modello proprio il calcolo del grado
finale, in conflitto con questa interfaccia. Invariati istruzioni conversazionali,
integrazione della conoscenza e ragionamento. Nessun prompt di sistema aggiuntivo
o istruzione nascosta nel Python.

## Algoritmo deterministico

Grado esterno `D`, obiettivo `T=edge_target`, limite `U=edge_upper`, dimensione
massima `m=U-1`. L'automatismo resta riservato a `D>U`; riduzione necessaria
`R=D-T`. Un gruppo con `k` membri riduce gli archi diretti del padre di `k-1`
e ha grado proprio `k+1<=U`. Riduce il grado locale, **non** il totale degli
archi: ogni nuovo nodo di navigazione aggiunge un arco netto al grafo.

1. Riunisce le etichette solo nella stessa direzione e ordina gli ID dei membri.
2. Divide ogni categoria in blocchi disgiunti da al massimo `m` membri.
   I blocchi singoli non riducono nulla e restano diretti.
3. Ordina i blocchi per capacità decrescente (`numero_membri-1`), con spareggi stabili.
4. Usa i blocchi interi necessari; nell'ultimo prende soltanto
   `riduzione_rimanente+1` membri. Gli altri collegamenti restano diretti.
5. Si ferma alla riduzione esatta `R`, producendo normali `EdgeGroup` per
   applicazione atomica, verifica revisioni e ripristino protetto già esistenti.

Il Core non cambia categoria o direzione di nessun membro. Esempio: tredici
indirizzi Botanica e riduzione sette producono **un gruppo Botanica da otto**;
gli altri cinque restano diretti. Categoria tematica non significa appartenenza
a famiglia di contenuto: non si dividono o distillano i nodi sorgente.
Per i blocchi disgiunti, questa selezione minimizza i nuovi nodi di navigazione:
le capacità maggiori raggiungono la riduzione con meno blocchi e l'ultimo
blocco parziale elimina lo scarto. Costo `O(N+C log C)` dopo validazione e
ordinamento delle categorie, con `N` indirizzi e `C` blocchi; l'ordinamento
dei membri aggiunge nel caso peggiore `O(N log N)`. Nessuna nuova libreria.

Una categoria di `n` elementi offre al massimo `n-ceil(n/m)` riduzioni a un
solo livello. Se la capacità compatibile complessiva non basta per `R`, errore
esplicito senza scritture. Non vengono mescolate categorie o interpretati null
come autorizzazioni a indovinare. Due categorie da quattro non possono ancora
ridurre sette archi. Un hub enorme può richiedere in futuro un piano multilivello:
2.500 vicini della stessa categoria con `m=49` non arrivano a grado 45 in un
livello. Non vengono inventati lotti ricorsivi fuori dal formato di operazione attuale.

## Contratto Core e applicativo

```python
directory = memory.directory(root_id)
classification = classification_from_assignments(
    {"assignments": {"incoming": incoming_labels, "outgoing": outgoing_labels}},
    directory,
)
plan = maintenance.plan(root_id, classification)
operation_id = maintenance.apply(plan, confirmed=True)
```

Parser da `luca_memory.classification`. Le mappe usano ID decimali come stringhe
e titoli di categoria oppure null/None. Coprono tutti gli indirizzi per direzione,
escluso il focus stesso; un vicino bidirezionale compare nelle due mappe.
Solo runtime/store proprietario può scrivere. Il piano resta un'anteprima
revisionata: classificare non modifica nulla. Una classificazione obsoleta va rifatta.

L'anteprima del cruscotto usa automaticamente il nuovo risultato dell'adapter,
poi mostra il piano concreto da confermare. Endpoint applicazione/ripristino e
formato persistente di undo invariati. Adapter personalizzati e liste HTTP
`groups` esplicite possono ancora fornire **gruppi operativi interi**: questo
percorso compatibile conserva la selezione del sottoinsieme più vicino
all'obiettivo senza tagliare gruppi espliciti. Non confonderlo con categorie LLM.

## Verifiche

Quindici nuovi test: schema/parser completi, null, ID sconosciuti/duplicati,
record pubblici malformati, revisioni obsolete, separazione temi/direzioni,
blocchi grandi limitati, capacità insufficiente, obiettivo esatto, ripristino
del grafo e percorso anteprima/conferma/ripristino del cruscotto. Duecento casi
riproducibili confrontano riduzione esatta e numero di nodi con una programmazione
dinamica esaustiva indipendente sulle categorie. Restano attivi test sui gruppi
interi, annullamento del sonno, crash e persistenza.

Prove con worker reale sullo stesso grafo di 153 nodi e soglie 50/45,
mai sulla memoria personale. Due DB nuovi per modello:

| Modello | Durate worker | Classificazione | Piano applicato |
| --- | --- | --- | --- |
| Gemma 4 E2B Q4_K_M | 21,014 / 19,343 s | Tutti i 52 ID, quattro categorie omogenee da 13, nessun null | Un gruppo Botanica entrante da otto, **52→45**, entrambe |
| Gemma 4 26B A4B Q8_0 | 29,012 / 34,298 s | Tutti i 52 ID, quattro categorie omogenee da 13, nessun null | Stesso piano, **52→45**, entrambe |

Rapporti:
`D:/Test/Luca/sleep-check-20261022-160543-520995.json` e
`D:/Test/Luca/sleep-check-20261022-160749-341104.json`.
Ispezionate tutte le categorie grezze, non solo i gruppi applicati. In tutte
le quattro prove: contenuti, rotte orientate, rubriche familiari, controlli e
indici conservati; riapertura e ripristino esatto superati. Worker terminati con
join e DB temporanei rimossi. Scaricato solo il 26B appena caricato; E2B rimasto
caricato, memoria GPU tornata a 6.935/14/14 MiB e utilizzo zero.

Rispetto alla prova precedente cambiano intenzionalmente contratto, schema e
paragrafo tecnico della Bibbia. I risultati sostengono questa pipeline sul grafo
controllato, non un effetto causale della dimensione del modello né correttezza
semantica universale. Le prove E2B si sovrapponevano al caricamento del modello
grande: durate osservate, non benchmark isolato. Validazione semantica su titoli
ambigui resta distinta dalla correttezza numerica deterministica.

Checkpoint: 295 test Python, OK (sette verifiche opzionali hardware/servizi
saltate), 19 JavaScript superati, Ruff e `git diff --check` puliti.
SHA-256 della Bibbia attuale:
`87fa4075ab02797df4edbe65d3e49851fef9d91bae4cb98f83b1059e3f86c1ab`.
Config runtime, schema SQLite, dipendenze e database personali invariati.
Per l'app già avviata usare la normale sequenza Esci/avvio, caricando insieme
il nuovo Python e il paragrafo tecnico dell'interfaccia aggiornato.
