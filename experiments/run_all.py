"""Run all experiments: RUNS seeded SA runs per instance and budget, then summarize.

Instances and references:
  classic      instances/classic/selection.csv      best-known (literature)
  visit_small  instances/visit_small/references.csv optimal (exact DP)
  visit_large  instances/visit_large/references.csv best-known (long SA runs)

For every instance, budget (iterations) and seed 0..RUNS-1 one SA run is made.
Outputs (in --out, default results/):
  runs.csv     one row per run (score, length, runtime, ...)
  results.csv  per instance and budget: best/avg/worst score, gap % =
               (ref - score) / ref * 100, runs that reach the reference, avg runtime
  summary.md   markdown tables of results.csv

Run serially (--workers 1, default) so that measured runtimes are not
distorted by other processes.

Usage: python -m experiments.run_all [--iterations 1000000 100000] [--runs 10]
                                     [--workers 1] [--out results]
"""

import argparse
import csv
import platform
import statistics
import sys
import time
from multiprocessing import Pool
from pathlib import Path

from src.exact_dp import solve_exact
from src.instance import load_instance
from src.sa import simulated_annealing

ROOT = Path(__file__).resolve().parent.parent
INSTANCES = ROOT / "instances"
GROUPS = ("classic", "visit_small", "visit_large")


def shown(path):
    """Path for console output: relative to the repository when possible. The
    repository path contains non-ASCII letters (e.g. "Ģ") that a cp1252 console
    cannot encode."""
    path = Path(path).resolve()
    return path.relative_to(ROOT) if path.is_relative_to(ROOT) else path


def gap(reference, score):
    """Relative gap in percent; negative if the score beats the reference."""
    if reference <= 0:
        raise ValueError(f"reference must be positive to compute a gap, got {reference}")
    return (reference - score) / reference * 100


def load_tasks():
    """All experiment instances with their reference values."""
    tasks = []
    sources = {
        "classic": INSTANCES / "classic" / "selection.csv",
        "visit_small": INSTANCES / "visit_small" / "references.csv",
        "visit_large": INSTANCES / "visit_large" / "references.csv",
    }
    classic_types = {}
    with open(INSTANCES / "classic" / "references.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            classic_types[row["instance"]] = row["type"]
    for group, csv_path in sources.items():
        if not csv_path.exists():
            raise FileNotFoundError(f"missing reference file {csv_path}")
        with open(csv_path, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                path = csv_path.parent / f"{row['instance']}.txt"
                ref_type = classic_types[row["instance"]] if group == "classic" else row["type"]
                tasks.append({"group": group, "instance": row["instance"], "path": path,
                              "reference": float(row["reference"]), "reference_type": ref_type})
    return tasks


def run_one(job):
    """One SA run; returns a row for runs.csv."""
    task, iterations, seed = job
    inst = load_instance(task["path"])
    res = simulated_annealing(inst, iterations=iterations, seed=seed)
    return {"group": task["group"], "instance": task["instance"], "n": inst.n,
            "tmax": f"{inst.tmax:g}", "iterations": iterations, "seed": seed,
            "score": res.score, "length": round(res.length, 6),
            "initial_score": res.initial_score, "runtime_s": round(res.runtime, 4),
            "reference": task["reference"], "reference_type": task["reference_type"]}


def summarize(runs, dp_times):
    """Aggregate runs.csv rows into one results.csv row per (instance, iterations)."""
    keys = []
    for r in runs:
        key = (r["group"], r["instance"], r["iterations"])
        if key not in keys:
            keys.append(key)
    rows = []
    for group, instance, iterations in keys:
        mine = [r for r in runs if (r["group"], r["instance"], r["iterations"]) == (group, instance, iterations)]
        scores = [r["score"] for r in mine]
        ref = mine[0]["reference"]
        rows.append({
            "group": group, "instance": instance, "n": mine[0]["n"], "tmax": mine[0]["tmax"],
            "reference": f"{ref:g}", "reference_type": mine[0]["reference_type"],
            "iterations": iterations, "runs": len(mine),
            "best": f"{max(scores):g}", "avg": f"{statistics.mean(scores):.2f}",
            "worst": f"{min(scores):g}",
            "gap_best_pct": f"{gap(ref, max(scores)):.2f}",
            "gap_avg_pct": f"{gap(ref, statistics.mean(scores)):.2f}",
            "gap_worst_pct": f"{gap(ref, min(scores)):.2f}",
            "hits": sum(s >= ref for s in scores),
            "above_reference": sum(s > ref for s in scores),
            "greedy_score": f"{mine[0]['initial_score']:g}",
            "avg_runtime_s": f"{statistics.mean(r['runtime_s'] for r in mine):.3f}",
            "exact_dp_runtime_s": f"{dp_times[instance]:.3f}" if instance in dp_times else "",
        })
    return rows


def write_csv(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def markdown_summary(results, args, total_time):
    main_budget = max(args.iterations)
    lines = [
        "# Experiment results",
        "",
        f"SA with {main_budget:,} iterations (main budget), {args.runs} runs per instance "
        f"(seeds 0-{args.runs - 1}). Gap % = (reference - score) / reference * 100; "
        "'hits' = runs that reach the reference. Runtime = average wall time of one run.",
        f"Machine: {platform.processor() or platform.machine()}, Python {platform.python_version()}, "
        f"runs executed with {args.workers} worker(s). Total experiment time {total_time / 60:.1f} min.",
        "",
    ]
    titles = {
        "classic": "Classic OP benchmarks (v = 0), reference = best-known from the literature",
        "visit_small": "Small instances with visit times, reference = exact DP optimum",
        "visit_large": "Large instances with visit times, reference = best of 10 long SA runs",
    }
    for group in GROUPS:
        rows = [r for r in results if r["group"] == group and r["iterations"] == main_budget]
        if not rows:
            continue
        extra = " DP time s |" if group == "visit_small" else ""
        lines += [f"## {titles[group]}", "",
                  "| Instance | n | Tmax | Reference | Greedy | Best | Avg | Worst | Gap best % "
                  f"| Gap avg % | Gap worst % | Hits | SA time s |{extra}",
                  "|---|---|---|---|---|---|---|---|---|---|---|---|---|" + ("---|" if extra else "")]
        for r in rows:
            dp = f" {r['exact_dp_runtime_s']} |" if extra else ""
            lines.append(f"| {r['instance']} | {r['n']} | {r['tmax']} | {r['reference']} "
                         f"| {r['greedy_score']} | {r['best']} | {r['avg']} | {r['worst']} "
                         f"| {r['gap_best_pct']} | {r['gap_avg_pct']} | {r['gap_worst_pct']} "
                         f"| {r['hits']}/{r['runs']} | {r['avg_runtime_s']} |{dp}")
        lines.append("")

    if len(args.iterations) > 1:
        lines += ["## Budget comparison (averages over the instances of each group)", "",
                  "| Group | Iterations | Avg gap % | Worst gap % | Hits | Avg SA time s |",
                  "|---|---|---|---|---|---|"]
        for group in GROUPS:
            for iterations in sorted(args.iterations):
                rows = [r for r in results if r["group"] == group and r["iterations"] == iterations]
                if not rows:
                    continue
                hits = sum(r["hits"] for r in rows)
                runs = sum(r["runs"] for r in rows)
                lines.append(
                    f"| {group} | {iterations:,} "
                    f"| {statistics.mean(float(r['gap_avg_pct']) for r in rows):.2f} "
                    f"| {max(float(r['gap_worst_pct']) for r in rows):.2f} "
                    f"| {hits}/{runs} "
                    f"| {statistics.mean(float(r['avg_runtime_s']) for r in rows):.3f} |")
        lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--iterations", type=int, nargs="+", default=[1_000_000, 100_000])
    parser.add_argument("--runs", type=int, default=10)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--out", type=Path, default=ROOT / "results")
    args = parser.parse_args()
    sys.stdout.reconfigure(errors="backslashreplace")
    if args.runs < 1 or args.workers < 1 or min(args.iterations) < 1:
        sys.exit("error: --runs, --workers and --iterations must be positive")

    try:
        tasks = load_tasks()
    except (OSError, ValueError, KeyError) as e:
        sys.exit(f"error: {e}")
    args.out.mkdir(parents=True, exist_ok=True)

    t_begin = time.perf_counter()
    # Exact DP runtime of the small instances, to compare with SA runtime.
    dp_times = {t["instance"]: solve_exact(load_instance(t["path"])).runtime
                for t in tasks if t["group"] == "visit_small"}

    jobs = [(t, it, seed) for it in args.iterations for t in tasks for seed in range(args.runs)]
    runs = []
    with Pool(args.workers) as pool:
        for i, row in enumerate(pool.imap(run_one, jobs), start=1):
            runs.append(row)
            if i % args.runs == 0:
                print(f"[{i}/{len(jobs)}] {row['group']}/{row['instance']} "
                      f"iterations={row['iterations']} last score={row['score']:g}", flush=True)
    total_time = time.perf_counter() - t_begin

    results = summarize(runs, dp_times)
    write_csv(args.out / "runs.csv", runs)
    write_csv(args.out / "results.csv", results)
    (args.out / "summary.md").write_text(markdown_summary(results, args, total_time), encoding="utf-8")
    above = [r["instance"] for r in results if r["above_reference"]]
    if above:
        print(f"NOTE: runs above the reference on {above} (reference is not optimal there)")
    print(f"done in {total_time / 60:.1f} min -> {shown(args.out)}")


if __name__ == "__main__":
    main()
