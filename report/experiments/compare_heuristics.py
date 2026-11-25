"""Measure both DPLL strategies with separate processes for runtime and memory."""

import argparse
import csv
import json
import platform
import subprocess
import sys
import tracemalloc
from datetime import datetime, timezone
from functools import partial
from pathlib import Path
from unittest.mock import patch

STRATEGIES = ("smallest", "jw")
REPEATS = 10
SAT_TIMEOUT = 3.0
PROCESS_TIMEOUT = 30.0
STRESS_STAGE = "data/puzzles/5x5/level_04.json"


def cpu_name():
    cpuinfo = Path("/proc/cpuinfo")
    if cpuinfo.is_file():
        for line in cpuinfo.read_text(encoding="utf-8").splitlines():
            name, _, value = line.partition(":")
            if name.strip() == "model name":
                return value.strip()
    return platform.processor() or platform.machine()


def load_backend(checkout):
    sys.path.insert(0, str(checkout))
    from griductive.experiments import benchmark
    from griductive.sat import dpll
    return benchmark, dpll


def measure_memory(engine):
    status, error, reveals = "SOLVED", "", 0
    tracemalloc.start()
    try:
        while not engine.solved:
            outcome = engine.step()
            status, error = outcome.code, outcome.message
            if status in ("ACCEPTED", "SOLVED"):
                reveals += 1
                error = ""
            if status != "ACCEPTED":
                break
    except Exception as exc:
        status = "TIMEOUT" if isinstance(exc, TimeoutError) else "ERROR"
        error = f"{type(exc).__name__}: {exc}"
    finally:
        peak = tracemalloc.get_traced_memory()[1]
        tracemalloc.stop()
    return dict(status=status, error=error, reveal_steps=reveals, peak_python_bytes=peak)


def worker(checkout, stage_path, heuristic, phase):
    benchmark, dpll = load_backend(checkout)
    puzzle = benchmark.load_puzzle(Path(checkout) / stage_path)
    with patch.object(dpll, "solve", partial(dpll.solve, heuristic=heuristic)):
        if phase == "time":
            summary, steps = benchmark.measure(puzzle, SAT_TIMEOUT)
            payload = dict(summary=summary, steps=steps)
        else:
            agent = benchmark.Agent(timeout_seconds=SAT_TIMEOUT, strict_dpll=True)
            payload = measure_memory(benchmark.GameEngine(puzzle, agent))
    print(json.dumps(payload, ensure_ascii=True))


def run_process(checkout, stage_path, heuristic, phase):
    command = [sys.executable, str(Path(__file__).resolve()), "--worker", str(checkout),
               stage_path, heuristic, phase]
    try:
        process = subprocess.run(command, capture_output=True, text=True,
                                 encoding="utf-8", timeout=PROCESS_TIMEOUT)
        if process.returncode == 0:
            return json.loads(process.stdout)
        error = process.stderr.strip() or f"Worker exited with code {process.returncode}"
    except subprocess.TimeoutExpired:
        return dict(status="TIMEOUT", error=f"{phase} worker exceeded {PROCESS_TIMEOUT:g} s")
    except ValueError as exc:
        error = f"Invalid worker output: {exc}"
    return dict(status="ERROR", error=error)


def write_report(directory, report):
    directory.mkdir(parents=True, exist_ok=True)
    rows = [run["summary"] for run in report["runs"]]
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with (directory / "benchmark.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    (directory / "benchmark.json").write_text(json.dumps(report, ensure_ascii=False), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkout", type=Path, help="Checkout containing the experiment runner")
    parser.add_argument("output", type=Path, help="Results directory for both strategies")
    args = parser.parse_args()
    checkout = args.checkout.resolve()
    commit = subprocess.check_output(
        ["git", "-C", str(checkout), "rev-parse", "HEAD"], text=True
    ).strip()
    changes = subprocess.check_output(
        ["git", "-C", str(checkout), "status", "--porcelain"], text=True
    )
    if changes:
        parser.error("The benchmark checkout must be clean so the commit identifies the measured code")

    benchmark, dpll = load_backend(checkout)
    manifest = json.loads(benchmark.MANIFEST.read_text(encoding="utf-8"))
    if STRESS_STAGE not in {entry["path"] for entry in manifest["stages"]}:
        parser.error(f"The benchmark manifest must contain {STRESS_STAGE}")
    metadata = dict(
        source_commit=commit, started_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        cpu=cpu_name(), python=platform.python_version(), platform=platform.platform(),
        repeats=REPEATS, timeout_seconds_per_call=SAT_TIMEOUT, process_timeout_seconds=PROCESS_TIMEOUT,
        stress_stage=STRESS_STAGE, manifest=manifest,
    )
    reports = {
        heuristic: dict(metadata, heuristic=heuristic, validation={}, runs=[])
        for heuristic in STRATEGIES
    }
    failed = False
    for stage in manifest["stages"]:
        stage_path = stage["path"]
        try:
            puzzle = benchmark.load_stage(stage)
            load_error = ""
        except Exception as exc:
            puzzle = None
            load_error = f"{type(exc).__name__}: {exc}"
        for heuristic, report in reports.items():
            try:
                if puzzle is None:
                    validation = dict(error=load_error)
                else:
                    with patch.object(dpll, "solve", partial(dpll.solve, heuristic=heuristic)):
                        validation = benchmark.validate(puzzle, SAT_TIMEOUT)
            except Exception as exc:
                validation = dict(error=f"{type(exc).__name__}: {exc}")
            report["validation"][stage_path] = validation
            failed |= bool(validation.get("error") or validation.get("false_clues")
                           or validation.get("uniqueness") != "UNIQUE"
                           or not validation.get("model_matches"))

        counts = dict.fromkeys(STRATEGIES, 0)
        for rep in range(1, REPEATS + 1):
            order = STRATEGIES if rep % 2 else STRATEGIES[::-1]
            for heuristic in order:
                if puzzle is None:
                    timing = memory = dict(status="ERROR", error=load_error)
                else:
                    timing = run_process(checkout, stage_path, heuristic, "time")
                    memory = run_process(checkout, stage_path, heuristic, "memory")
                summary = timing.get("summary", timing)
                both_solved = summary["status"] == memory["status"] == "SOLVED"
                if both_solved and summary["reveal_steps"] != memory["reveal_steps"]:
                    memory.update(status="ERROR", error="The phases revealed different numbers of cards")
                    both_solved = False
                counts[heuristic] += both_solved
                failed |= not both_solved
                row = dict(stage=stage_path, size=stage["size"], seed=stage["seed"], run=rep,
                           **summary, memory_status=memory["status"], memory_error=memory["error"],
                           peak_python_bytes=memory.get("peak_python_bytes"),
                           memory_reveal_steps=memory.get("reveal_steps"))
                reports[heuristic]["runs"].append(dict(summary=row, steps=timing.get("steps", [])))
        print(f"{stage_path}: {counts} / {REPEATS} complete pairs", flush=True)
    for heuristic, report in reports.items():
        write_report(args.output / heuristic, report)
    return int(failed)


if __name__ == "__main__":
    if sys.argv[1:2] == ["--worker"]:
        worker(*sys.argv[2:])
    else:
        raise SystemExit(main())
