# Start integrating your module

Person 1's engine and Pygame UI are implemented. Local Genshin portraits and fonts
are loaded from `assets/`. Portrait filenames use `Name · Origin · Game.png`;
the second segment is displayed verbatim, including custom labels such as Chef.
The stage files use alphabetical source casts drawn from these assets. New puzzles should
set `name` to the portrait name and `origin` to its label. Legacy `profession`
fields still load, and `Character.origin` aliases that existing model field.
An unmatched character displays an initial placeholder. Font files fall back to
Pygame defaults if missing. Keep `assets/images/NOTICE.txt` with the artwork.
The default analyzer is a temporary semantic backtracking implementation. It is
not the required CNF encoder, DPLL solver, deduction trace, uniqueness checker,
or experiment suite. Those remain the responsibilities of Persons 2-5.

## Run and check

Use Python 3.11+ and install `requirements-dev.txt` into an environment for your OS.
From the repository root:

```text
python main.py
python main.py --puzzle data/puzzles/4x4/level_01.json
python main.py --headless
python -m pytest tests -q
python -m griductive.check_analyzer
```

The Stage picker contains 13 original stages. Development FACT-chain fixtures
are stored under tests/fixtures/ and are excluded from the picker. The default
stage is 3x3/level_01.json. See docs/LEVELS.md for the full catalog.

In the GUI, click an unresolved card and choose Criminal or Innocent in its popup.
Cancel, Escape, or an outside click dismisses it. Select a revealed clue
to highlight its referenced cells. Hint selects a forced character without revealing
it. Auto Solve reveals one card at a time; Stop stops after the current analysis.
Load lists JSON files under `data/puzzles/` and also accepts a typed file path.
Scroll the clue panel or file list for more entries. Escape closes the picker or game.

## Person 4: connect the agent

Create `griductive/agent/adapter.py` with a no-argument factory/class named `Agent`:

```python
from griductive.domain.models import Analysis, PublicState, Status

class Agent:
    def analyze(self, state: PublicState) -> Analysis:
        # Build CNF from state.clues and state.verdicts using Person 2's encoder.
        # Check consistency and entailment with Person 3's DPLL solver.
        # Return Analysis(False, ()) if the public KB is UNSAT.
        # Otherwise classify EVERY unresolved cell in state.characters order.
        # Example shape (not a correct implementation):
        # Analysis(True, (("B1", Status.CRIMINAL), ("C1", Status.UNKNOWN), ...))
        raise NotImplementedError("Connect the team's encoder and DPLL here")
```

```text
python main.py --analyzer griductive.agent.adapter:Agent
python main.py --headless --analyzer griductive.agent.adapter:Agent
python -m griductive.check_analyzer --analyzer griductive.agent.adapter:Agent
```

The checker compares public classifications with the reference analyzer, tests
progressive reveals on 3x3/4x4/5x5 fixtures, and checks unknown, inconsistent,
binary, count, and parity cases. It exits nonzero on failure. It is a smoke check,
not a proof of algorithm correctness or a replacement for your own unit tests.

Return `Status` enum members, not plain strings. Results must use row-major order
and contain every unresolved cell exactly once. Do not classify revealed cells.
Never return a model's labels as entailments. Raise on timeout or unsupported
clues; an incomplete search must not be reported as UNKNOWN or as a forced verdict.

The GUI runs analysis in a single background worker. Calls are serial. Load and
Restart are disabled while it is working. Implement a deadline inside your solver:
a hung plugin keeps game mutations disabled, although drawing and closing still
work. Plugins are trusted Python code, not sandboxed. The data API prevents
accidental hidden-data access; do not read puzzle files inside an analyzer.

## Person 2: consume the public models

### Extended stage schema

The public Clue model now includes the following templates and fields. Update
your independent evaluator and CNF encoder before running levels 03 and above.

| Kind | Fields and meaning |
| --- | --- |
| `COUNT_COMPARE` | Count `target_status` in `cells` versus `other_cells`, with operator `GT`, `LT`, or `EQ`. `other_region_label` provides the second region's display wording. These targets are used directly, without count normalization. |
| `CONNECTED` | Cells with `target_status` inside `cells` must be linked by orthogonal steps entirely within that region. Empty/singleton groups satisfy the constraint. |
| `IMPLIES` | `cells[0]` with `antecedent_status` implies `cells[1]` with `consequent_status`. Cell order is significant. |

Use `clue.referenced_cells` to highlight both comparison regions or both
conditional cells. Core cardinality/parity clues still normalize to criminal
constraints, as described below. Their stored `target_status` preserves wording.
The new comparison and connectivity templates retain their actual target status.

```json
{"id":"compare","type":"COUNT_COMPARE","region":{"type":"neighbors","cell":"B2"},"other_region":{"type":"neighbors","cell":"C2"},"operator":"GT","target_status":"CRIMINAL"}
{"id":"connected","type":"CONNECTED","region":{"type":"row","index":1},"target_status":"INNOCENT"}
{"id":"conditional","type":"IMPLIES","if":{"cell":"A1","status":"CRIMINAL"},"then":{"cell":"B1","status":"INNOCENT"}}
```

Additional regions are `grid`, `boundary`, `corners`, `common_neighbors`
with two distinct `cells`, and `direction` with a reference `cell` plus `direction`
(`above`, `below`, `left`, `right`). Directional references outside the board fail
validation. A `group` region has fixed `cells` and a human-readable `label`.
Use root `fixed_cast: true` when the group's wording depends on the source cast.
The stage with a Liyue-origin count uses this option.

Updated clue support: `QUOTE` is a nonlogical remark with no cells; ignore it
when encoding constraints (equivalently, encode True). `region_label` preserves
human-readable region wording. `target_status` records whether the source clue
counts innocents or criminals, but `kind` and `count` are ALWAYS normalized to
criminal counts by the loader. Do not convert innocent counts a second time.
For example, 1 innocent in a three-cell column becomes EXACTLY 2 criminals.
The UI reconstructs the original wording. New `rows`/`columns` region forms
accept `indices`/`labels` lists and expand their union; intersection remains
available to restrict neighbors to multiple rows. GUI quotes are drawn from
`config.CHARACTER_QUOTES` and are never passed as factual constraints.

`griductive/domain/models.py` defines frozen dataclasses:

| Field | Meaning |
| --- | --- |
| `PublicState.size` | Grid width/height, 3, 4, or 5 |
| `characters` | Tuple of `Character(cell, name, profession)` in row-major order; `origin` aliases profession |
| `verdicts` | Tuple of `(cell, Status)` for revealed cards only |
| `clues` | Tuple of currently revealed `Clue` objects only |
| `Clue.id` | Unique clue identifier |
| `Clue.kind` | FACT/SAME/DIFFERENT/EXACTLY/AT_LEAST/AT_MOST/EVEN/ODD |
| `Clue.cells` | Expanded tuple of unique cell IDs, row-major |
| `Clue.count` | Count for cardinality clues; otherwise None |
| `Clue.status` | Status for FACT; otherwise None |

Regions are expanded by the loader, so the encoder can consume `clue.cells`
directly. This includes intersections. Diagonal neighbors are included; the center
is excluded. Names and professions are display metadata only. Use row-major IDs
for deterministic primary variables. The default reference analyzer does not
implement CNF; write independent semantic evaluators and encoding tests as planned.

## Person 3: connect DPLL through the agent

The GUI never calls DPLL directly. Agree your CNF/result types with Persons 2 and 4,
then expose `solve(cnf, assumptions=())`. The adapter translates SAT results into
`Analysis`. Keep temporary assumptions isolated, check KB consistency first, and
complete SAT models over declared variables. Your decisions/propagations/backtracks
and timing belong in solver results, not in Pygame code.

## Person 5: write fixtures and integration checks

Copy a stage JSON and change its data. File shape:

```json
{
  "title": "My puzzle",
  "size": 3,
  "initially_revealed": ["A1"],
  "characters": [
    {
      "cell": "A1", "name": "Ada", "profession": "Artist",
      "status": "INNOCENT",
      "clue": {"id": "clue-A1", "type": "FACT", "cells": ["B1"], "status": "CRIMINAL"}
    }
  ]
}
```

This abbreviated example needs the other eight characters to become a valid file.
Provide exactly one card per cell, unique names alphabetical in row-major order,
unique clue IDs, and a CRIMINAL/INNOCENT solution for every card. `initially_revealed`
may be empty for negative tests. The loader checks structure, not full-puzzle
uniqueness or solvability; those checks belong to the agent/experiments work.

Clue forms:

```json
{"id":"c1", "type":"SAME", "cells":["A1","B1"]}
{"id":"c2", "type":"DIFFERENT", "cells":["A1","B1"]}
{"id":"c3", "type":"EXACTLY", "count":1, "region":{"type":"row","index":1}}
{"id":"c4", "type":"AT_LEAST", "count":1, "region":{"type":"column","label":"B"}}
{"id":"c5", "type":"AT_MOST", "count":2, "region":{"type":"neighbors","cell":"B2"}}
{"id":"c6", "type":"EVEN", "region":{"type":"cells","cells":["A1","B1"]}}
{"id":"c7", "type":"ODD", "region":{"type":"intersection","regions":[{"type":"row","index":1},{"type":"column","label":"B"}]}}
```

Use EXACTLY with count 0 for NO. Count bounds are 0 through region size.
The engine guards against a proved verdict disagreeing with the stored solution:
it returns ERROR without revealing. This is a data/backend diagnostic, not an
alternative to entailment validation. All clue statements must be true regardless
of their owner's status.

Headless integration API:

```python
from griductive.engine.game import GameEngine
from griductive.engine.puzzle import load_puzzle
from griductive.engine.reference import ReferenceAnalyzer

engine = GameEngine(load_puzzle("data/puzzles/3x3/level_01.json"), ReferenceAnalyzer())
snapshot = engine.public_state()
hint = engine.hint()  # No mutation.
outcome = engine.step()  # One entailed verdict and reveal, or a terminal result.
```

Outcome codes: ACCEPTED, SOLVED, HINT, NOT_PROVABLE, CONTRADICTED,
ALREADY_REVEALED, STALLED, INCONSISTENT, ERROR. Rejected verdicts do not mutate
state. `restart()` restores initial reveals. Each loaded puzzle gets a new analyzer;
an existing analyzer must handle arbitrary snapshots, including restarts.

## Person 1 follow-up at final integration

The GUI has been tested with actual Pygame offscreen rendering and synthetic mouse
events. Run it on your team's desktops to check display scaling and window sizing.
The logical window is 1180x1020 and Pygame scales it to fit the display.
Vertical cards fill the left board area. Long names/origins are clipped to their card;
keep fixture labels short. Clues have a scrollable panel. Portraits are cached by
character name and render size. `ui/assets.py` manages artwork and font loading.
Review the final DPLL-backed flow with Person 4 and record the demonstration video
after the team completes its algorithms and experiments.
