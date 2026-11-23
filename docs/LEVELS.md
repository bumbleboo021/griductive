🌐 **Language:** [English](LEVELS.md) | [Tiếng Việt](LEVELS_vi.md)

# Stage catalog

The game contains 13 original stages. Seven were added in this update and the
three tutorial stages were removed from the playable collection. Development
chain fixtures live under `tests/fixtures/`. The app starts at 3x3 level 01.

| Board | File | Stage name | Initially revealed | Proved moves | Quote cards |
| --- | --- | --- | --- | --- | --- |
| 3x3 | `data/puzzles/3x3/level_01.json` | Stage 1 - 3x3 - Quiet Rows | A1 | 8 | 4 |
| 3x3 | `data/puzzles/3x3/level_02.json` | Stage 2 - 3x3 - Crossed Testimonies | A1 | 8 | 3 |
| 3x3 | `data/puzzles/3x3/level_03.json` | Stage 3 - 3x3 - Lantern Bridge | A1, C1 | 7 | 3 |
| 3x3 | `data/puzzles/3x3/level_04.json` | Stage 4 - 3x3 - Shared Alibis | A1, C1 | 7 | 2 |
| 4x4 | `data/puzzles/4x4/level_01.json` | Stage 5 - 4x4 - Quiet Rows | A1 | 15 | 8 |
| 4x4 | `data/puzzles/4x4/level_02.json` | Stage 6 - 4x4 - Crossed Testimonies | A1 | 15 | 6 |
| 4x4 | `data/puzzles/4x4/level_03.json` | Stage 7 - 4x4 - The Silent Courtyard | A1, D1 | 14 | 4 |
| 4x4 | `data/puzzles/4x4/level_04.json` | Stage 8 - 4x4 - Crossing Paths | A1, D1 | 14 | 5 |
| 5x5 | `data/puzzles/5x5/level_01.json` | Stage 9 - 5x5 - Quiet Rows | A1 | 24 | 14 |
| 5x5 | `data/puzzles/5x5/level_02.json` | Stage 10 - 5x5 - Crossed Testimonies | A1 | 24 | 9 |
| 5x5 | `data/puzzles/5x5/level_03.json` | Stage 11 - 5x5 - Threads of Evidence | A1, E1 | 23 | 10 |
| 5x5 | `data/puzzles/5x5/level_04.json` | Stage 12 - 5x5 - The Boundary Case | A1, E1 | 23 | 10 |
| 5x5 | `data/puzzles/5x5/level_05.json` | Stage 13 - 5x5 - Teyvat Conspiracy | A1, E1 | 23 | 7 |

## Clue coverage

Levels 03 and above introduce orthogonal connectivity, direct spatial identities,
count comparisons, conditionals, shared-neighbor parity, and regional budgets.
The collection covers FACT, SAME, DIFFERENT, EXACTLY, AT_LEAST, AT_MOST, ODD,
EVEN, COUNT_COMPARE, CONNECTED, and IMPLIES. Regions include rows, columns,
neighbors, common neighbors, intersections, immediate directions, the boundary,
and the whole grid. The loader also supports corners and named fixed groups.

Stage 13 (5x5) includes a count of characters from Liyue. That stage
uses `fixed_cast: true` to preserve origin-group membership. Other stages retain
randomized portrait casting. Connectivity ignores diagonals. Empty and singleton
selected-status groups satisfy CONNECTED. An additional count can assert existence.

Clues that can be safely removed become configurable QUOTE remarks. The pruning
pass verifies uniqueness and progressive solvability after each removal. Difficulty
has not been calibrated through human playtesting.

## Play and verify

Choose Stage in the game or launch a file directly.

```powershell
.\.venv-win\Scripts\python.exe main.py --puzzle data/puzzles/5x5/level_05.json
.\.venv-win\Scripts\python.exe scripts/validate_levels.py --output docs/level_validation.json
```

Validation checks every clue against its solution, independently searches for a
second complete model, and exercises the public reveal loop. The JSON report
includes active clue IDs and the accepted verdict/reveal sequence. It contains
solution spoilers. The game never reads that report.

## Rebuild stages

These commands overwrite the generated stage files with their reproducible versions.

```powershell
.\.venv-win\Scripts\python.exe scripts/build_levels.py
.\.venv-win\Scripts\python.exe scripts/build_extended_levels.py
.\.venv-win\Scripts\python.exe scripts/validate_levels.py --output docs/level_validation.json
```

The first script rebuilds levels 01-02. The second rebuilds levels 03-04 for 3x3
and 4x4, and levels 03-05 for 5x5. Each applies the redundant-clue pruning pass.
The runtime development analyzer uses semantic backtracking. Teammates should
extend their CNF/DPLL encoder to support the new public clue fields before
connecting their assessed agent to these stages.
