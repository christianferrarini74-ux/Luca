# Indexed memory search

`MemorySearch` is Luca's first search layer above `MemoryStore`. It keeps the
Core independent from SQLite details while exposing the retrieval paths needed
by the future runtime.

## Search paths

- `cell_by_id()` and `cell_by_alias()` provide exact lookup.
- `cells_by_text()` uses SQLite FTS5 over labels, forms, provenance, and cell
  payload text. It can restrict results by cell kind.
- `cells_by_kind()` returns an indexed kind without scanning every cell.
- `assertions()` filters explicit subject, predicate, and object references.
- `outgoing()`, `incoming()`, and `exact_edge()` expose both edge directions.
- `expand()` delegates bounded topological expansion to the CPU thought
  reference and returns its traceable result.

Cells are indexed when they are added and rebuilt when an existing database has
an incomplete search index. Edges remain semantic-free addresses; assertion
meaning is recovered from the referenced cells.

## Current boundary

This module is not yet an associative or embedding index. It provides fast
exact, lexical, and topological retrieval. A later associative layer may rank
distant candidates, but the explicit graph must still verify every candidate.
