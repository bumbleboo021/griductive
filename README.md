# griductive
Project Introduction to Artificial Intelligence - CS14003

A Python/Pygame project inspired by [Griductive](https://knotwise.games/games/griductive).
Person 1's game engine and Pygame interface are implemented, with playable tutorial
puzzles and a replaceable reference analyzer. See [TODO.md](TODO.md) for ownership
and [docs/INTEGRATION.md](docs/INTEGRATION.md) for teammate APIs, puzzle format, and checks.

## Setup

Use Python 3.11 or newer. Create the environment on the operating system where you
will run the game (a Linux virtual environment cannot be reused on Windows).

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python main.py
```

On Linux/macOS, activate with `source .venv/bin/activate` instead.
Close the window or press Escape to quit. Run `python -m pytest tests -q` from the
repository root. If your existing `.venv` is for another OS, create a separate
`.venv-win` on Windows instead; do not overwrite an environment you still use.

```text
python main.py --headless
python -m griductive.check_analyzer
python main.py --analyzer griductive.agent.adapter:Agent
```

The last command works after Person 4 implements that adapter. The default
reference analyzer enables development now; it is not the assessed CNF/DPLL
implementation. It supports core clues and parity with a three-second deadline
per analysis; large difficult puzzles may time out. No PNG assets are needed.

## Layout

```text
griductive/
  app.py                 Pygame startup and application wiring
  domain/                Shared models, clues, regions, public state
  engine/                Private puzzle, loading, verdict/reveal lifecycle
  ui/                    Pygame screens, cards, controls, clue highlights
  logic/                 Variable mapping, CNF encoding, semantic evaluation
  sat/                   Hand-written DPLL and solver statistics
  agent/                 Entailment, hints, deduction trace, uniqueness
  experiments/           Benchmark runner and metric export
assets/{fonts,images,sounds}/
data/puzzles/{3x3,4x4,5x5}/
tests/{engine,logic,sat,agent,integration}/
docs/{report,demo}/
results/                 Generated benchmark output (ignored by Git)
main.py                  Run from the repository root
TODO.md                  Requirements, ownership, interfaces, milestones
```

Keep domain and solver modules independent of Pygame. Only the engine owns hidden
statuses and unrevealed clues; the agent receives a public-state snapshot.
Empty directories contain `.gitkeep` files so Git preserves the structure.
