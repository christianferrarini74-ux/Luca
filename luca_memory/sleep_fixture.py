"""Controlled graphs and structural oracles for sleep diagnostics, not library ingestion."""

import json

from .node import KnowledgeNode


def graph_snapshot(memory):
    """Capture durable knowledge and indexes, excluding expected audit/revision changes."""
    db = memory.store.connection
    with memory.store.lock:
        return {name: [tuple(row) for row in db.execute(query)] for name, query in {
            "cells": "SELECT id,content,created_at FROM cells ORDER BY id",
            "edges": "SELECT source_id,target_id,last_used_at,use_count FROM edges ORDER BY source_id,target_id",
            "families": "SELECT part_id,root_id FROM family_parts ORDER BY part_id",
            "catalog": "SELECT node_id,title FROM node_catalog ORDER BY node_id",
            "aliases": "SELECT cell_id,alias FROM cell_aliases ORDER BY cell_id,alias",
            "entries": "SELECT node_id,title,terms FROM entry_search ORDER BY node_id",
            "search": "SELECT rowid,* FROM cell_search ORDER BY rowid",
        }.items()}


def populate(memory, settings):
    """Build one overflowing family plus controls exactly at upper and target limits."""
    if memory.store.has_cells():
        raise ValueError("The sleep fixture requires an empty disposable store.")
    topics = ("Botanica", "Astronomia")
    assignments = {"incoming": {}, "outgoing": {}}
    with memory.store.transaction():
        def node(title, content="Controlled diagnostic payload."):
            identity = memory.store.next_cell_id()
            memory.update_node(KnowledgeNode(identity, f"sleep_probe_{identity}", title, content, created_at=1))
            return identity

        root = node("Indice interdisciplinare di prova")
        parts = [node(f"Parte {index} dell'indice") for index in range(1, 4)]
        for part in parts:
            memory.attach_part(root, part)
        # Labels are an intentionally easy semantic oracle, never a hidden model instruction.
        for index in range(settings.edge_upper + 2):
            direction = "incoming" if index % 2 else "outgoing"
            category = topics[(index // 2) % 2]
            member = node(f"{category}: scheda controllata {index + 1}", f"{category}. Identificatore {index + 1}.")
            assignments[direction][member] = category
            memory.connect(member, root) if direction == "incoming" else memory.connect(root, member)
        controls = {}
        for label, degree in (("upper", settings.edge_upper), ("target", settings.edge_target)):
            control = node(f"Controllo alla soglia {label}")
            controls[label] = control
            for index in range(degree):
                memory.connect(control, node(f"Voce {label} {index + 1}"))
    return {"root": root, "parts": parts, "controls": controls, "assignments": assignments,
            "before": graph_snapshot(memory)}


def oracle_groups(fixture):
    """Deterministic proposals exercise the Core independently of model taxonomy quality."""
    groups = []
    for direction, members in fixture["assignments"].items():
        for category in sorted(set(members.values())):
            ids = [identity for identity, value in members.items() if value == category]
            if len(ids) >= 2:
                groups.append({"title": category, "direction": direction, "members": ids})
    return groups


def _reachable(edges, originals):
    adjacency = {}
    for source, target, *_ in edges:
        adjacency.setdefault(source, set()).add(target)
    result = set()
    for source in originals:
        seen, pending = set(), list(adjacency.get(source, ()))
        while pending:
            target = pending.pop()
            if target in seen:
                continue
            seen.add(target)
            pending.extend(adjacency.get(target, set()) - seen)
        result.update((source, target) for target in seen if target in originals)
    return result


def verify_regrouping(memory, settings, fixture, operation):
    """Check exact routes, all original-node reachability, content, families and indexes."""
    before, after = fixture["before"], graph_snapshot(memory)
    row = memory.store.connection.execute(
        "SELECT payload FROM maintenance_operations WHERE id=? AND active=1", (operation,)).fetchone()
    if row is None:
        raise AssertionError("No committed active maintenance operation.")
    record = json.loads(row[0])
    created = set(record["created_ids"])
    edges = {(source, target) for source, target, *_ in after["edges"]}
    original_ids = {identity for identity, *_ in before["cells"]}
    checks = {
        "within_target": memory.directory(fixture["root"]).external_degree <= settings.edge_target,
        "original_contents_unchanged": [row for row in after["cells"] if row[0] in original_ids] == before["cells"],
        "families_unchanged": after["families"] == before["families"],
        "all_original_routes_preserved": all((source, target) in edges or any(
            (source, group) in edges and (group, target) in edges for group in created)
            for source, target, *_ in before["edges"]),
        "original_reachability_unchanged": _reachable(before["edges"], original_ids) == _reachable(after["edges"], original_ids),
        "generated_groups_within_upper": all(memory.directory(identity).external_degree <= settings.edge_upper for identity in created),
        "controls_unchanged": all(memory.directory(identity).external_degree == getattr(settings, "edge_" + label)
                                  for label, identity in fixture["controls"].items()),
        "shared_family_directory": all(memory.directory(part) == memory.directory(fixture["root"]) for part in fixture["parts"]),
        "generated_groups_indexed": created <= {row[0] for row in after["catalog"]} & {int(row[0]) for row in after["entries"]},
        "original_entries_unchanged": [row for row in after["entries"] if int(row[0]) in original_ids] == before["entries"],
    }
    taxonomy = [{"title": group["title"], "direction": group["direction"],
                 "member_ids": group["members"],
                 "source_categories": sorted({fixture["assignments"][group["direction"]][member]
                                              for member in group["members"]})}
                for group in record["plan"]["groups"]]
    return {"checks": checks, "groups": taxonomy, "degree_before": record["plan"]["degree_before"],
            "degree_after": memory.directory(fixture["root"]).external_degree,
            "thematically_pure": all(len(group["source_categories"]) == 1 for group in taxonomy)}
