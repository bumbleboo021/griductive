# Appendix: Use of Generative AI

## 1. Tools and Scope

Generative AI tools (**OpenAI Codex**, **Google Gemini**, and **Antigravity IDE AI Assistant**) were used during the **Griductive** project to support architecture planning, game engine and Pygame UI development, original stage design, conceptual tutoring on CNF/DPLL, code review, automated test generation, and documentation.

**Human–AI boundary:** The team made all architectural, design, and asset decisions, supplied all artwork, fonts, and audio assets, and wrote the core algorithmic components (`griductive/logic/encoder.py` entirely without AI-generated production code, and the core DPLL solver in `griductive/sat/dpll.py` with AI limited to tutoring, code review, and the optional `jw` heuristic extension).

## 2. Summary of Key Requests

The table below summarizes the main ideas of the substantive requests used to complete the project:

| No. | Main Idea of Request | AI-Assisted Output |
| --- | --- | --- |
| 1 | **Project structure & task plan** — organize the Python/Pygame repository and shared contracts from the assignment specification. | Created package layout, dependency files, CLI entry point, `README.md`, and `TODO.md` with shared data models and milestones. |
| 2 | **Game engine & public-state boundary** — build progressive reveal mechanics, puzzle validation, and a replaceable analyzer interface. | Implemented immutable domain models (`griductive/domain/models.py`), validated JSON loader (`puzzle.py`), `GameEngine` (`game.py`), a temporary semantic reference analyzer (`reference.py`) for early testing, and `docs/INTEGRATION.md`. |
| 3 | **Pygame UI & card presentation** — build vertical character cards, reveal animations, dark theme, and supplied asset integration. | Implemented board/card rendering (`window.py`, `character_card.py`, `assets.py`, `config.py`), aspect-preserving portrait caching, character-name substitution in clues, and `docs/UI_CUSTOMIZATION.md`. |
| 4 | **Gameplay interactions & polish** — add verdict popups, evidence feedback, clue scrolling, keyboard controls, help, and music. | Added mouse + WASD/arrow/Enter verdict controls, `Incorrect verdict` / `Not enough evidence` dialogs, smoothed clue-panel scrolling with cell highlighting, draggable stage picker, help modal, and multi-track music playback. |
| 5 | **Original stage design & validation** — construct progressively solvable 3×3, 4×4, and 5×5 puzzles using Griductive clue families. | Documented level-design rules (`docs/LEVEL_DESIGN.md`) and created 13 original stages (four 3×3, four 4×4, five 5×5) validated offline for clue truth, full-clue uniqueness, and progressive solvability. |
| 6 | **CNF modeling concepts & contract review** — clarify propositional logic encoding and verify the `encode(PublicState) -> CNFResult` API. | Explained DIMACS literal mapping, proof-by-contradiction entailment, and primary/auxiliary variable conventions without generating production encoder code. |
| 7 | **Automated CNF encoder test suites** — verify binary, cardinality, parity, comparison, connectivity, and end-to-end puzzle encoding. | Generated four `pytest` suites (`test_easy_encoder.py`, `test_hard_encoder.py`, `test_superhard_encoder.py`, `test_integration.py`) with exhaustive truth-table, BFS, and differential checks across all 13 stages. |
| 8 | **DPLL tutoring & step-by-step code review** — understand unit propagation/backtracking and debug the handwritten solver. | Explained DPLL clause states (`SAT`, `CONFLICT`, `UNIT`, `OPEN`) and entailment queries; identified bugs during iterative implementation in `griductive/sat/dpll.py`. |
| 9 | **DPLL branching heuristic extension** — compare heuristics and add Dynamic Two-Sided Jeroslow–Wang (`jw`) alongside `smallest`. | Explained Jeroslow–Wang scoring and polarity selection, implemented the optional `heuristic="jw"` selector, and benchmarked it against `smallest`. |
| 10 | **DPLL verification & documentation** — generate solver oracle tests and Vietnamese technical notes/comments. | Generated `tests/sat/test_dpll.py` (including randomized truth-table oracle checks), translated code/test comments to Vietnamese, and prepared `docs/DPLL_NOTES.md`. |

## 3. Verification Summary

- **Full test suite (`python -m pytest tests -q`):** **298 passed** (`67.40s`), including:
  - **189 passed** across the four CNF encoder test suites (`tests/logic/`).
  - **10 passed** in `tests/sat/test_dpll.py` (edge cases, `PHP(4,3)` UNSAT backtracking, timeout handling, and 175 randomized `1..5`-variable formulas verified against a $2^n$ truth-table oracle for both `smallest` and `jw`).
  - Engine, UI, keyboard/popup interaction, animation, and stage-validation tests.
- **Public-state analyzer check (`python -m griductive.check_analyzer --analyzer griductive.agent.adapter:Agent`):** **PASS: 62 public-state checks** across `3×3`, `4×4`, and `5×5` progressive reveals.
- **13-stage progressive benchmark (`Agent(timeout_seconds=10.0, strict_dpll=True)`):**
  - `smallest`: **13/13** solved (`7,988` SAT calls, `11,442` decisions, `331,964` propagations, `0` backtracks, `5.39s` solver time).
  - `jw`: **13/13** solved (`7,988` SAT calls, `10,122` decisions [-11.5%], `332,726` propagations, `0` backtracks, `5.30s` solver time).

## 4. External References

- [Official Griductive game](https://knotwise.games/games/griductive) and [archive](https://knotwise.games/games/griductive/archive)
- [Original developer announcement describing 3×3, 4×4, and 5×5 boards](https://www.reddit.com/r/playmygame/comments/1r5fdze/griductive_a_detectivestyle_logic_puzzle_game/)
- [Developer article on Griductive puzzle generation](https://dev.to/_a80b26c075279295b18e9/what-is-griductive-and-how-the-puzzles-are-made-24f5)
- Course assignment specification: `AI - Project 2.pdf`
