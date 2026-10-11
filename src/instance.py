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

from dataclasses import dataclass
from pathlib import Path

import numpy as np


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


def make_instance(name, tmax, x, y, score, visit):
    """Build an Instance from arrays already in internal order (start..end)."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    score = np.asarray(score, dtype=float)
    visit = np.asarray(visit, dtype=float)

    if not (len(x) == len(y) == len(score) == len(visit)):
        raise ValueError(f"{name}: coordinate/score/visit arrays differ in length")
    if len(x) < 2:
        raise ValueError(f"{name}: need at least a start and an end point")
    if np.any(visit < 0):
        raise ValueError(f"{name}: negative visit time")
    if visit[0] != 0 or visit[-1] != 0:
        raise ValueError(f"{name}: start and end must have visit time 0")

    dist = np.hypot(x[:, None] - x[None, :], y[:, None] - y[None, :])
    cost = build_cost_matrix(dist, visit)
    return Instance(name, float(tmax), x, y, score, visit, dist, cost)


def load_instance(path):
    """Read an instance file (see module docstring for the format)."""
    path = Path(path)
    lines = [line.split() for line in path.read_text().splitlines() if line.strip()]

    header = lines[0]
    tmax = float(header[0])
    paths = int(header[1]) if len(header) > 1 else 1
    if paths != 1:
        raise ValueError(f"{path.name}: expected 1 path, got {paths}")

    rows = []
    for fields in lines[1:]:
        if len(fields) not in (3, 4):
            raise ValueError(f"{path.name}: expected 'x y S [v]', got {fields}")
        x, y, s = map(float, fields[:3])
        v = float(fields[3]) if len(fields) == 4 else 0.0
        rows.append((x, y, s, v))

    # File order: start, end, attractions -> internal order: start, attractions, end.
    rows = [rows[0]] + rows[2:] + [rows[1]]
    x, y, score, visit = zip(*rows)
    return make_instance(path.stem, tmax, x, y, score, visit)


def save_instance(inst, path):
    """Write an instance in the file format above (start first, end second)."""
    order = [inst.start, inst.end] + list(range(1, inst.end))
    lines = [f"{inst.tmax:.10g} 1"]
    for i in order:
        values = (inst.x[i], inst.y[i], inst.score[i], inst.visit[i])
        lines.append(" ".join(f"{v:.10g}" for v in values))
    Path(path).write_text("\n".join(lines) + "\n")
