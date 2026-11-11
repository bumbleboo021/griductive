# Appendix: Use of Generative AI

## 1. Tool and scope

The project used OpenAI Codex through an IDE-connected assistant for planning,
Python/Pygame implementation, debugging, testing, interface customization, and
documentation. This appendix records assistance requested in the conversation up
to 11 November 2026. It does not represent a record of other team members' work.

AI assistance included generating and modifying source code, rather than only
explaining concepts. Most implementation assistance concerned Person 1's game
engine and graphical interface, corresponding to assignment section 4.1.

## 2. Requests and resulting assistance

Keyboard-control refinement: the assistant separated keyboard card selection
from opening verdict choices. Stages and restarts select the top-left card;
WASD/arrows move the selection, Enter opens choices with Innocent focused, and
keyboard directions select Innocent, Criminal, or Cancel before Enter confirms.
The popup displays keyboard focus and retains mouse controls. UI tests cover
navigation, confirmation, cancellation, default focus, and stage/reset selection.

Asset-credit update: at the project owner's direction, the assistant recorded
VMAS group as the source of the three instrumental tracks, HOYO-MiX as the source
of the other two music tracks, and Genshin Impact as the source of the character
images and background in `assets/ATTRIBUTION.md`. The inventory was matched to
the current files, and obsolete ambient WAV and M4A entries were removed. Source
URLs, font credits, and license or permission details remain for the team to fill
in; this update records supplied credits without independently verifying them.

The prompts below are representative excerpts or summaries of the user's requests,
in conversation order. Summaries are not presented as verbatim quotations.

| No. | User request | AI-assisted work or response |
| --- | --- | --- |
| 1 | Create a Pygame project structure and TODO.md using the reference game and the first five subsections of section 4 of the assignment PDF. | Read the local assignment PDF and reference website; created packages, dependency files, a starter application, README instructions, and a five-person task plan mapped to sections 4.1-4.5. |
| 2 | Explain how each person should start. | Explained shared data contracts, proposed first deliverables, component dependencies, and a first integration target consisting of one proved verdict and clue reveal. |
| 3 | Complete Person 1's work so teammates can implement and check their components immediately; ask about frontend decisions. | Implemented the game engine, validated puzzle loading, Pygame board and controls, public-state boundary, integration documentation, tutorial fixtures, tests, and a replaceable analyzer interface. The user initially selected shapes and text without external portraits. |
| 4 | Check the terminal log. | Inspected the visible IDE terminal, identified a pip launcher referencing an obsolete environment path, verified the prepared Windows environment, and supplied commands to use it. |
| 5 | Recommend a source for multiple levels. | Searched for puzzle archives and data sources; discussed the official archive and existing JSON examples, plus the need for schema conversion and validation. |
| 6 | Explain how to modify the frontend and how people organize frontends. | Identified rendering and input methods, explained Pygame's drawing/event approach, and proposed theme, component, and screen organization. |
| 7 | Use the supplied character icons and fonts; display the filename's origin label instead of the original profession; ask about frontend preferences. | Added portrait lookup and caching, parsed name/origin metadata from filenames, used the supplied fonts, updated tutorial casts, and retained the dark theme selected by the user. Labels such as Chef and Alcohol were preserved as supplied. |
| 8 | Enlarge character icons and explain UI configuration. | Increased portrait sizes, extracted UI settings into config.py, and wrote customization instructions covering card spacing, fonts, colors, and portrait dimensions. |
| 9 | Follow the reference game's card concept: horizontal cards, large icons, names and smaller role text; shrink and move solved icons upward, reveal a clue, and use the supplied background. | Added a dedicated card renderer, timed portrait movement/shrinking, delayed clue appearance, a background with a dark overlay, and selection of the full clue in the side panel. Suggested additional gameplay improvements. |
| 10 | Randomize the characters for each level and replace cell IDs in displayed clues with character names. | Randomized the display cast on GUI level loading, kept Restart stable, and resolved cell references to current names when rendering clues. Added an optional name-plus-coordinate display setting. |
| 11 | Do not sort randomized characters alphabetically. | Removed sorting from the randomized GUI cast so sampled characters occupy cells in random order. |
| 12 | Find existing 3x3, 4x4, and 5x5 Griductive maps, excluding HCMUS AI projects. | Searched original developer sources, the official archive, and Reddit app documentation. No downloadable non-course collection containing all three sizes was verified or imported. |
| 13 | Record the requested assistance in appendix.md for the report appendix. | Prepared this disclosure document. |

## 3. Implementation contributions

### Project planning and setup

- Created the Python package structure and initial dependency files.
- Created `TODO.md` with five-person ownership, implementation checklists,
  integration milestones, and shared report/video responsibilities.
- Updated `README.md` with run instructions and environment guidance.
- Prepared a local `.venv-win` environment for development and verification.

### Engine and integration boundary

- Added immutable shared character, clue, status, public-state, and analysis models
  in `griductive/domain/models.py`.
- Added puzzle JSON parsing and structural validation in
  `griductive/engine/puzzle.py`, including required regions and support for parity
  clues and intersection regions in the temporary development path.
- Implemented initial reveals, Restart, public snapshots, verdict outcomes,
  progressive reveals, Hint, and one-step automatic solving in
  `griductive/engine/game.py`.
- Kept hidden solution labels and unrevealed clues outside the analyzer's input.
- Added a plugin interface for a teammate's `analyze(PublicState)` implementation,
  GUI/headless launch options, and a public-state integration checker.
- Created simple FACT-chain tutorial fixtures for 3x3, 4x4, and 5x5 boards.
  These fixtures were generated for this project; they were not downloaded
  official Griductive levels.

### Temporary reference analyzer

AI assistance also produced `griductive/engine/reference.py`, a semantic
backtracking analyzer that works on public information and uses a deadline.
It enables immediate gameplay and comparison while teammates implement their
components. It is not the assignment's required CNF encoder or DPLL SAT solver.

The engine delegates consistency and entailment classification to its analyzer.
The final team implementation must connect and validate the assessed logic agent.
The reference analyzer and integration checker do not replace independent solver,
encoding, uniqueness, or experiment work.

### Frontend and assets

- Implemented board rendering, card selection, status feedback, clue highlighting,
  Load, Restart, Hint, and Auto Solve in Pygame.
- Added serial background analysis so the drawing/event loop remains responsive.
- Integrated user-supplied portraits and fonts, with origin labels parsed from
  portrait filenames.
- Added `config.py` for appearance settings and `character_card.py` for rendering
  and reveal animations.
- Integrated the user-supplied background with a configurable dark overlay.
- Randomized character display assignments on GUI loading without changing cell
  IDs, clue constraints, solution labels, or initial reveals; Restart preserves
  the current assignment.
- Displayed current character names in clues while preserving stable cell-based
  references in structured puzzle data.
- Wrote `docs/INTEGRATION.md` and `docs/UI_CUSTOMIZATION.md`.

The artwork and font files were supplied by the user, not generated by the AI.
The existing `assets/images/NOTICE.txt` records attribution information for the
artwork and should remain with the assets.

## 4. Verification performed during assistance

The assistant ran Python checks and automated tests during implementation.
The most recent complete test run recorded in the conversation passed 29 tests.
After the final change removing alphabetical sorting from the randomized cast,
the targeted UI suite passed 11 tests. The complete suite was not rerun after
that final targeted change.

Checks covered public-state isolation, accepted/rejected verdict transitions,
restart behavior, invalid puzzle input, stalled/inconsistent states, progressive
tutorial solving, UI events, rendering across board sizes, animation timing,
delayed clue appearance, random cast behavior, and clue name substitution.

Earlier integration-checker runs passed 62 public-state comparisons, including
progressive reveals on all three tutorial sizes. These checks used the temporary
reference analyzer; they are not evidence that the team's eventual DPLL
implementation has passed validation.

The assistant inspected offscreen Pygame renders, including intermediate and
finished reveal states. This does not establish that every desktop display scale
or every possible clue length has been manually checked.

## 5. External references and search limitations

- [Official Griductive game](https://knotwise.games/games/griductive)
- [Official Griductive archive](https://knotwise.games/games/griductive/archive)
- [Original developer announcement describing 3x3, 4x4, and 5x5 boards](https://www.reddit.com/r/playmygame/comments/1r5fdze/griductive_a_detectivestyle_logic_puzzle_game/)
- [Griductive Reddit app documentation](https://developers.reddit.com/apps/griductive)
- [Developer article about puzzle generation](https://dev.to/_a80b26c075279295b18e9/what-is-griductive-and-how-the-puzzles-are-made-24f5)
- Local assignment document: `AI - Project 2.pdf`.

The reference site's text was accessible. An attempt to inspect its interactive
board through the browser tool failed because the browser access host was
unavailable. The frontend changes therefore followed the user's description and
available reference information, rather than a verified pixel-for-pixel copy.

An early recommendation mentioned public student solver repositories as possible
JSON examples. After the user excluded HCMUS AI projects, subsequent map searches
focused on original developer sources. No external repository level files or
official puzzle JSON were imported as part of this assistance.

The Reddit app documentation mentioned `data.griductive.com`, but a working
public JSON index or individual download URL was not verified. That domain must
not be described in the report as a successfully used dataset source.

## 6. Human decisions and remaining responsibilities

Subsequent keyboard-navigation request: the assistant added WASD and arrow-key
movement from the selected card, reusing mouse-selection behavior. Unresolved
cards open their verdict popup and solved cards select their clue. Movement
stops at board edges and is blocked during analysis, Auto Solve, or other modal
dialogs. Tests cover all eight keys, edge behavior, solved-card transitions,
and blocked input without changing puzzle knowledge.

Subsequent stage-navigation request: the assistant added a draggable Stage-picker
scrollbar with track-click navigation alongside mouse-wheel scrolling. Tests cover
dragging in both directions, clamping, release, stage selection after scrolling,
and hiding the scrollbar for a short stage list.

Subsequent stage-expansion request: the assistant removed the three playable
tutorial JSON files, retained their chain data as test fixtures, and changed the
default stage to 3x3 level 01. Seven additional stages were constructed, giving
four 3x3, four 4x4 and five 5x5 stages. The semantic development analyzer, loader,
display model and independent validator gained count comparisons, orthogonal
connectivity and implications, plus directional, boundary, whole-grid and common-
neighbor regions. A named Liyue-origin group in 5x5 level 05 uses a fixed cast.
The stages were pruned to replace removable clues with quotes and all 13 passed
clue-truth, complete-clue uniqueness and public progressive-solving validation.
The suite passed 80 tests, including exhaustive partial-assignment checks for the
new clue families. Teammate CNF/DPLL support for these fields remains pending.

Selection-style clarification: the assistant removed the extra inset selection
outline and made selected cards use the same tint, outer outline, lift and
interpolation as mouse-hovered cards.

Subsequent Auto Solve animation correction: the assistant connected automatically
proved cards to the same hover interpolation used for mouse input, including
the lift, color transition and outline. The active card keeps focus during its
reveal, including the final solved move. Restart and stage changes clear the
automatic focus. Tests exercise normal and final automatic-move completion.

Subsequent portrait-sizing issue: the assistant found that Ayaka and Xiangling
have narrower PNG canvases than most other portraits. Rendering was changed to
preserve each image's aspect ratio, centered horizontally and aligned at the
bottom of its portrait area. Regression checks cover Ayaka, Xiangling and Lumine.

Subsequent clue-panel request: the assistant grouped revealed clues inside a
bordered panel, added a scroll-position indicator, and implemented time-based
easing for wheel and precise trackpad scrolling. Clue selection scrolls toward
the selected item. Tests cover interpolation, bounds, reset, clipped hit targets,
and ignoring wheel events outside the clue panel.

Subsequent attribution and music-selection request: the assistant created a
fillable asset inventory and per-source attribution template, with a folder guide
for license texts. The game gained a Tracks picker with file-derived track names,
streamed looping playback, session-level track selection, and playback recovery
when loading a different track fails. The user offered to supply an MP3 VBR
version of an existing M4A file. The implementation lists native WAV, OGG, MP3,
and FLAC files. An attempted M4A conversion dependency was removed after that
clarification. Asset license details remain placeholders for the user to complete.

Subsequent UI request: the assistant added timed hover feedback to buttons,
character cards, and stage entries. The Load control became Stage, showing each
JSON's root name field with legacy title compatibility. Bundled levels and their
build script were updated with names. A top-right question-mark button opens a
how-to-play panel. The user approved adding an original ambient loop. The
assistant synthesized a 16-second WAV loop and implemented an initially disabled
music toggle, volume configuration, audio error handling, and cleanup on exit.
Hover, named-stage loading, help dismissal, and music playback toggling were
covered by tests and offscreen renders of the new screens were reviewed.

Subsequent notification request: the assistant added an Incorrect verdict dialog
for contradicted choices and a Not enough evidence dialog for choices that public
clues cannot yet prove. Continue, Enter, Space, or Escape dismisses the dialog.
The implementation interprets "without hint" as lacking sufficient revealed
evidence. Using the Hint button is optional. Tests cover rejection, unchanged
state, blocked background clicks, dismissal, and a subsequent accepted verdict.
The full suite passed 49 tests and both notification layouts were inspected.

Subsequent card-layout request: the user asked to remove the waiting text and
make character cards vertical across the left side. The assistant enlarged the
board and centered larger portraits, removed Awaiting verdict, and introduced a
1180x1020 logical window with automatic display scaling. All 13 targeted UI tests
passed, including vertical-card checks on 3x3, 4x4, and 5x5 boards. The offscreen
driver reported a software-renderer warning. The layout render was inspected.

Subsequent interaction change: the user requested removing the Selected label
and permanent Criminal/Innocent controls. The assistant implemented a character
verdict popup, dismissal by Cancel/Escape/outside click, and relocated the four
general controls beneath the clue panel. The complete suite passed 48 tests,
including popup submission, dismissal, and unchanged-state checks. Open/closed
popup renders were inspected.

Subsequent clue-presentation request: the assistant preserved structured region
wording, added innocent-target counts normalized to criminal constraints, supported
neighbor intersections with multiple rows/columns, and introduced nonlogical
QUOTE cards using configurable personal remarks. A bounded pruning script replaced
removable clues in all six original levels only after uniqueness and progressive
solving checks. All six levels were revalidated; the complete suite passed 47
tests at this stage. The teammate integration guide documents ignoring QUOTE
constraints and avoiding a second conversion of normalized innocent counts.

Subsequent level-design request: the user asked for two levels for each of 3x3,
4x4, and 5x5. The assistant created six original seeded levels, a reproducible
construction script, an offline semantic validator, a level catalog, and saved
validation traces. Every level passed clue-truth, full-clue uniqueness, and
progressive-solving checks with the temporary reference analyzer. These levels
were created with AI assistance and are not imported official Griductive maps.
The assessed CNF/DPLL-based checks remain the team's responsibility.

Subsequent research request: the user asked the assistant to read Griductive
documentation and determine how to create solvable levels using original-game
clue families. The assistant consulted the official glossary, strategy guide,
and developer generation article, compared them to the local implementation,
and wrote `docs/LEVEL_DESIGN.md`. The guide distinguishes clue truth, full-clue
uniqueness, and progressive solvability; it proposes an offline validator and
generator. No generator or new validated puzzle was implemented in that research
step. The official guide pages initially timed out on direct access; their
indexed text was subsequently available through web search.

The user chose Pygame, the five-person task structure, initial text/shape assets,
the later supplied character artwork and fonts, retention of the dark theme,
filename-derived origin labels, the requested reveal behavior, the background,
and randomized character placement without alphabetical sorting.

The team should review, understand, and adapt the generated code before final
submission. The main CNF encoding, DPLL solver, assessed deduction agent,
full-puzzle uniqueness checking, final experiment set and measurements, report,
and demonstration video remain separate team responsibilities in the recorded
scope. Suggestions such as keyboard shortcuts, hover feedback, deduction history,
sound settings, and reduced-motion settings were recommendations, not completed
features unless subsequently implemented by the team.

Before inserting this appendix into the final report, update it with subsequent
AI use, the final test results, actual team contributions, and any additional
assets or external puzzle data used. No individual contribution percentage is
inferred from this assistance log.
