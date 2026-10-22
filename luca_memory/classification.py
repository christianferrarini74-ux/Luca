"""Complete, revision-bound semantic labels, independent of routing arithmetic."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ClassifiedDirectory:
    focus_id: int
    revision: int
    incoming: tuple[tuple[int, str | None], ...]
    outgoing: tuple[tuple[int, str | None], ...]

    def payload(self):
        return {"focus_id": self.focus_id, "revision": self.revision,
                "assignments": {direction: {str(identity): label for identity, label in getattr(self, direction)}
                                for direction in ("incoming", "outgoing")}}

    def categories(self, directory):
        """Validate public records again at the Core boundary, including omitted/duplicate IDs."""
        if type(self.focus_id) is not int or type(self.revision) is not int or (self.focus_id, self.revision) != (directory.focus_id, directory.revision):
            from .synaptic import StaleRevision
            raise StaleRevision("The classified directory is stale; classify the current directory again.")
        categories = []
        for direction in ("incoming", "outgoing"):
            allowed = {entry.id for entry in getattr(directory, direction) if entry.id != directory.focus_id}
            seen, labels = set(), {}
            entries = getattr(self, direction)
            if not isinstance(entries, tuple) or any(not isinstance(entry, tuple) or len(entry) != 2 for entry in entries):
                raise ValueError("Classification entries must be immutable ID/label pairs.")
            for identity, _ in entries:
                if type(identity) is not int or identity not in allowed or identity in seen:
                    raise ValueError("Classification IDs must be distinct existing directional addresses.")
                seen.add(identity)
            for identity, label in sorted(entries, key=lambda entry: entry[0]):
                if label is None:
                    continue
                if not isinstance(label, str) or not label.strip() or len(label) > 256:
                    raise ValueError("Classification labels must be null or nonempty strings of at most 256 characters.")
                labels.setdefault(label.strip(), []).append(identity)
            if seen != allowed:
                raise ValueError("Every external address needs a category or explicit null.")
            categories.extend((direction, title, tuple(sorted(members))) for title, members in labels.items())
        return tuple(categories)


def classification_from_assignments(value, directory):
    """Require coverage, but never infer a label for missing or uncertain knowledge."""
    if not isinstance(value, dict) or set(value) != {"assignments"}:
        raise ValueError("A complete classification requires directional assignments.")
    assignments = value["assignments"]
    if not isinstance(assignments, dict) or set(assignments) != {"incoming", "outgoing"}:
        raise ValueError("Invalid classification directions.")
    directions = {}
    for direction in ("incoming", "outgoing"):
        allowed = {str(entry.id) for entry in getattr(directory, direction) if entry.id != directory.focus_id}
        members = assignments[direction]
        if not isinstance(members, dict) or set(members) != allowed:
            raise ValueError("Every external address needs a category or explicit null.")
        directions[direction] = tuple((int(identity), members[identity]) for identity in sorted(members, key=int))
    result = ClassifiedDirectory(directory.focus_id, directory.revision, **directions)
    result.categories(directory)
    return result
