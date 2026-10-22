"""Select only the necessary whole groups, without changing semantic membership."""


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
