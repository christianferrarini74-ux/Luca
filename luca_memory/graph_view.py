"""Bounded, read-only graph metadata for the cockpit; never load node bodies."""


def graph_settings(frontend):
    """Validate display limits independently of memory/navigation budgets."""
    settings = frontend.get("graph", {})
    if not isinstance(settings, dict):
        raise ValueError("frontend.graph must be a mapping.")
    result = {}
    for key, default, maximum in (("node_limit", 500, 2000), ("edge_limit", 2000, 10000)):
        value = settings.get(key, default)
        if type(value) is not int or not 1 <= value <= maximum:
            raise ValueError(f"frontend.graph.{key} must be an integer from 1 to {maximum}.")
        result[key] = value
    return result


def graph_snapshot(session, settings, *, mode="global", node_id=None):
    """Read one consistent metadata snapshot under the store's shared lock."""
    if mode not in {"global", "focus"}:
        raise ValueError("Graph mode must be global or focus.")
    if node_id is not None and (type(node_id) is not int or node_id <= 0):
        raise ValueError("Graph node_id must be a positive integer.")
    store, carousel = session.store, session.carousel
    with store.lock:
        db = store.connection
        center = node_id if node_id is not None else carousel.focus_id
        if center is not None:
            row = db.execute("SELECT COALESCE(f.root_id,n.node_id) FROM node_catalog n "
                             "LEFT JOIN family_parts f ON f.part_id=n.node_id WHERE n.node_id=?", (center,)).fetchone()
            if row is None:
                raise KeyError("Unknown graph node ID.")
            center = int(row[0])
        # Canonical roots and all their parts are eligible in the local view.
        scope = """WITH roots(id) AS (
            SELECT ? UNION SELECT target_id FROM edges WHERE source_id=?
            UNION SELECT source_id FROM edges WHERE target_id=?)
        """ if mode == "focus" else ""
        where = " WHERE COALESCE(f.root_id,n.node_id) IN (SELECT id FROM roots)" if mode == "focus" else ""
        params = (center, center, center) if mode == "focus" else ()
        base = " FROM node_catalog n LEFT JOIN family_parts f ON f.part_id=n.node_id"
        total = db.execute("SELECT COUNT(*) FROM node_catalog").fetchone()[0]
        scoped = db.execute(scope + "SELECT COUNT(*)" + base + where, params).fetchone()[0]
        rows = db.execute(scope + "SELECT n.node_id,n.title,COALESCE(f.root_id,n.node_id)" + base + where +
                          " ORDER BY CASE WHEN n.node_id=? THEN 0 ELSE 1 END,n.node_id LIMIT ?",
                          (*params, center, settings["node_limit"])).fetchall()
        vram, ram = set(carousel.vram.node_ids()), set(carousel.ram.node_ids())
        roots = sorted({int(row[2]) for row in rows})
        counts = {}
        if roots:
            root_marks = ",".join("?" for _ in roots)
            counts = dict(db.execute(f"SELECT root_id,COUNT(*) FROM family_parts "
                                     f"WHERE root_id IN ({root_marks}) GROUP BY root_id", roots))
        nodes = [{"id": int(row[0]), "title": row[1], "root_id": int(row[2]),
                  "part_count": counts.get(row[0], 0),
                  "tier": "vram" if row[0] in vram else "ram" if row[0] in ram else "ssd"}
                 for row in rows]
        ids = [n["id"] for n in nodes]
        edges, visible_edges = [], 0
        if ids:
            marks = ",".join("?" for _ in ids)
            clause = f" FROM edges WHERE source_id IN ({marks}) AND target_id IN ({marks})"
            visible_edges = db.execute("SELECT COUNT(*)" + clause, (*ids, *ids)).fetchone()[0]
            edges = [{"source": int(row[0]), "target": int(row[1])} for row in db.execute(
                "SELECT source_id,target_id" + clause + " ORDER BY source_id,target_id LIMIT ?",
                (*ids, *ids, settings["edge_limit"]))]
        return {"revision": store.revision, "mode": mode, "center_id": center,
                "focus_id": carousel.focus_id, "reading_id": carousel.reading_id,
                "backend": carousel.physical_state().get("backend", "host"),
                "nodes": nodes, "edges": edges,
                "read_node_ids": list(session.navigator.workspace.nodes),
                "navigation": list(session.navigator.trace),
                "total_nodes": total, "scope_nodes": scoped, "visible_edges": visible_edges,
                "nodes_truncated": scoped > len(nodes), "edges_truncated": visible_edges > len(edges),
                "limits": dict(settings)}
