"""Reproduce the Griductive progressive-solving experiment."""
import argparse
import csv
import hashlib
import json
import math
import platform
from pathlib import Path
from statistics import fmean
from time import perf_counter

from griductive.agent.adapter import Agent
from griductive.agent.uniqueness import check_uniqueness
from griductive.domain.models import Status
from griductive.engine.game import GameEngine
from griductive.engine.puzzle import load_puzzle
from griductive.engine.reference import ReferenceAnalyzer
from scripts.validate_levels import compatible

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = Path(__file__).with_name("manifest.json")
COUNTERS = ("decisions", "propagations", "backtracks")


def load_stage(entry):
    path = ROOT / entry["path"]
    data = path.read_bytes().replace(b"\r\n", b"\n")
    if hashlib.sha256(data).hexdigest() != entry["sha256"]:
        raise ValueError(f"Stage differs from manifest: {path.name}")
    raw = json.loads(data)
    if (raw["size"], raw["metadata"]["seed"]) != (entry["size"], entry["seed"]):
        raise ValueError("Size or seed differs from manifest")
    return load_puzzle(path)


def validate(puzzle, timeout):
    solution = dict(puzzle.solution)
    truth = {cell: status == Status.CRIMINAL for cell, status in solution.items()}
    false_clues = [c.id for c in puzzle.clues if not compatible(c, truth)]
    unique = check_uniqueness(puzzle, timeout_seconds=timeout, strict_dpll=True)
    agent = Agent(timeout_seconds=timeout, strict_dpll=True)
    engine = GameEngine(puzzle, agent)
    oracle = ReferenceAnalyzer(timeout=timeout)
    checks = 0
    error = ""
    try:
        while not engine.solved:
            before = engine.public_state()
            expected = oracle.analyze(before)
            actual = agent.analyze(before)
            if actual != expected:
                raise ValueError(f"Expected {expected}, got {actual}")
            forced = next(((c, s) for c, s in expected.verdicts if s != Status.UNKNOWN), None)
            outcome = engine.step()
            if forced is None or outcome.code not in ("ACCEPTED", "SOLVED"):
                raise ValueError(f"Unexpected outcome {outcome}")
            cell, status = forced
            after = engine.public_state()
            owners = {char.cell: clue for char, clue in zip(puzzle.characters, puzzle.clues)}
            if (outcome.cell != cell or dict(after.verdicts) != dict(before.verdicts) | {cell: status}
                    or set(after.clues) != set(before.clues) | {owners[cell]}):
                raise ValueError(f"Incorrect reveal for {cell}")
            checks += 1
    except Exception as exc:
        error = f"Step {checks + 1}: {type(exc).__name__}: {exc}"
    return dict(false_clues=false_clues, uniqueness=unique.status.value,
                model_matches=unique.first_model == solution, checked_steps=checks,
                progressive_status="SOLVED" if engine.solved and not error else "FAILED", error=error)


def measure(puzzle, timeout):
    calls = []
    steps = []

    def record(result):
        calls.append(dict(decisions=result.decisions, propagations=result.propagations,
                          backtracks=result.backtracks, runtime_ms=result.runtime * 1000,
                          outcome="TIMEOUT" if result.is_timeout else "SAT" if result.is_sat else "UNSAT"))

    agent = Agent(timeout_seconds=timeout, strict_dpll=True, on_sat_result=record)
    engine = GameEngine(puzzle, agent)
    status, error = "SOLVED", ""
    started = perf_counter()
    while not engine.solved:
        first = len(calls)
        cell = None
        try:
            outcome = engine.step()
            status, cell = outcome.code, outcome.cell
            if status not in ("ACCEPTED", "SOLVED"):
                error = outcome.message
        except Exception as exc:
            status = "TIMEOUT" if isinstance(exc, TimeoutError) else "ERROR"
            error = f"{type(exc).__name__}: {exc}"
        steps.append(dict(cell=cell, status=status, cnf=agent.last_cnf_counts,
                          sat_calls=agent.last_sat_calls, calls=calls[first:]))
        if status != "ACCEPTED":
            break
    elapsed = (perf_counter() - started) * 1000
    counts = [s["cnf"] for s in steps if s["cnf"] is not None]
    summary = dict(status=status, error=error, primary_vars=puzzle.size**2,
                   peak_aux_vars=max((c[1] for c in counts), default=None),
                   peak_clauses=max((c[2] for c in counts), default=None),
                   total_sat_calls=sum(s["sat_calls"] for s in steps),
                   completed_sat_results=len(calls),
                   reveal_steps=sum(s["status"] in ("ACCEPTED", "SOLVED") for s in steps),
                   elapsed_ms=elapsed)
    for key in (*COUNTERS, "runtime_ms"):
        values = [c[key] for c in calls]
        summary["solver_ms" if key == "runtime_ms" else "total_" + key] = sum(values)
        summary["mean_call_" + key] = fmean(values) if values else None
        summary["max_call_" + key] = max(values, default=None)
    return summary, steps


def run(repeats, timeout, output):
    manifest = json.loads(MANIFEST.read_text())
    report = dict(manifest=manifest, python=platform.python_version(), platform=platform.platform(),
                  heuristic="smallest", repeats=repeats, timeout_seconds_per_call=timeout,
                  validation={}, runs=[])
    rows = []
    for entry in manifest["stages"]:
        path = entry["path"]
        puzzle = None
        try:
            puzzle = load_stage(entry)
            validation = validate(puzzle, timeout)
        except Exception as exc:
            validation = dict(error=f"{type(exc).__name__}: {exc}")
        report["validation"][path] = validation
        for rep in range(1, repeats + 1):
            if puzzle is None:
                summary, steps = dict(status="ERROR", error=validation["error"]), []
            else:
                summary, steps = measure(puzzle, timeout)
            row = dict(stage=path, size=entry["size"], seed=entry["seed"], run=rep, **summary)
            rows.append(row)
            report["runs"].append(dict(summary=row, steps=steps))
        print(path, rows[-1]["status"], validation.get("error", ""), flush=True)
    output.mkdir(parents=True, exist_ok=True)
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with (output / "benchmark.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    (output / "benchmark.json").write_text(json.dumps(report, ensure_ascii=False), encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--timeout", type=float, default=3.0)
    parser.add_argument("--output", type=Path, default=ROOT / "results")
    args = parser.parse_args()
    if args.runs < 1 or not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error("runs and timeout must be positive and finite")
    report = run(args.runs, args.timeout, args.output)
    failed = any(r["summary"]["status"] != "SOLVED" for r in report["runs"])
    invalid = any(v.get("error") or v["false_clues"] or not v["model_matches"]
                  or v["uniqueness"] != "UNIQUE" for v in report["validation"].values())
    return int(failed or invalid)


if __name__ == "__main__":
    raise SystemExit(main())
