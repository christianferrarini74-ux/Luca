"""Metadata-only entry cues: suggest addresses without choosing or opening knowledge."""

import re

from .node import normalise_key

_CONNECTORS = frozenset([
    "anche", "ancora", "avere", "avete", "avevo", "che", "chi", "cio",
    "come", "con", "cosa", "dal", "dalla", "dalle", "degli", "dei",
    "del", "della", "delle", "dello", "descrivi", "descrivimi", "dimmi", "dove",
    "essere", "erano", "fatto", "fanno", "fare", "gli", "hai", "hanno",
    "ho", "loro", "mai", "mia", "mie", "mio", "miei", "molto",
    "nel", "nella", "nelle", "nello", "noi", "non", "ora", "parlami",
    "parlare", "per", "perche", "puoi", "quale", "quali", "quanto", "quando",
    "questo", "questa", "questi", "queste", "sai", "sei", "sentito", "sia",
    "siamo", "sono", "stato", "stai", "stiamo", "sulla", "sulle", "sul",
    "suo", "sua", "suoi", "sue", "tutto", "tutti", "una", "uno",
    "voi", "the", "and", "are", "about", "can", "could", "did",
    "does", "for", "from", "have", "has", "how", "into", "its",
    "not", "our", "please", "some", "tell", "that", "their", "them",
    "there", "these", "they", "this", "those", "was", "were", "what",
    "when", "where", "which", "who", "why", "will", "with", "would",
    "you", "your",
])


def ensure_entry_index(store):
    db = store.connection
    db.execute("""CREATE VIRTUAL TABLE IF NOT EXISTS entry_search USING fts5(
        node_id UNINDEXED, title, terms, tokenize='unicode61 remove_diacritics 2')""")
    db.execute("""CREATE TRIGGER IF NOT EXISTS entry_index_delete AFTER DELETE ON cells BEGIN
        DELETE FROM entry_search WHERE rowid=OLD.id;
    END""")


def index_entry(store, node):
    db = store.connection
    db.execute("DELETE FROM entry_search WHERE rowid=?", (node.id,))
    db.execute("INSERT INTO entry_search(rowid,node_id,title,terms) VALUES(?,?,?,?)",
               (node.id, node.id, node.title, " ".join((node.slug, *node.keywords))))


def entry_candidates(store, text, limit):
    """OR-match metadata, not entire documents or an LLM-specific subject vocabulary."""
    tokens = tuple(dict.fromkeys(token for token in re.findall(r"\w+", normalise_key(text))
                                if len(token) >= 3 and token not in _CONNECTORS))
    if not tokens or limit < 1:
        return ()
    # The user-message budget bounds input size; quote each token as FTS data.
    match = " OR ".join('"' + token.replace('"', '""') + '"' for token in tokens)
    rows = store.connection.execute("""SELECT node_id,title,bm25(entry_search,0,8,2) AS cue_score
        FROM entry_search WHERE entry_search MATCH ? ORDER BY cue_score,node_id LIMIT ?""", (match, limit))
    from .synaptic import DirectoryEntry
    return tuple(DirectoryEntry(int(row[0]), row[1]) for row in rows)
