"""Plot median elapsed time from the benchmark CSV."""
import csv
from collections import defaultdict
from pathlib import Path
from statistics import median

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from griductive.experiments.benchmark import ROOT


def plot(directory):
    groups = defaultdict(list)
    with (directory / "benchmark.csv").open(encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            groups[row["stage"]].append(row)
    fig, ax = plt.subplots(figsize=(8, 5.8), layout="constrained")
    for y, (path, rows) in enumerate(groups.items()):
        solved = [float(r["elapsed_ms"]) for r in rows if r["status"] == "SOLVED"]
        value = median(solved) if solved else 0
        size = int(rows[0]["size"])
        ax.barh(y, value, height=.62, color={3:"#24847c", 4:"#426bb0", 5:"#935e8e"}[size])
        label = f"{value:.1f}" if solved else "—"
        if len(solved) < len(rows):
            label += f" ({len(solved)}/{len(rows)} solved)"
        ax.annotate(label, (value, y), xytext=(4, 0), textcoords="offset points", va="center")
    ax.set_yticks(range(len(groups)), [f"{Path(p).parent.name} / {Path(p).stem}" for p in groups])
    ax.invert_yaxis()
    ax.set_xlabel("Median elapsed time for solved runs (ms)")
    ax.set_title("Progressive solving time by stage", loc="left")
    ax.set_axisbelow(True)
    ax.grid(axis="x", alpha=.2)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.margins(x=.2)
    fig.savefig(directory / "runtime_by_stage.png", dpi=160)
    plt.close(fig)


if __name__ == "__main__":
    plot(ROOT / "results")
