# Griductive implementation plan

## Goal and scope

Build a playable Pygame grid-deduction game with a no-guess logic agent. Encode
structured clues automatically as CNF, implement DPLL ourselves, and accept a
verdict only when it follows from currently public information. A successful
verdict reveals the character's clue and enables the next deduction.

Requirements source: [AI - Project 2.pdf](AI%20-%20Project%202.pdf), particularly
sections 2-3 and 4.1-4.5 (pages 5-7). Gameplay reference:
[Griductive](https://knotwise.games/games/griductive). The assignment defines the
required implementation scope. Daily online puzzles, accounts, and subscriptions
are outside this project. Person 1's engine and GUI are implemented. A temporary semantic analyzer makes
the game playable; the assessed CNF/DPLL agent and experiment suite remain pending.
See [the integration guide](docs/INTEGRATION.md) for the implemented contracts.

## Five-person ownership

Replace the placeholders with names/student IDs before starting. Each owner writes
tests and a report contribution for their area; completion starts at 0% and must
be updated from actual contributions, not estimated from assigned points.

| Owner | PDF requirement | Main directories | Reviewer | Completion |
| --- | --- | --- | --- | --- |
| Person 1 | 4.1 Reimplement the Game (10 pts) | `engine/`, `ui/`, `app.py`, assets | Person 4 | Implemented; team review pending |
| Person 2 | 4.2 Automatic Logical Representation and CNF Encoding (10 pts) | `domain/`, `logic/` | Person 3 | 0% |
| Person 3 | 4.3 DPLL SAT Solver (10 pts) | `sat/` | Person 2 | 0% |
| Person 4 | 4.4 Deductive Logic Agent (20 pts) | `agent/` | Person 1 | 0% |
| Person 5 | 4.5 Experiments (10 pts) | `experiments/`, puzzle data, integration tests, results | Person 4 | 0% |

Paths above are relative to `griductive/` for Python packages. Person 5 also
coordinates integration and report assembly; Persons 2 and 3 support Person 4's
larger workload through entailment fixtures and SAT-query debugging.

## Agree on shared interfaces first

The public models, puzzle loader, engine, and `Analyzer.analyze(PublicState)`
boundary now exist; see `docs/INTEGRATION.md`. The encoder and SAT APIs below
remain proposals for Persons 2-4. Review shared types before changing them.

- [ ] Persons 1, 2, 4: define `Character`, `Clue`, `Puzzle`, `PublicState`, status
  enums, and immutable/public snapshots in `domain/`. Fix coordinate conversion
  (A1 is top-left), row-major cell ordering, and alphabetical display-name ordering.
- [ ] Persons 1, 2, 5: define and document the puzzle JSON schema: size, stable cell
  IDs, names, professions, hidden statuses, one structured clue per card, and initial
  face-up cells. The loader validates these and exposes only public data to the agent.
- [ ] Person 2: `encode(public_state) -> CNF` with integer literals, deterministic
  primary variable IDs, separate auxiliary IDs, and variable/clause statistics.
- [ ] Person 3: `solve(cnf, assumptions=()) -> SatResult` containing SAT/UNSAT,
  a complete model when SAT, and decisions/propagations/backtracks/runtime.
  Calls must not mutate their input or retain temporary assumptions.
- [ ] Person 4: `classify(public_state)` checks consistency first, then classifies
  unresolved cells; `next_move(public_state)` picks the first forced row-major cell.
- [ ] Persons 1, 4: `submit_verdict(cell_id, status)` checks entailment, accepts and
  reveals through the engine, or returns NOT_PROVABLE/CONTRADICTED unchanged.
  Define an INCONSISTENT result that stops play without revealing anything.
- [ ] Persons 4, 5: define trace/metrics records and a separate offline full-puzzle
  validation API. Hidden data must never enter live hint or deduction calls.

## Person 1 - 4.1 Reimplement the Game

- [x] Implement validated JSON loading, initial reveals, restart, and engine-owned
  hidden solution/clues; keep the agent's input limited to public knowledge.
- [x] Render 3x3 and 4x4 grids (allow 5x5), coordinates, names, professions,
  face-down cards, known statuses, and readable revealed clues.
- [x] Add selection and CRIMINAL/INNOCENT actions; accepted verdicts mark status,
  flip the card, and reveal its clue. All revealed clues are true regardless of owner status.
- [x] Distinguish NOT_PROVABLE from CONTRADICTED; rejection must not change the
  board or expose hidden clue text.
- [x] Selecting a revealed clue highlights all referenced/counted cells.
- [x] Add Load, Restart, Hint, and Auto Solve controls; show solved, stalled,
  inconsistent, and error states. Keep the event loop responsive during solving.
- [x] Test reveal transitions, unchanged state on rejection, restart, and no hidden
  information in public snapshots; verify rendering and controls through offscreen Pygame event tests.

Acceptance: a user can load and play a puzzle using only proved verdicts, obtain
a valid hint, and watch Auto Solve reveal clues progressively.

- [ ] Review on team desktops and integrate the final CNF/DPLL agent with Person 4.
- [ ] Record the final demo after the remaining team work is complete.

## Person 2 - 4.2 Automatic Logical Representation and CNF Encoding

- [ ] Define deterministic primary variables: true = criminal, false = innocent.
- [ ] Implement rows, columns, explicit distinct cell lists, and neighbors including
  diagonals but excluding the center. Validate IDs, regions, and integer count bounds.
- [ ] Encode FACT, SAME, DIFFERENT, EXACTLY, AT_LEAST, and AT_MOST automatically;
  support NO as EXACTLY(0). Never hand-write puzzle-specific CNF.
- [ ] Add proved verdicts as units; include only revealed clues in the live KB.
- [ ] Implement independent direct semantic evaluators for all six clue templates.
- [ ] Implement two planned extensions: EVEN/ODD parity as one extension family,
  and intersection of regions as a second distinct extension. Document syntax,
  semantics, CNF conversion, and GUI highlighting with Persons 1 and 5.
- [ ] Report primary/auxiliary variable counts and clause counts. Document a binary
  clue derivation and a counting-clue derivation for the report.
- [ ] Exhaustively compare semantic evaluation with CNF satisfiability on small
  assignments (fix primary variables, existentially solve auxiliary variables).
  Cover empty regions, k=0, k=region size, invalid parameters, and both extensions.

Acceptance: arbitrary supported structured clues become correct CNF, with no
hidden facts included and reproducible variable IDs and statistics.

## Person 3 - 4.3 DPLL SAT Solver

- [ ] Implement unit propagation and conflict detection, including empty clauses.
- [ ] Implement deterministic variable selection, recursive branching, and backtracking.
- [ ] Return SAT with a complete assignment over declared variables, or UNSAT;
  handle an empty formula and unconstrained variables correctly.
- [ ] Support temporary assumptions or copied unit clauses without changing the KB.
- [ ] Record decisions, propagations, backtracks, and elapsed runtime; document what
  each counter measures and reset per call.
- [ ] Test satisfiable/unsatisfiable formulas, propagation chains, branching,
  backtracking, contradictory assumptions, and repeated independent calls.
- [ ] Cross-check small formulas against a simple exhaustive truth-table oracle.
- [ ] Optional after correctness: add pure-literal elimination or a second branching
  heuristic for controlled benchmark comparisons.

Acceptance: the main SAT algorithm is implemented by the team, passes the oracle
comparison, and supplies complete models and reliable counters to the agent.

## Person 4 - 4.4 Deductive Logic Agent

- [ ] Check SAT(KB) first; UNSAT means INCONSISTENT, not a forced verdict.
- [ ] For each unresolved character Ci, query KB AND NOT Ci and KB AND Ci:
  the first UNSAT forces CRIMINAL, the second UNSAT forces INNOCENT,
  and both SAT means UNKNOWN. One satisfying model is not proof.
- [ ] Choose forced verdicts deterministically; never guess when all are UNKNOWN.
- [ ] Submit each move to the engine; after acceptance receive the newly revealed
  clue, rebuild/update the public KB, and continue.
- [ ] Stop explicitly on solved, stalled/ambiguous public state, or inconsistency.
  A stalled public state is not by itself proof that the complete puzzle is nonunique.
- [ ] Provide Hint from public entailment only; identify a forced character and/or
  a relevant revealed clue without inspecting hidden labels.
- [ ] Record each step, active clue IDs, SAT queries/results, verdict, and newly
  revealed clue; expose the trace to UI and experiments.
- [ ] Implement a separate full-clue uniqueness check: find a model, block only
  its primary-variable assignment, and solve again. Distinguish zero, one, and
  multiple solutions; auxiliary assignments must not count as different puzzles.
- [ ] Test forced/unknown/inconsistent cases, deterministic order, progressive
  reveals, no-guess behavior, and independence from hidden information.

Acceptance: Auto Solve and Hint use only public information and every accepted
step has a reproducible entailment query in the trace.

## Person 5 - 4.5 Experiments

- [ ] Create several reproducible 3x3 and 4x4 fixtures spanning all core clue types,
  required regions, and both extensions; optionally include a 5x5 stress case.
- [ ] Validate complete-clue uniqueness and agreement with the stored solution.
  Separately check that intended playable fixtures finish through progressive reveals.
- [ ] Add deliberately ambiguous and inconsistent fixtures, malformed inputs, and
  a uniquely solvable complete puzzle whose initial public clues cannot advance.
- [ ] Build a headless benchmark runner and CSV/JSON exports in `results/`.
- [ ] Record primary variables, auxiliary variables, clauses, SAT calls, decisions,
  propagations, backtracks, deduction steps/reveal waves, and runtime per case.
  Define whether growing-KB counts are final/peak; distinguish per-call and total metrics.
- [ ] Use the same puzzle set and environment for comparisons; start with baseline
  DPLL across board sizes and compare optional heuristics only if implemented.
- [ ] Fix seeds/order, document hardware/software and timeout limits, repeat timed
  runs consistently, and retain failures/timeouts in result tables.
- [ ] Coordinate end-to-end checks: load -> public KB -> CNF -> DPLL -> entailed
  verdict -> reveal -> completion; summarize findings and limitations for the report.

Acceptance: one documented command reproduces the experiment tables, including
failures, with all six required metric categories and consistent comparisons.

## Integration milestones (approximately three weeks)

1. **Week 1:** agree contracts/schema; create small fixtures; implement engine and
   GUI shell, core encoder, baseline DPLL, and agent/query test doubles.
2. **Week 2:** integrate manual verdict validation, progressive deduction, hints,
   Auto Solve, clue highlighting, extensions, and boundary-case tests.
3. **Week 3:** freeze benchmark fixtures, run experiments, fix integration issues,
   finish report/video, and verify a clean installation and submission archive.

Dependencies: shared contracts first; Person 4 integrates Persons 2 and 3;
Person 1 connects verdicts/hints to Person 4; Person 5 supplies fixtures early
and runs final measurements after the complete reveal loop works.

## Shared submission work beyond the five main work areas

- [ ] Section 4.6 (30 pts): each owner writes their methods/results and actual
  contribution percentage; Person 5 assembles the report and all five review it.
  Include formulation, clue semantics, reveal protocol, CNF derivations, algorithms,
  experiments, limitations, references, and an appendix documenting AI usage/prompts.
- [ ] Section 4.7 (10 pts): Person 1 coordinates a 5-10 minute narrated/subtitled
  English or Vietnamese demo of manual play and solving; others demonstrate their
  features. Upload to Google Drive, include its link in the report, and verify
  anyone-with-link viewing in a private browser. Do not use YouTube.
- [ ] All: add final run/benchmark instructions; run the test suite and verify a
  clean setup without relying on local caches or an existing virtual environment.
- [ ] All: package `Source/` and `Report.pdf` in the required student-ID-named
  archive; omit environments/caches, follow the >20 MB Drive rule if needed, and
  verify the actual course deadline before submission.
