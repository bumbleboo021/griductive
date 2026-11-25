🌐 **Language:** [English](LEVEL_DESIGN.md) | [Tiếng Việt](LEVEL_DESIGN_vi.md)

# Designing solvable Griductive levels

Implementation update after stage expansion: the loader and development analyzer
now support COUNT_COMPARE, CONNECTED and IMPLIES, along with common-neighbor,
directional, whole-grid, boundary and corner regions. Seven stages using these
features were added and validated. See LEVELS.md and INTEGRATION.md for the
current catalog and schema. CNF/DPLL support remains a teammate integration task.

## Research sources

This guide separates documented game behavior from a proposed implementation for
this repository. It does not claim to reproduce the original generator.

- [Official how-to-play and glossary](https://knotwise.games/games/griductive/how-to-play)
- [Official strategy guide](https://knotwise.games/games/griductive/strategy)
- [Developer's explanation of puzzle generation](https://dev.to/_a80b26c075279295b18e9/what-is-griductive-and-how-the-puzzles-are-made-24f5)

The developer article describes choosing a solution, collecting true candidate
clues, selecting constraints, checking uniqueness, estimating difficulty, and
building hints. It also describes a separate progressive-solving test. This is a
useful architectural reference, not source code or an exported level dataset.
[Source](https://dev.to/_a80b26c075279295b18e9/what-is-griductive-and-how-the-puzzles-are-made-24f5)

## Original clue vocabulary versus current support

The glossary defines rows, columns, diagonal-inclusive neighbors, edges/corners,
between-regions, common neighbors, immediate directions, exact/minimum counts,
odd counts, comparisons, and group superlatives. Connectivity uses orthogonal
steps. Statements remain true even when spoken by a criminal.
[Source](https://knotwise.games/games/griductive/how-to-play)

The strategy guide explicitly discusses membership-plus-count clues, overlaps,
count budgets, connected groups, and odd parity. It says even parity exists in
the engine but is not published in current puzzles. Its current daily format is
4 columns by 5 rows, so our square sizes are a project adaptation.
[Source](https://knotwise.games/games/griductive/strategy)

The following are invented examples illustrating those families, not copied
puzzle statements. Internal names are suggested schema names, not official APIs.

| Clue family | Example | Support in this repository |
| --- | --- | --- |
| Exact count | Exactly 2 criminals in row 1. | `EXACTLY` |
| Zero count | No criminals in column C. | `EXACTLY` with count 0 |
| Minimum count | At least 1 criminal among A1, B1, C1. | `AT_LEAST` |
| Neighbor count | Exactly 1 criminal neighbors B2. | `EXACTLY` with a neighbors region |
| Overlap count | Exactly 1 criminal is both in row 1 and a neighbor of B2. | Count over an intersection region |
| Odd count | Row 2 contains an odd number of criminals. | `ODD` |
| Membership and count | A1 is criminal, and exactly 2 criminals neighbor B2. | Needs a compound clue or two constraints; cannot be represented as one current card clue |
| Region comparison | Row 1 contains more criminals than row 2. | `COUNT_COMPARE` in the development analyzer |
| Connected group | The criminals in column B form one orthogonally connected group. | `CONNECTED` in the development analyzer |
| Strict maximum | Row 1 has more criminals than every other row. | Not implemented |
| Unique matching count | Column B alone has exactly 2 criminals among columns. | Not implemented |

The current code additionally accepts `FACT`, `SAME`, `DIFFERENT`, `AT_MOST`,
and `EVEN`. These are project capabilities; their presence in our schema does
not establish that they are standalone sentence templates in current daily games.
For levels styled after the original, prioritize counts, neighbors, overlaps,
and ODD before implementing the more complex families.

Important semantic distinctions:

- A named member plus a count is a conjunction. A criminal named as a member
  must belong to the counted region; merely encoding the count loses information.
- A statement giving a total and a subregion count requires both constraints.
  For example, 3 criminals in R with 1 in R intersect S differs from only counting
  the intersection.
- Counting innocent people can be translated to criminal counts on a fixed region:
  exactly k innocents means exactly `len(region) - k` criminals.
- Use stable cell IDs in constraints; names are a display substitution.
- Shared-region totals need an explicit union/deduplication rule in our schema.
- When implementing connectivity, define behavior for empty groups explicitly;
  require a positive count if the intended sentence asserts people exist.

These are implementation rules for avoiding ambiguous encodings, not a claim
that every wording above is already supported by the loader.

## Three separate correctness checks

A proposed level must pass all three:

1. **Clue truth:** each clue is true under the stored complete solution.
2. **Complete-clue uniqueness:** all clues, together with the initial known
   statuses, admit exactly one complete assignment of primary status variables.
3. **Progressive solvability:** using only initial reveals and subsequently proved
   statuses/clues, a forced move remains available until every card is revealed.

Truth alone is insufficient. So is complete-clue uniqueness. For example, an
initial card can reveal a tautology while all useful clues remain locked; the
complete puzzle may be unique, but there is no legal first move.

For Boolean Ci meaning criminal, a verdict is proved by these queries:

```text
if SAT(KB) is false:
    INCONSISTENT
elif SAT(KB AND NOT Ci) is false:
    Ci is CRIMINAL
elif SAT(KB AND Ci) is false:
    Ci is INNOCENT
else:
    Ci is UNKNOWN
```

Check base consistency first: an inconsistent KB cannot establish useful verdicts.
Timeout is a separate result and must never be treated as proof or UNKNOWN.

For uniqueness, solve the complete-clue KB once, then block that model's primary
assignment and solve again:

```text
block = OR( NOT Ci if model[Ci] else Ci, for every primary Ci )
unique iff SAT(full_KB) and UNSAT(full_KB AND block)
```

Do not block auxiliary variables: different auxiliary assignments can encode the
same character solution. Compare the first model to the stored solution too.

## Proposed generation procedure for this project

This is a practical design proposal, not an implemented generator.

1. Choose board size and a seeded random criminal/innocent solution. Avoid all-one
   status boards for the initial level set; choose a reasonable mix.
2. Enumerate rows, columns, neighbor regions, and useful intersections. Explicit
   cell lists can represent other fixed shapes, but prefer readable geometric groups.
3. Calculate each region's actual criminal count and build true EXACTLY,
   AT_LEAST, AT_MOST, and ODD candidates. Exclude empty tautologies and trivial
   minimum/maximum bounds. Avoid making every clue a FACT.
4. Choose one or more initially revealed cards. Their statuses and clues are the
   only starting knowledge. Reserve an informative opening clue for these cards.
5. Assign candidate clues to card owners and simulate public solving. When a
   new card is proved, its clue becomes available. Favor clue assignments that
   create a continuing deduction path.
6. If stalled, revise a clue on an already available card, increase initial
   reveals, or reject this attempt. Merely adding a helpful clue to a still-hidden
   card does not unblock the current state. Restart validation after a revision.
7. Run the three correctness checks. Keep a trace showing which public clues
   justified each move. Save the seed and validation results with level metadata.
8. Try removing/replacing redundant constraints or reducing initial reveals. After
   every change, rerun truth, uniqueness, and progressive-solving checks.
9. Measure difficulty and human-test the puzzle before publishing it.

Suggested pseudocode:

```python
for attempt in range(max_attempts):
    solution = sample_solution(size, rng)
    pool = true_readable_clues(solution, supported_templates)
    puzzle = assign_clues_to_cards(pool, solution, initial_reveals, rng)
    if not all_clues_true(puzzle):
        continue
    if not full_clue_solution_is_unique(puzzle):
        continue
    trace = solve_with_progressive_reveals(puzzle)
    if trace.completed:
        return puzzle, trace
raise GenerationError("No validated puzzle within attempt/time budget")
```

The helper functions above still need implementation. Do not confuse the existing
`--headless` command with a full uniqueness validator: it demonstrates the public
reveal loop, but does not independently validate every hidden clue's truth.

## A small deduction design example

Suppose a 3x3 board starts with A1 known innocent. Its clue says column C has
zero criminals. That immediately forces C1, C2, and C3 innocent.

Assign C3 a clue saying exactly one criminal neighbors C3. Its neighbors are
B2, C2, and B3. After C2 is known innocent, this alone leaves two possibilities;
it does not yet prove B2 or B3.

To continue, provide another accessible constraint that distinguishes those two,
or choose B3 as an additional initially innocent card. Then B2 must be criminal.
B2's newly revealed clue can constrain the next region. Continue designing until
all statuses are forced, then run the complete validation pipeline.

This example illustrates dependencies only. It is not a complete nine-card puzzle
and should not be saved as a validated level without the remaining clues/checks.

## Difficulty beyond board size

For our level set, record:

- Number of initial reveals and total proved moves.
- Forced moves available at each step; many simultaneous forced moves often
  indicate a broad, easy opening.
- Whether deductions require combining multiple revealed clues.
- Dependency depth, region overlap, and clue-family diversity.
- Solver runtime and decisions, recorded separately from human difficulty.

These are proposed project measurements. A fast SAT query does not necessarily
mean a human finds the clue easy. Do not present an uncalibrated score as the
official Griductive difficulty formula.

## Randomized portraits and clue safety

Our GUI randomizes character names/origins while preserving cell-based clues.
This is safe for the current constraints. A future clue about a profession or
origin group would become unsafe if the cast changes that group's membership.

For such clues, either lock the cast per puzzle or regenerate/revalidate the clue
regions after casting. Keep references to a named person stored as a stable cell
ID and substitute the current display name only when rendering.

## Recommended next implementation

Start with an offline level validator, then a seeded generator using EXACTLY,
AT_LEAST, neighbor counts, intersection counts, and ODD. Validate 3x3 cases first,
then 4x4 and 5x5. Keep the six assignment templates available for coverage tests.
Add comparison, compound, and connectivity clues only when both the independent
evaluator and the CNF/DPLL path can handle them correctly.

The existing loader checks structure, not the three full correctness properties.
`engine/reference.py` provides a temporary public-state analyzer. The final
teammate agent should supply the assessed DPLL-backed path; the generation and
validation tools can use that through a clearly defined adapter.
