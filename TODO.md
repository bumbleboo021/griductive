# Project checklist

[English](TODO.md) | [Tiếng Việt](TODO_vi.md)

Implemented features and completed verification and handoff checklist.
Installation and usage are in [README.md](README.md). Report sources are
maintained on the [report branch](https://github.com/bumbleboo021/griductive/tree/report).

## Implemented

- [x] Validated JSON loading and immutable public-state models.
- [x] Private answers, justified verdicts and progressive clue reveals.
- [x] Distinct insufficient-evidence and contradicted-verdict feedback.
- [x] Pygame interface, keyboard controls, stage picker, Restart, Hint and Auto Solve.
- [x] Portraits, background, fonts, music selection and interaction animations.
- [x] Smooth clue scrolling and referenced-cell highlighting.
- [x] Thirteen stages across 3×3, 4×4 and 5×5 grids.
- [x] CNF encoding for core clues, parity, comparisons, implications and connectivity.
- [x] Deterministic primary/auxiliary variable allocation and CNF statistics.
- [x] Custom DPLL with unit propagation, backtracking, assumptions and timeouts.
- [x] Smallest-ID and dynamic two-sided Jeroslow–Wang heuristics.
- [x] Public-state logic agent, deduction traces and full-clue uniqueness checking.
- [x] Docked Agent inspector with replay, actual SAT queries and cumulative metrics.
- [x] In-game heuristic switching with history reset and proved-card preservation.
- [x] Semantic validation, solver checks and offscreen UI integration tests.
- [x] Fixed experiment manifest and strict headless CSV/JSON benchmark export.
- [x] Two-heuristic comparison runner and report tables/figures on the report branch.
- [x] Report chapters, references, appendix and updated Agent illustration.
- [x] Published report PDF in the repository with README links.

## Verification and handoff

- [x] Retain and deliver the raw CSV/JSON used for report tables, with environment,
  source revision, repeats and timeout settings.
- [x] Verify a clean checkout can reproduce the report's experiment outputs.
- [x] Check the final PDF, cross-references, figures and required submission files.
- [x] Record the required demonstration and confirm its shared link is in the report.
- [x] Document asset sources, non-commercial educational use, and copyright notices in
  [assets/ATTRIBUTION.md](assets/ATTRIBUTION.md) and [assets/images/NOTICE.txt](assets/images/NOTICE.txt).
- [x] Check display scaling, keyboard navigation and audio on target computers.
