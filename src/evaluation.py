"""Solution evaluation for the TTDP (as an Orienteering Problem on costs t').

A solution is a route: a list of node indices that starts at node 0 (start),
ends at node n-1 (end) and contains each attraction at most once. Attractions
not on the route are unvisited.

All lengths are measured with the modified cost matrix t' (Instance.cost), so
the length of a route equals its travel time plus the visit times of the
visited attractions (see build_cost_matrix in src/instance.py).

`cost` can be a numpy array or a list of lists; both are indexed as
cost[i][j]. The SA passes a list of lists (inst.cost.tolist()) because
indexing Python lists element by element is much faster than numpy arrays.

The *_delta functions return the change in route length caused by a move in
O(1) time, without modifying the route. two_opt_delta relies on t' being
symmetric, which holds because t is Euclidean and (v_i + v_j)/2 is symmetric.

Positions are checked explicitly: Python would silently accept 0 or -1 as a
list index and the delta would then be computed for the wrong edges. The
check costs about 2% of SA runtime. Whether `node` is already on the route
cannot be checked in O(1); the SA guarantees it by drawing from the unvisited set.
"""

from numbers import Integral

# Floating point slack when comparing a route length with Tmax.
FEASIBILITY_TOL = 1e-9

# Weight of the length tie-break in the objective f = score - w * length.
# With integer scores a score gain of 1 must outweigh any length difference,
# which holds as long as route lengths stay below 1 / w = 1e6.
LENGTH_WEIGHT = 1e-6


def route_length(cost, route):
    """Total cost of the route under t' (= travel time + visit time)."""
    return sum(cost[a][b] for a, b in zip(route, route[1:]))


def route_score(score, route):
    """Sum of scores of the nodes on the route (start and end score 0)."""
    return sum(score[i] for i in route)


def objective(total_score, length, length_weight=LENGTH_WEIGHT):
    """Value to maximize: score first, shorter route as a tie-break."""
    return total_score - length_weight * length


def route_errors(inst, route):
    """Return a list of reasons why the route is infeasible (empty if feasible)."""
    errors = []
    if len(route) < 2 or route[0] != inst.start or route[-1] != inst.end:
        errors.append(f"route must start at {inst.start} and end at {inst.end}")
    if any(not isinstance(i, Integral) for i in route):
        return errors + ["route must contain integer node indices"]
    middle = route[1:-1]
    if any(not (0 < i < inst.end) for i in middle):
        errors.append("route contains start/end in the middle or an invalid node")
    if len(set(middle)) != len(middle):
        errors.append("route visits a node more than once")
    if not errors:
        length = route_length(inst.cost, route)
        if length > inst.tmax + FEASIBILITY_TOL:
            errors.append(f"route length {length:.6f} exceeds Tmax {inst.tmax}")
    return errors


def is_feasible(inst, route):
    return not route_errors(inst, route)


def _check_position(route, pos, last):
    if not 1 <= pos <= last:
        raise IndexError(f"position {pos} outside 1..{last} for a route of length {len(route)}")


def insert_delta(cost, route, pos, node):
    """Length change when `node` is inserted so that it becomes route[pos]
    (between route[pos-1] and route[pos]); 1 <= pos <= len(route)-1."""
    _check_position(route, pos, len(route) - 1)
    a, b = route[pos - 1], route[pos]
    return cost[a][node] + cost[node][b] - cost[a][b]


def remove_delta(cost, route, pos):
    """Length change when route[pos] is removed; 1 <= pos <= len(route)-2."""
    _check_position(route, pos, len(route) - 2)
    a, k, b = route[pos - 1], route[pos], route[pos + 1]
    return cost[a][b] - cost[a][k] - cost[k][b]


def replace_delta(cost, route, pos, node):
    """Length change when route[pos] is replaced by `node`; 1 <= pos <= len(route)-2."""
    _check_position(route, pos, len(route) - 2)
    a, k, b = route[pos - 1], route[pos], route[pos + 1]
    return cost[a][node] + cost[node][b] - cost[a][k] - cost[k][b]


def two_opt_delta(cost, route, i, j):
    """Length change when the segment route[i..j] is reversed;
    1 <= i < j <= len(route)-2. Only the two boundary edges change."""
    if not 1 <= i < j <= len(route) - 2:
        raise IndexError(f"segment {i}..{j} invalid for a route of length {len(route)}, "
                         f"need 1 <= i < j <= {len(route) - 2}")
    a, b = route[i - 1], route[i]
    c, d = route[j], route[j + 1]
    return cost[a][c] + cost[b][d] - cost[a][b] - cost[c][d]


def cheapest_insertion(cost, route, node):
    """Return (pos, delta) of the cheapest position to insert `node`.

    Tries every edge of the route, so this is O(len(route))."""
    if len(route) < 2:
        raise ValueError("route must contain at least start and end")
    best_pos, best_delta = 1, float("inf")
    for pos in range(1, len(route)):
        # Same formula as insert_delta, inlined: pos is always in range here.
        a, b = route[pos - 1], route[pos]
        delta = cost[a][node] + cost[node][b] - cost[a][b]
        if delta < best_delta:
            best_pos, best_delta = pos, delta
    return best_pos, best_delta
