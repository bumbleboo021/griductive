🌐 **Language:** [English](TODO.md) | [Tiếng Việt](TODO_vi.md)

# Griductive team handoff and remaining work

This checklist reflects the current repository. Replace Person 1-5 with names and
student IDs. Checked items describe implemented work. Unchecked items describe
remaining implementation or team review. Record actual contributions separately
when preparing the report.

Requirements are in [AI - Project 2.pdf](AI%20-%20Project%202.pdf), sections 4.1-4.7.
Use [README.md](README.md) to install, run and check the project.

## Current ownership

| Owner | Assignment area | Existing work to reuse | Next deliverable |
| --- | --- | --- | --- |
| Person 1 | 4.1 Game and GUI, 10 pts | Engine, Pygame UI, assets, public-state boundary, stage picker, controls and animations | Review the final agent integration and record the GUI demonstration |
| Person 2 | 4.2 Representation and CNF, 10 pts | Frozen Clue/PublicState models, loader, regions and semantic examples | Automatic encoder with core and extended clue coverage |
| Person 3 | 4.3 DPLL, 10 pts | Public integration contract and semantic oracles for comparison | Custom DPLL with complete models, assumptions and metrics |
| Person 4 | 4.4 Deduction agent, 20 pts | GameEngine lifecycle, Analyzer protocol and plugin CLI | DPLL-backed adapter, deduction trace and uniqueness API |
| Person 5 | 4.5 Experiments, 10 pts | Thirteen validated stages, negative tests, offline validator and traces | Reproducible benchmark runner and report tables |

`logic/`, `sat/`, `agent/`, and `experiments/` under `griductive/` currently contain
package placeholders. The default game uses `engine/reference.py` and
`engine/advanced_clues.py` for semantic backtracking. The assessed CNF/DPLL path
and its measurements remain to be implemented.

## Begin here

- [ ] All members run the setup and four baseline commands in README.md.
- [ ] Read `domain/models.py`, `engine/puzzle.py`, and `engine/game.py` before
  changing interfaces. Review [docs/INTEGRATION.md](docs/INTEGRATION.md).
- [ ] Persons 2-4 agree the internal CNF and SAT-result types, assumption handling,
  declared variable counts, metrics fields, and timeout representation.
- [ ] Persons 2-4 implement the six core clue templates and QUOTE handling first,
  connect the adapter, and pass the existing public-state checker.
- [ ] Add parity, comparisons, connectivity and implication support, then run the
  adapter against all stages. Levels 03 and above exercise the richer templates.
- [ ] Person 5 select and freeze the experiment manifest with stage paths and seeds.
- [ ] All members update this checklist as deliverables are reviewed.

Proposed internal APIs are `encode(public_state) -> CNF` and
`solve(cnf, assumptions=()) -> SatResult`. Persons 2-4 should settle their concrete
return fields together. The implemented external boundary is
`analyze(PublicState) -> Analysis` and must stay compatible with GameEngine.

## Person 1 - game and interface

### Implemented

- [x] Private puzzle storage, structural loading, initial reveals and Restart.
- [x] Immutable public snapshots containing revealed clues and proved statuses.
- [x] Criminal/Innocent popup on unresolved cards and distinct rejection notifications.
- [x] Accepted verdicts reveal cards and their clues progressively.
- [x] Stage picker using JSON `name`, plus legacy `title` compatibility.
- [x] Hint, Auto Solve, Stop, help panel, music toggle and track selector.
- [x] Background, local fonts, portrait fitting, origin labels and random casts.
- [x] Hover/selection feedback, automatic-move highlighting and reveal animations.
- [x] Bordered clue panel with smooth scrolling and referenced-cell highlighting.
- [x] Engine and offscreen UI tests, including unchanged state after rejected choices.
- [x] Integration guide, UI guide and AI-assistance appendix.

### Remaining

- [ ] Review manual verdicts, Hint, Auto Solve, Restart and stage switching with
  Person 4's final adapter, including error and timeout behavior.
- [ ] Check rendering and audio on teammates' actual desktops.
- [ ] Review shortened card clues against complete side-panel text for final stages.
- [ ] Complete asset attributions and supplied license/permission records.
- [ ] Prepare the GUI portion of the final demonstration after integration.

## Person 2 - logical representation and CNF

### Available foundation

- [x] Shared Status, Character, Clue, PublicState and Analysis dataclasses.
- [x] Deterministic row-major cell order and validated region expansion.
- [x] Semantic support for all stage templates in the development analyzer.
- [x] Exhaustive small-region tests and independent offline semantic checks.
- [x] Assign primary variables from cell IDs, with true meaning criminal.
  Allocate auxiliary variables separately and deterministically.
- [x] Encode FACT, SAME, DIFFERENT, EXACTLY, AT_LEAST and AT_MOST.
- [x] Add public verdicts as unit clauses and encode only public clues.
- [x] Treat QUOTE as an empty contribution to CNF.
- [x] Encode ODD and EVEN over the normalized criminal count.
- [x] Encode COUNT_COMPARE using its actual target status, both regions, and
  strict GT/LT or EQ semantics. Test overlapping regions and cancellation.
- [x] Encode IMPLIES with ordered premise/conclusion cells and their own statuses.
- [x] Encode CONNECTED with four-direction adjacency inside the given region.
  Preserve current empty/singleton semantics and test diagonal-only contact.
- [x] Handle the loader's expanded regions, including intersections, common
  neighbors, direct directions, boundary, whole-grid and fixed named groups.
- [x] Maintain independent semantic evaluators for the encoder's supported clues.
- [x] Report primary variables, auxiliary variables and generated clause counts.
- [x] Compare CNF satisfiability with direct semantics exhaustively on small cases.
  Fix primary assignments and allow auxiliary assignments to vary.
- [x] Cover empty regions, count extremes, innocent-target normalization,
  conditionals, shared regions, connectivity and invalid inputs.

### Remaining implementation

- [ ] Write report derivations for a binary clue, a counting clue, and extensions.

Core cardinality/parity `kind` and `count` already describe criminals after loading.
For example, exactly 1 innocent among 3 cells is stored as EXACTLY 2 criminals.
Use the stored normalized constraint directly. COUNT_COMPARE and CONNECTED use
`target_status` directly. See the schema table in README.md.

Acceptance requires semantic/CNF agreement, reproducible variable allocation,
clause statistics, and successful integration with Persons 3 and 4.

## Person 3 - DPLL SAT solver

- [ ] Implement unit propagation and conflict detection.
- [ ] Implement deterministic variable selection, branching and backtracking.
- [ ] Return SAT with a complete assignment over declared variables, or UNSAT.
- [ ] Handle empty formulas, empty clauses, contradictory units and unconstrained
  variables explicitly.
- [ ] Support temporary assumptions without mutating the persistent KB or leaking
  assumptions between entailment queries.
- [ ] Record decisions, propagations, backtracks and runtime per call.
  Document counter definitions and how totals are aggregated.
- [ ] Represent timeout separately from SAT and UNSAT.
- [ ] Compare small formulas with a truth-table oracle and test repeated calls.
- [ ] Work with Person 2 to verify formulas containing auxiliary variables.
- [ ] Document DPLL and the selected deterministic branching rule for the report.
- [ ] Optional after correctness, add another heuristic for controlled comparisons.

Acceptance requires complete models, reproducible results, isolated assumptions,
and correct counters through Person 4's entailment calls.

## Person 4 - deductive logic agent

- [x] Implement `griductive/agent/adapter.py` with a no-argument `Agent` factory
  exposing `analyze(state: PublicState) -> Analysis`.
- [x] Call Person 2's encoder and Person 3's DPLL solver.
- [x] Check base KB consistency first. Return `Analysis(False, ())` when UNSAT.
- [x] Classify every unresolved cell in row-major order. UNSAT under NOT Ci
  proves criminal. UNSAT under Ci proves innocent. Both SAT means UNKNOWN.
- [x] Return Status enum members and exactly one result per unresolved cell.
- [ ] Raise an explicit failure for unsupported clues or timeouts.
- [ ] Keep all live queries within the supplied public snapshot. Hidden labels
  and unrevealed clue contents belong to the engine.
- [ ] Handle Restart snapshots correctly if caching knowledge bases or results.
- [x] Pass `python -m griductive.check_analyzer --analyzer griductive.agent.adapter:Agent`.
- [ ] Extend differential checks to new clue types and all levels 03 and above.
- [ ] Run manual verdicts, Hint and Auto Solve through the GUI using the adapter.
- [ ] Record step number, active clue IDs, SAT queries/results, accepted verdict,
  and newly revealed clue. Coordinate the engine/trace boundary with Person 1.
- [ ] Add separate offline full-clue uniqueness checking. Find one model, block
  its primary assignment, and check for another. Exclude auxiliary variables
  from the blocking clause.
- [ ] Test solved, stalled, inconsistent and timeout states, plus hidden-data
  independence. Distinguish stalled public knowledge from complete-clue ambiguity.
- [ ] Document entailment, uniqueness and progressive solving for the report.

The engine already chooses the first forced row-major verdict and reveals the
card. Integrate the analyzer through the existing CLI factory hook. Coordinate
any trace callback or additional agent loop with that existing lifecycle.

Acceptance requires a no-guess solve of all supported stages using the team's
CNF/DPLL path and a reproducible trace of the public reveal sequence.

## Person 5 - experiments and stage review

### Available foundation

- [x] Thirteen original stages with names and seeds, comprising 4 for 3x3,
  4 for 4x4, and 5 for 5x5.
- [x] Offline clue-truth, full-clue uniqueness and progressive-solving validator.
- [x] Saved semantic validation traces in `docs/level_validation.json`.
- [x] Negative tests for false clues, ambiguity and progressive stalls.
- [x] Reproducible build scripts and redundant-clue pruning to quote cards.

### Remaining experiments

- [ ] Review stage design and human difficulty. Include representative core and
  extended cases in a fixed manifest with paths, seeds and version information.
- [ ] Rerun truth, uniqueness and progressive validation with the team's agent.
- [ ] Add a headless benchmark runner under `griductive/experiments/` that exports
  CSV/JSON to `results/` and documents one reproduction command.
- [ ] Record primary/auxiliary variables, clauses, SAT calls, decisions,
  propagations, backtracks, reveal steps/waves and runtime.
- [ ] Specify final or peak variable/clause counts as the KB grows. Distinguish
  per-SAT-call statistics from per-stage totals.
- [ ] Define run count, seeds, timeout limit and environment details. Retain
  failures and timeouts in output tables.
- [ ] Use the same stage manifest for every comparison. Compare optional solver
  heuristics only after the baseline is correct.
- [ ] Review randomized display casts and the fixed-cast origin-group stage.
  Use saved JSON data for reproducible headless experiments.
- [ ] Produce tables/charts, observations, failure analysis and limitations.
- [ ] Coordinate final integration checks and report assembly.

The semantic validator provides a development baseline. Benchmark counters and
results must come from the team's measured CNF/DPLL implementation.

## Integration checkpoints

1. Persons 2-4 agree CNF/SAT return types, variable numbering and metrics.
2. Encode and solve a small public KB, then connect the adapter and pass core checks.
3. Support every template used by levels 03 and above and validate all 13 stages.
4. Persons 1 and 4 exercise the complete GUI reveal loop, errors and Restart.
5. Person 5 freezes inputs, runs reproducible experiments and prepares report output.
6. All members review the report, appendix, credits, demo and submission archive.

## Shared report and submission work

- [ ] Section 4.6, 30 pts. Each member writes their methods and results and records
  actual completion/contribution percentages. Person 5 assembles the report.
- [ ] Include variables, clue semantics, public KB, reveal protocol, CNF examples,
  DPLL, entailment, uniqueness, experiments, limitations and references.
- [ ] Review [appendix.md](appendix.md) and add subsequent AI usage and prompts.
- [ ] Complete [assets/ATTRIBUTION.md](assets/ATTRIBUTION.md), add the source terms
  under `assets/licenses/`, and retain `assets/images/NOTICE.txt`.
- [ ] Section 4.7, 10 pts. Prepare a 5-10 minute demo showing manual play and
  solving, with English or Vietnamese narration/subtitles. Add the Google Drive
  link to the report and verify anyone-with-link viewing in a private browser.
- [ ] Verify a clean installation and current run/test/experiment instructions.
- [ ] Package `Source/` and `Report.pdf` in the student-ID-named archive required
  by the assignment. Omit virtual environments and caches. Follow its Drive
  submission rule for archives above 20 MB and verify the course deadline.
