"""Additive schema for canonical families and revision-aware navigation."""


def ensure_synaptic_schema(store):
    db = store.connection
    db.executescript("""
        CREATE TABLE IF NOT EXISTS graph_revision (
            singleton INTEGER PRIMARY KEY CHECK(singleton = 1), revision INTEGER NOT NULL
        );
        INSERT OR IGNORE INTO graph_revision VALUES (1, 0);
        CREATE TABLE IF NOT EXISTS node_id_sequence (
            singleton INTEGER PRIMARY KEY CHECK(singleton = 1), last_id INTEGER NOT NULL
        );
        INSERT OR IGNORE INTO node_id_sequence SELECT 1, COALESCE(MAX(id),0) FROM cells;
        UPDATE node_id_sequence SET last_id = MAX(last_id, (SELECT COALESCE(MAX(id),0) FROM cells));
        CREATE TRIGGER IF NOT EXISTS synaptic_id_allocation AFTER INSERT ON cells BEGIN
            UPDATE node_id_sequence SET last_id = MAX(last_id, NEW.id);
        END;
        CREATE TABLE IF NOT EXISTS node_versions (
            node_id INTEGER PRIMARY KEY REFERENCES cells(id) ON DELETE CASCADE,
            content_revision INTEGER NOT NULL DEFAULT 0,
            directory_revision INTEGER NOT NULL DEFAULT 0
        );
        INSERT OR IGNORE INTO node_versions(node_id) SELECT id FROM cells;
        CREATE TABLE IF NOT EXISTS node_catalog (
            node_id INTEGER PRIMARY KEY REFERENCES cells(id) ON DELETE CASCADE,
            title TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS managed_aliases (
            node_id INTEGER NOT NULL REFERENCES cells(id) ON DELETE CASCADE, alias TEXT NOT NULL,
            PRIMARY KEY(node_id, alias)
        );
        CREATE TABLE IF NOT EXISTS family_parts (
            part_id INTEGER PRIMARY KEY REFERENCES cells(id),
            root_id INTEGER NOT NULL REFERENCES cells(id), CHECK(part_id != root_id)
        );
        CREATE INDEX IF NOT EXISTS family_by_root ON family_parts(root_id, part_id);
        CREATE TABLE IF NOT EXISTS maintenance_operations (
            id INTEGER PRIMARY KEY, payload TEXT NOT NULL, active INTEGER NOT NULL
        );
        CREATE TRIGGER IF NOT EXISTS synaptic_cell_insert AFTER INSERT ON cells BEGIN
            UPDATE node_id_sequence SET last_id = MAX(last_id, NEW.id);
            UPDATE graph_revision SET revision = revision + 1;
            INSERT INTO node_versions VALUES(NEW.id,
                (SELECT revision FROM graph_revision), (SELECT revision FROM graph_revision));
        END;
        CREATE TRIGGER IF NOT EXISTS synaptic_cell_delete AFTER DELETE ON cells BEGIN
            UPDATE graph_revision SET revision = revision + 1;
        END;
        CREATE TRIGGER IF NOT EXISTS synaptic_cell_update AFTER UPDATE OF content ON cells
        WHEN OLD.content != NEW.content BEGIN
            UPDATE graph_revision SET revision = revision + 1;
            UPDATE node_versions SET content_revision = (SELECT revision FROM graph_revision),
                directory_revision = (SELECT revision FROM graph_revision) WHERE node_id = NEW.id;
            UPDATE node_versions SET directory_revision = (SELECT revision FROM graph_revision)
            WHERE node_id IN (SELECT source_id FROM edges WHERE target_id = NEW.id)
               OR node_id IN (SELECT target_id FROM edges WHERE source_id = NEW.id);
        END;
        CREATE TRIGGER IF NOT EXISTS synaptic_family_guard BEFORE INSERT ON family_parts BEGIN
            SELECT CASE WHEN EXISTS(SELECT 1 FROM family_parts WHERE part_id = NEW.root_id
                OR root_id = NEW.part_id) THEN RAISE(ABORT, 'Nested families are not allowed') END;
        END;
        CREATE TRIGGER IF NOT EXISTS synaptic_part_edge_guard BEFORE INSERT ON edges BEGIN
            SELECT CASE WHEN EXISTS(SELECT 1 FROM family_parts
                WHERE (part_id = NEW.source_id AND root_id != NEW.target_id)
                   OR (part_id = NEW.target_id AND root_id != NEW.source_id))
                THEN RAISE(ABORT, 'External edges must use the family root') END;
        END;
    """)
    for table, prefix, ids in (
        ("edges", "edge", "{row}.source_id, {row}.target_id"),
        ("family_parts", "family", "{row}.part_id, {row}.root_id"),
    ):
        for event, row in (("INSERT", "NEW"), ("DELETE", "OLD")):
            db.executescript(f"""
                CREATE TRIGGER IF NOT EXISTS synaptic_{prefix}_{event.lower()}
                AFTER {event} ON {table} BEGIN
                    UPDATE graph_revision SET revision = revision + 1;
                    UPDATE node_versions SET directory_revision = (SELECT revision FROM graph_revision)
                    WHERE node_id IN ({ids.format(row=row)});
                END;
            """)
    # Populate only missing metadata, once per legacy node; no durable content is rewritten.
    from .node import KnowledgeNode, normalise_key
    from .store import Cell
    rows = db.execute("""SELECT c.* FROM cells c LEFT JOIN node_catalog n ON n.node_id=c.id
                         WHERE n.node_id IS NULL""")
    for row in rows:
        node = KnowledgeNode.from_cell(Cell(row["id"], row["content"], row["created_at"]))
        db.execute("INSERT INTO node_catalog VALUES (?, ?)", (node.id, node.title))
        if node.slug and node.title:
            for alias in {normalise_key(value) for value in (node.slug, node.title, *node.keywords)} - {""}:
                db.execute("""INSERT OR IGNORE INTO managed_aliases SELECT ?, ?
                    WHERE EXISTS(SELECT 1 FROM cell_aliases WHERE cell_id=? AND alias=?)""",
                           (node.id, alias, node.id, alias))
    db.commit()
