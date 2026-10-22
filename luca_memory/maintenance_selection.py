"""Deterministic routing from categories; legacy whole-group selection for manual plans."""


def route_categories(categories, required_reduction, member_limit):
    """Pack bounded directional routing groups and reach the target exactly.

    Full chunks precede smaller ones, minimizing the number of new routing nodes.
    Only the final selected chunk may be partial; leftovers keep their direct arcs.
    Category labels and direction never change and chunks never overlap.
    """
    if type(required_reduction) is not int or required_reduction < 1 or type(member_limit) is not int or member_limit < 2:
        raise ValueError("Routing requires a positive reduction and at least two members per group.")
    chunks = []
    for direction, title, members in categories:
        for offset in range(0, len(members), member_limit):
            chunk = members[offset:offset + member_limit]
            if len(chunk) >= 2:
                chunks.append((direction, title, chunk))
    chunks.sort(key=lambda item: -len(item[2]))  # Stable ties retain classification order.
    if sum(len(members) - 1 for _, _, members in chunks) < required_reduction:
        raise ValueError("The classification has insufficient compatible members to reach edge_target.")
    remaining = required_reduction
    selected = []
    for direction, title, members in chunks:
        if remaining == 0:
            break
        reduction = min(remaining, len(members) - 1)
        selected.append((title, direction, members[:reduction + 1]))
        remaining -= reduction
    return tuple(selected)


def select_groups(groups, required_reduction):
    """Minimize overshoot; break ties by group count, then proposal order.

    States retain only reductions below the target. A crossing is terminal:
    no subsequent grouping is added once enough arcs have been removed.
    """
    states = {0: ()}
    best = None
    for index, group in enumerate(groups):
        reduction = len(group.members) - 1
        for total, chosen in tuple(states.items()):
            new_total = total + reduction
            selection = (*chosen, index)
            if new_total >= required_reduction:
                candidate = new_total, len(selection), selection
                if best is None or candidate < best:
                    best = candidate
            else:
                previous = states.get(new_total)
                if previous is None or (len(selection), selection) < (len(previous), previous):
                    states[new_total] = selection
    if best is None:
        raise ValueError("The proposed grouping does not reach edge_target.")
    return tuple(groups[index] for index in best[2])
