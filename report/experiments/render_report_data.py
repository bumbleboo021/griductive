"""Build the LaTeX tables and chart data from the recorded benchmark outputs."""

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median
from tempfile import NamedTemporaryFile


ROOT = Path(__file__).resolve().parents[2]
HEURISTICS = ("smallest", "jw")
METADATA = (
    "manifest", "source_commit", "started_utc", "platform", "cpu", "python",
    "repeats", "timeout_seconds_per_call", "process_timeout_seconds", "stress_stage",
)
WORKLOAD = ("primary_vars", "peak_aux_vars", "peak_clauses", "total_sat_calls", "reveal_steps")
METRICS = ("total_decisions", "total_propagations", "total_backtracks", "solver_ms", "elapsed_ms")
ROW_END = r" \\"


def load_results(root, heuristic):
    directory = root / heuristic
    report = json.loads((directory / "benchmark.json").read_text(encoding="utf-8"))
    if report["heuristic"] != heuristic:
        raise ValueError(f"{directory}: wrong heuristic in JSON")
    with (directory / "benchmark.csv").open(encoding="utf-8", newline="") as stream:
        csv_rows = list(csv.DictReader(stream))
    summaries = [run["summary"] for run in report["runs"]]
    if len(csv_rows) != len(summaries):
        raise ValueError(f"{directory}: CSV and JSON have different run counts")
    for i, (row, summary) in enumerate(zip(csv_rows, summaries), 1):
        if set(summary) - row.keys() or any(
            value != ("" if summary.get(key) is None else str(summary[key]))
            for key, value in row.items()
        ):
            raise ValueError(f"{directory}: CSV and JSON disagree at data row {i}")

    stages = report["manifest"]["stages"]
    expected = {
        (stage["path"], stage["size"], stage["seed"], rep)
        for stage in stages
        for rep in range(1, report["repeats"] + 1)
    }
    actual = {(r["stage"], r["size"], r["seed"], r["run"]) for r in summaries}
    if len(actual) != len(summaries) or expected != actual:
        raise ValueError(f"{directory}: missing, duplicate or unexpected runs")
    if set(report["validation"]) != {stage["path"] for stage in stages}:
        raise ValueError(f"{directory}: validation results do not match the manifest")
    return report


def format_number(value, places=0):
    if value is None:
        return "--"
    if not places and int(value) != value:
        places = 1
    return f"{value:,.{places}f}".replace(",", r"\,").replace(".", ",")


def value_at(runs, field, aggregate=median):
    values = [r[field] for r in runs if r.get(field) is not None]
    return aggregate(values) if values else None


def tex_escape(value):
    escapes = {
        "\\": r"\textbackslash{}", "{": r"\{", "}": r"\}", "%": r"\%",
        "#": r"\#", "&": r"\&", "_": r"\_", "$": r"\$",
        "~": r"\textasciitilde{}", "^": r"\textasciicircum{}",
    }
    return "".join(escapes.get(char, char) for char in str(value))


def scatter_plot(groups):
    times = [time for pairs in groups.values() for pair in pairs for time in pair]
    if not times:
        return ""

    low, high = min(times) * 0.82, max(times) * 1.22
    plots = [rf"\addplot[experiment identity] coordinates {{({low:.10g},{low:.10g}) ({high:.10g},{high:.10g})}};"]
    for size, pairs in sorted(groups.items()):
        points = " ".join(f"({x:.10g},{y:.10g})" for x, y in pairs)
        plots.append(rf"\addplot+[only marks] coordinates {{{points}}};")
        plots.append(rf"\addlegendentry{{\({size}\times{size}\)}}")
    return "\n".join(plots)


def make_row(values):
    return " & ".join(map(str, values)) + ROW_END


def series_plot(series):
    return "\n".join(
        r"\addplot coordinates {" + " ".join(f"({value:.8g},{row})" for value, row in points) + "};\n"
        + rf"\addlegendentry{{\texttt{{{heuristic}}}}}"
        for heuristic, points in zip(HEURISTICS, series)
        if points
    )


def make_data(results, destination):
    baseline, alternative = [load_results(results, h) for h in HEURISTICS]
    for field in METADATA:
        if baseline[field] != alternative[field]:
            raise ValueError(f"Configurations have different {field!r}")

    reports = (baseline, alternative)
    runs_by_stage = [defaultdict(list), defaultdict(list)]
    for report, grouped in zip(reports, runs_by_stage):
        for run in report["runs"]:
            grouped[run["summary"]["stage"]].append(run)

    stress = baseline["stress_stage"]
    workload, times, memory_rows, workload_counts, statuses = [], [], [], [], []
    labels, scatter_groups = [], defaultdict(list)
    memory_points, decision_points = [[], []], [[], []]
    matched = main_faster = main_lower_memory = time_pairs = memory_pairs = 0
    last_size = None
    stages = baseline["manifest"]["stages"]
    macros = {}
    for stage in stages:
        path, size, seed = stage["path"], stage["size"], stage["seed"]
        stage_id = Path(path).stem.removeprefix("level_")
        if not re.fullmatch(r"[0-9]+", stage_id):
            raise ValueError(f"Unexpected level filename: {path}")
        label = rf"\({size}\times{size}\)/{stage_id}"
        run_groups = [grouped[path] for grouped in runs_by_stage]
        successful = [[run for run in group if run["summary"]["status"] == "SOLVED"]
                      for group in run_groups]
        traces = {
            tuple((s["cell"], s["status"], tuple(s["cnf"]), s["sat_calls"]) for s in run["steps"])
            for group in successful for run in group
        }
        matched += all(len(group) == baseline["repeats"] for group in successful) and len(traces) == 1

        summaries = [[run["summary"] for run in group] for group in successful]
        work = [[value_at(rows, key, max if key in ("peak_aux_vars", "peak_clauses") else median)
                 for key in WORKLOAD] for rows in summaries]
        metrics = [[value_at(rows, key) for key in METRICS] for rows in summaries]
        memory = [
            value_at([run["summary"] for run in group if run["summary"]["memory_status"] == "SOLVED"],
                     "peak_python_bytes")
            for group in run_groups
        ]
        memory = [value / 1024 if value is not None else None for value in memory]
        if path == "data/puzzles/5x5/level_02.json":
            macros["TimeExampleBase"], macros["TimeExampleJW"] = (
                format_number(group[-1], 2) for group in metrics
            )
        if path == "data/puzzles/5x5/level_01.json":
            macros["MemoryExampleBase"], macros["MemoryExampleJW"] = (
                format_number(value, 1) for value in memory
            )

        if path == stress:
            stress_metrics = [
                (*workload_values, *metric_values, mem_value)
                for workload_values, metric_values, mem_value in zip(work, metrics, memory)
            ]
            names = (
                "Biến chính", "Biến phụ (đỉnh)", "Mệnh đề CNF (đỉnh)", "Lượt gọi SAT", "Bước lật",
                "Quyết định", "Lan truyền", "Quay lui", "Thời gian DPLL (ms)",
                "Thời gian toàn lượt (ms)", "Đỉnh cấp phát Python (KiB)",
            )
            macros["StressLabel"] = label
            macros["StressSeed"] = str(seed)
            macros["StressTimeBase"], macros["StressTimeJW"] = (
                format_number(group[-1], 2) for group in metrics
            )
            macros["StressDecisionBase"], macros["StressDecisionJW"] = (
                format_number(group[0]) for group in metrics
            )
            macros["StressMemoryBase"], macros["StressMemoryJW"] = (
                format_number(value, 1) for value in memory
            )
            base, jw = metrics
            have_results = all(value is not None for value in (base[0], jw[0], base[-1], jw[-1], *memory))
            macros["StressTradeoff"] = str(int(have_results and jw[0] < base[0]
                                                and jw[-1] > base[-1] and memory[1] > memory[0]))
            macros["StressRows"] = "\n".join(
                make_row([name, format_number(a, 2 if i >= 8 else 0),
                          format_number(b, 2 if i >= 8 else 0)])
                for i, (name, a, b) in enumerate(zip(names, *stress_metrics, strict=True))
            )
            continue

        if last_size is not None and last_size != size:
            for rows in (workload, times, memory_rows, workload_counts):
                rows.append(r"\addlinespace[2pt]")
        last_size = size
        labels.append("{" + label + "}")
        row_index = len(labels)
        workload.append(make_row([label, seed, *map(format_number, work[0])]))
        times.append(make_row([label, *(format_number(value, 2) for group in metrics for value in group[3:])]))
        memory_rows.append(make_row([label, *(format_number(value, 1) for value in memory)]))
        workload_counts.append(make_row([label, *(format_number(value) for group in metrics for value in group[:3])]))
        base_time, new_time = (group[-1] for group in metrics)
        if base_time and new_time and base_time > 0 and new_time > 0:
            scatter_groups[size].append((base_time, new_time))
            time_pairs += 1
            main_faster += new_time < base_time
        if all(value is not None for value in memory):
            memory_pairs += 1
            main_lower_memory += memory[1] < memory[0]
        for j, (mem, counters) in enumerate(zip(memory, metrics)):
            if mem is not None:
                memory_points[j].append((mem, row_index))
            if counters[0] is not None:
                decision_points[j].append((counters[0], row_index))

    for label, report in zip(("Smallest", "JW"), reports):
        summaries = [run["summary"] for run in report["runs"]]
        for is_stress, group_name in ((False, "Nhóm chính"), (True, macros["StressLabel"])):
            group = [r for r in summaries if (r["stage"] == stress) == is_stress]
            for key, phase in (("status", "Thời gian"), ("memory_status", "Bộ nhớ")):
                counts = Counter(row[key] for row in group)
                solved, stalled, timeouts = (counts[s] for s in ("SOLVED", "STALLED", "TIMEOUT"))
                statuses.append(make_row([
                    group_name, rf"\texttt{{{report['heuristic']}}}", phase, solved, stalled, timeouts,
                    len(group) - solved - stalled - timeouts,
                ]))
        macros["Solved" + label] = str(sum(r["status"] == "SOLVED" for r in summaries))
        macros["Total" + label] = str(len(summaries))
        macros["Snapshots" + label] = str(sum(v.get("checked_steps", 0) for v in report["validation"].values()))
        macros["Validated" + label] = str(sum(
            not v.get("error") and v.get("false_clues") == []
            and v.get("uniqueness") == "UNIQUE" and v.get("model_matches")
            and v.get("progressive_status") == "SOLVED"
            for v in report["validation"].values()
        ))

    repeat = baseline["repeats"]
    macros.update(
        StageCount=str(len(stages)), MainStageCount=str(len(labels)), MatchedStages=str(matched),
        RepeatCount=str(repeat), Timeout=format_number(baseline["timeout_seconds_per_call"]),
        ProcessTimeout=format_number(baseline["process_timeout_seconds"]),
        MainRunCount=str(len(labels) * repeat * len(reports)),
        StressRunCount=str(repeat * len(reports)),
        Commit=tex_escape(baseline["source_commit"][:7]), UTC=tex_escape(baseline["started_utc"]),
        Platform=tex_escape(baseline["platform"]), CPU=tex_escape(baseline["cpu"]),
        Python=tex_escape(baseline["python"]), WorkloadRows="\n".join(workload),
        RuntimeRows="\n".join(times), MemoryRows="\n".join(memory_rows),
        CountRows="\n".join(workload_counts), StatusRows="\n".join(statuses),
        ScatterPlot=scatter_plot(scatter_groups), TimePairs=str(time_pairs), TimeJWFaster=str(main_faster),
        MemoryPlot=series_plot(memory_points), MemoryPairs=str(memory_pairs),
        MemoryJWLower=str(main_lower_memory), DecisionPlot=series_plot(decision_points),
    )
    content = "% Generated by report/experiments/render_report_data.py from results/benchmark/.\n"
    for name, value in macros.items():
        content += f"\\newcommand{{\\Exp{name}}}{{%\n{value}%\n}}\n"
    ticks = ",".join(map(str, range(1, len(labels) + 1)))
    content += (r"\pgfplotsset{experiment levels/.style={" + "\n"
                f"    ytick={{{ticks}}},\n    yticklabels={{{','.join(labels)}}}\n"
                "}}\n")
    if destination.exists() and destination.read_text(encoding="utf-8") == content:
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile("w", encoding="utf-8", newline="\n",
                            dir=destination.parent, delete=False) as stream:
        stream.write(content)
    Path(stream.name).replace(destination)
    print(f"Generated {destination}")


if __name__ == "__main__":
    make_data(ROOT / "results" / "benchmark", ROOT / "report" / "generated" / "experiment-data.tex")
