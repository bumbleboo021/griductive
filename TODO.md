# Project checklist

[English](TODO.md) | [Tiếng Việt](TODO_vi.md)

Implemented features and remaining follow-up work. Installation and usage are in
[README.md](README.md). Report sources are maintained on the
[report branch](https://github.com/bumbleboo021/griductive/tree/report).

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

- [ ] Retain and deliver the raw CSV/JSON used for report tables, with environment,
  source revision, repeats and timeout settings.
- [ ] Verify a clean checkout can reproduce the report's experiment outputs.
- [ ] Check the final PDF, cross-references, figures and required submission files.
- [ ] Record the required demonstration and confirm its shared link is in the report.
- [ ] Review asset redistribution permissions and retain applicable license notices.
- [ ] Check display scaling, keyboard navigation and audio on target computers.

These items need confirmation; implemented code alone does not establish that the
final data archive, demonstration or submission package has been delivered.

## Follow-up improvements

- [ ] Reconcile `Agent.run_trace()` with the engine reveal lifecycle so accepted
  moves do not trigger an additional unrecorded analysis.
- [ ] Audit trace termination and error handling for rejected moves, already solved
  stages and timeouts.
- [ ] Consider exposing both heuristics through the main benchmark CLI, rather than
  relying on the separate report comparison runner.
- [ ] Add runtime variability (for example, IQR) alongside medians in experiment outputs.
- [ ] Review older technical guides for outdated handoff instructions.
