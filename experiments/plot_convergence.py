"""Convergence plot (score vs iteration) of one SA run on a representative instance.

Two panels sharing the iteration axis: top = current and best score with the
reference value; bottom = temperature (log scale). The data is also written
as CSV next to the PNG.

Usage: python -m experiments.plot_convergence [--instance visit_large/large_chao66_r30]
                                              [--iterations 1000000] [--seed 0]
"""

import argparse
import csv
import math
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # file output only, no window
import matplotlib.pyplot as plt  # noqa: E402

from src.instance import load_instance  # noqa: E402
from src.sa import simulated_annealing  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
POINTS = 1000  # history samples per run

# Validated categorical slots 1-2 and neutral inks (light surface).
SURFACE = "#fcfcfb"
TEXT = "#0b0b0b"
TEXT_SECONDARY = "#52514e"
GRID = "#e4e3df"
BEST = "#2a78d6"
CURRENT = "#eb6834"


def reference_of(instance):
    """Reference value and type for 'group/name' from the group's references CSV."""
    group, name = instance.split("/", 1)
    folder = ROOT / "instances" / group
    with open(folder / "references.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["instance"] == name:
                return float(row["reference"]), row["type"]
    raise ValueError(f"no reference for {instance} in {folder / 'references.csv'}")


def style(ax):
    ax.set_facecolor(SURFACE)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.tick_params(colors=TEXT_SECONDARY, labelsize=9)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--instance", default="visit_large/large_chao66_r30")
    parser.add_argument("--iterations", type=int, default=1_000_000)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--out", type=Path, default=ROOT / "results" / "convergence.png")
    args = parser.parse_args()
    if args.iterations < POINTS:
        sys.exit(f"error: --iterations must be at least {POINTS}")

    try:
        inst = load_instance(ROOT / "instances" / f"{args.instance}.txt")
        reference, ref_type = reference_of(args.instance)
    except (OSError, ValueError) as e:
        sys.exit(f"error: {e}")
    res = simulated_annealing(inst, iterations=args.iterations, seed=args.seed,
                              history_every=args.iterations // POINTS)
    its = [h[0] for h in res.history]
    current = [h[1] for h in res.history]
    best = [h[2] for h in res.history]
    temps = [res.t0 * res.alpha ** i for i in its]

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out.with_suffix(".csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["iteration", "current_score", "best_score", "temperature"])
        writer.writerows(zip(its, current, best, (f"{t:.6g}" for t in temps)))

    fig, (ax_score, ax_temp) = plt.subplots(
        2, 1, sharex=True, figsize=(8, 5.2), gridspec_kw={"height_ratios": [3, 1.2]},
        facecolor=SURFACE)
    for ax in (ax_score, ax_temp):
        style(ax)

    ax_score.plot(its, current, color=CURRENT, linewidth=1.0, label="current solution")
    ax_score.plot(its, best, color=BEST, linewidth=2.0, label="best so far")
    ax_score.axhline(reference, color=TEXT_SECONDARY, linewidth=1.0, linestyle=(0, (4, 3)))
    ax_score.text(its[0], reference, f"reference {reference:g} ({ref_type})",
                  color=TEXT_SECONDARY, fontsize=9, ha="left", va="bottom")
    ax_score.text(its[-1], best[-1], f"  best {best[-1]:g}", color=TEXT, fontsize=9,
                  ha="left", va="center")
    ax_score.set_ylabel("score", color=TEXT_SECONDARY, fontsize=10)
    ax_score.legend(loc="lower right", frameon=False, fontsize=9, labelcolor=TEXT)
    ax_score.set_title(f"SA convergence on {inst.name} (n = {inst.n}, Tmax = {inst.tmax:g}, "
                       f"seed {args.seed})", color=TEXT, fontsize=11, loc="left")

    ax_temp.plot(its, temps, color=TEXT_SECONDARY, linewidth=1.5)
    ax_temp.set_yscale("log")
    ax_temp.yaxis.set_major_locator(matplotlib.ticker.LogLocator(base=10, subs=(1.0, 2.0, 5.0)))
    ax_temp.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}"))
    ax_temp.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    ax_temp.set_ylabel("temperature", color=TEXT_SECONDARY, fontsize=10)
    ax_temp.set_xlabel("iteration", color=TEXT_SECONDARY, fontsize=10)
    ax_temp.xaxis.set_major_formatter(
        matplotlib.ticker.FuncFormatter(
            lambda v, _: f"{v / 1e6:g}M" if v >= 1e6 else (f"{v / 1e3:g}k" if v else "0")))

    fig.tight_layout()
    fig.savefig(args.out, dpi=200, facecolor=SURFACE)
    print(f"greedy {res.initial_score:g} -> best {res.score:g} (reference {reference:g}); "
          f"T0 = {res.t0:.3g}, T_end = {temps[-1]:.3g}; saved {args.out}")
    if not math.isclose(best[-1], res.score):
        print("note: last history sample precedes the final best update")


if __name__ == "__main__":
    main()
