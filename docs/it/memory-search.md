# Ricerca indicizzata della memoria

`MemorySearch` è il primo livello di ricerca sopra `MemoryStore`. Mantiene il
Core indipendente dai dettagli SQLite ed espone i percorsi che serviranno al
runtime futuro.

## Percorsi di ricerca

- `cell_by_id()` e `cell_by_alias()` fanno lookup esatto.
- `cells_by_text()` usa SQLite FTS5 su etichette, forme, provenienza e payload
  testuale delle celle. Può limitare i risultati al tipo di cella.
- `cells_by_kind()` restituisce un tipo indicizzato senza scansionare tutte le celle.
- `assertions()` filtra i riferimenti espliciti a soggetto, predicato e oggetto.
- `outgoing()`, `incoming()` e `exact_edge()` espongono entrambi i versi degli archi.
- `expand()` delega l'espansione topologica delimitata alla baseline CPU del
  pensiero e restituisce un risultato tracciabile.

Le celle vengono indicizzate quando sono aggiunte e l'indice viene ricostruito
se un database esistente è incompleto. Gli archi restano indirizzi senza
semantica; il significato delle assertion viene ricavato dalle celle referenziate.

## Confine attuale

Questo modulo non è ancora un indice associativo o a embedding. Fornisce
recupero esatto, lessicale e topologico. Un futuro livello associativo potrà
classificare candidati lontani, ma il grafo esplicito dovrà comunque verificare
ogni candidato.
