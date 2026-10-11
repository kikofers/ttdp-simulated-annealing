"""Problem instances for the Tourist Trip Design Problem (TTDP).

File format (standard Orienteering Problem format, extended with visit times):

    Tmax P
    x y S [v]
    x y S [v]
    ...

- Tmax: time budget, P: number of paths (must be 1).
- One line per point: coordinates, score and an optional visit duration v
  (missing v means 0, so the classic OP benchmark files are read unchanged).
- The FIRST point in the file is the start, the SECOND point is the end.

Internally the points are reordered so that node 0 is the start and node n-1
is the end; nodes 1..n-2 are the attractions.
"""

import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from src.evaluation import FEASIBILITY_TOL


@dataclass
class Instance:
    name: str
    tmax: float
    x: np.ndarray       # x coordinates, shape (n,)
    y: np.ndarray       # y coordinates, shape (n,)
    score: np.ndarray   # S_i, 0 for start and end
    visit: np.ndarray   # v_i, 0 for start and end
    dist: np.ndarray    # t_ij: Euclidean travel time, shape (n, n)
    cost: np.ndarray    # t'_ij: modified cost, see build_cost_matrix()

    @property
    def n(self):
        """Number of nodes including start and end."""
        return len(self.score)

    @property
    def start(self):
        return 0

    @property
    def end(self):
        return self.n - 1


def build_cost_matrix(dist, visit):
    """Return the modified cost matrix t'_ij = t_ij + (v_i + v_j) / 2.

    Every attraction on a route is entered once and left once, so it receives
    v_i/2 + v_i/2 = v_i in total, while start and end have v = 0. Therefore
    the length of a route under t' equals its travel time plus the visit
    times of all visited attractions. With this transformation the TTDP
    becomes a standard Orienteering Problem on the costs t', and the rest of
    the code (evaluation, SA, exact DP) never has to handle visit times.

    The diagonal is set to 0 (a node is never followed by itself).
    """
    cost = dist + (visit[:, None] + visit[None, :]) / 2.0
    np.fill_diagonal(cost, 0.0)
    return cost


class InstanceError(ValueError):
    """Invalid instance file or instance data (the message says what and where)."""


def validate_instance(inst):
    """Check that `inst` describes a meaningful TTDP instance.

    Called when an instance is created and again before solving, so that a
    corrupted or hand-modified instance fails with a clear message instead of
    producing wrong results.
    """
    n = inst.n
    for attr in ("x", "y", "score", "visit"):
        values = getattr(inst, attr)
        if values.shape != (n,):
            raise InstanceError(f"{inst.name}: {attr} has shape {values.shape}, expected ({n},)")
        bad = np.flatnonzero(~np.isfinite(values))
        if bad.size:
            raise InstanceError(f"{inst.name}: {attr} of node {bad[0]} is not a finite number")
    if n < 2:
        raise InstanceError(f"{inst.name}: need at least a start and an end point")
    if not np.isfinite(inst.tmax):
        raise InstanceError(f"{inst.name}: Tmax must be a finite number, got {inst.tmax}")
    for attr in ("score", "visit"):
        bad = np.flatnonzero(getattr(inst, attr) < 0)
        if bad.size:
            raise InstanceError(f"{inst.name}: node {bad[0]} has negative {attr}")
    if inst.visit[inst.start] != 0 or inst.visit[inst.end] != 0:
        raise InstanceError(f"{inst.name}: start and end must have visit time 0")
    for attr in ("dist", "cost"):
        matrix = getattr(inst, attr)
        if matrix.shape != (n, n) or not np.all(np.isfinite(matrix)):
            raise InstanceError(f"{inst.name}: {attr} matrix must be finite with shape ({n}, {n})")
    direct = inst.cost[inst.start, inst.end]
    if direct > inst.tmax + FEASIBILITY_TOL:
        raise InstanceError(f"{inst.name}: no feasible route, the direct trip start -> end "
                            f"takes {direct:.6g} > Tmax = {inst.tmax:g}")


def make_instance(name, tmax, x, y, score, visit):
    """Build and validate an Instance from arrays already in internal order (start..end)."""
    arrays = {}
    for attr, values in (("x", x), ("y", y), ("score", score), ("visit", visit)):
        try:
            arrays[attr] = np.asarray(values, dtype=float)
        except (TypeError, ValueError):
            raise InstanceError(f"{name}: {attr} must contain only numbers") from None
        if arrays[attr].ndim != 1:
            raise InstanceError(f"{name}: {attr} must be a one-dimensional sequence")
    lengths = {len(a) for a in arrays.values()}
    if len(lengths) != 1:
        raise InstanceError(f"{name}: coordinate/score/visit arrays differ in length")
    x, y, score, visit = arrays["x"], arrays["y"], arrays["score"], arrays["visit"]

    with np.errstate(invalid="ignore"):  # non-finite input is reported by validate_instance
        dist = np.hypot(x[:, None] - x[None, :], y[:, None] - y[None, :])
        cost = build_cost_matrix(dist, visit)
    inst = Instance(name, float(tmax), x, y, score, visit, dist, cost)
    validate_instance(inst)
    return inst


def load_instance(path):
    """Read an instance file (see module docstring for the format).

    Raises InstanceError with the file name and line number if the file does
    not follow the format or contains invalid values.
    """
    path = Path(path)
    lines = [(no, line.split())
             for no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1)
             if line.strip()]
    if not lines:
        raise InstanceError(f"{path.name}: file is empty")

    def number(value, line_no, what, non_negative=False):
        try:
            result = float(value)
        except ValueError:
            raise InstanceError(f"{path.name}, line {line_no}: {what} must be a number, "
                                f"got {value!r}") from None
        if not math.isfinite(result):
            raise InstanceError(f"{path.name}, line {line_no}: {what} must be finite, got {value!r}")
        if non_negative and result < 0:
            raise InstanceError(f"{path.name}, line {line_no}: {what} must be >= 0, got {value!r}")
        return result

    header_no, header = lines[0]
    if len(header) not in (1, 2):
        raise InstanceError(f"{path.name}, line {header_no}: header must be 'Tmax P', "
                            f"got {' '.join(header)!r}")
    tmax = number(header[0], header_no, "Tmax", non_negative=True)
    if len(header) == 2 and number(header[1], header_no, "P") != 1:
        raise InstanceError(f"{path.name}, line {header_no}: only single-path instances "
                            f"(P = 1) are supported, got P = {header[1]}")

    rows = []
    for line_no, fields in lines[1:]:
        if len(fields) not in (3, 4):
            raise InstanceError(f"{path.name}, line {line_no}: expected 'x y S [v]', "
                                f"got {' '.join(fields)!r}")
        x = number(fields[0], line_no, "x")
        y = number(fields[1], line_no, "y")
        s = number(fields[2], line_no, "score S", non_negative=True)
        v = number(fields[3], line_no, "visit time v", non_negative=True) if len(fields) == 4 else 0.0
        rows.append((x, y, s, v))
    if len(rows) < 2:
        raise InstanceError(f"{path.name}: need at least a start and an end point, "
                            f"found {len(rows)} point(s)")

    # File order: start, end, attractions -> internal order: start, attractions, end.
    rows = [rows[0]] + rows[2:] + [rows[1]]
    x, y, score, visit = zip(*rows)
    try:
        return make_instance(path.stem, tmax, x, y, score, visit)
    except InstanceError as e:
        # Report the file name (with extension) like the parsing errors above.
        detail = str(e).removeprefix(f"{path.stem}: ")
        raise InstanceError(f"{path.name}: {detail}") from None


def save_instance(inst, path):
    """Write an instance in the file format above (start first, end second)."""
    order = [inst.start, inst.end] + list(range(1, inst.end))
    lines = [f"{inst.tmax:.10g} 1"]
    for i in order:
        values = (inst.x[i], inst.y[i], inst.score[i], inst.visit[i])
        lines.append(" ".join(f"{v:.10g}" for v in values))
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
