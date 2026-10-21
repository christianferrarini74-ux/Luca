"""Represent partitions as unique ID assignments instead of duplicable lists."""


def grouping_schema(directory):
    directions = {}
    for direction in ("incoming", "outgoing"):
        directions[direction] = {"type": "object", "properties": {
            str(entry.id): {"type": ["string", "null"]}
            for entry in getattr(directory, direction) if entry.id != directory.focus_id},
            "additionalProperties": False}
    return {"type": "object", "properties": {"assignments": {"type": "object",
        "properties": directions, "required": ["incoming", "outgoing"], "additionalProperties": False}},
        "required": ["assignments"], "additionalProperties": False}


def groups_from_assignments(value, directory):
    assignments = value.get("assignments")
    if assignments is None:
        return value.get("groups")  # Compatibility with existing non-model adapters.
    if not isinstance(assignments, dict) or set(assignments) != {"incoming", "outgoing"}:
        raise ValueError("Invalid directional assignments")
    groups = []
    for direction, members in assignments.items():
        allowed = {str(entry.id) for entry in getattr(directory, direction) if entry.id != directory.focus_id}
        if not isinstance(members, dict) or set(members) - allowed:
            raise ValueError("Unknown assignment address")
        labels = {}
        for identity, label in members.items():
            if label is None:
                continue
            if not isinstance(label, str) or not label.strip():
                raise ValueError("Invalid group label")
            labels.setdefault(label.strip(), []).append(int(identity))
        groups.extend({"title": title, "direction": direction, "members": ids} for title, ids in labels.items())
    return groups
