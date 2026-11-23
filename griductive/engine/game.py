"""Engine: authoritative private state and atomic public reveal transitions."""
from dataclasses import dataclass
from griductive.domain.models import Analysis, Analyzer, PublicState, Status
from griductive.engine.puzzle import Puzzle


@dataclass(frozen=True)
class Outcome:
    code: str
    message: str
    cell: str | None = None


class GameEngine:
    def __init__(self, puzzle: Puzzle, analyzer: Analyzer):
        self._puzzle = puzzle
        self._analyzer = analyzer
        self.restart()

    @property
    def title(self):
        return self._puzzle.title

    def restart(self):
        self._revealed = frozenset(self._puzzle.initially_revealed)

    def set_analyzer(self, analyzer: Analyzer):
        """Replace the analyzer between actions, preserving the revealed board."""
        self._analyzer = analyzer

    def analyze(self) -> Analysis:
        """Classify the current public state without revealing any cards."""
        return self._analysis()

    @property
    def solved(self):
        return len(self._revealed) == len(self._puzzle.characters)

    def public_state(self) -> PublicState:
        revealed = self._revealed
        return PublicState(self._puzzle.size, self._puzzle.characters,
                           tuple((c, s) for c, s in self._puzzle.solution if c in revealed),
                           tuple(clue for char, clue in zip(self._puzzle.characters, self._puzzle.clues)
                                 if char.cell in revealed))

    def _analysis(self) -> Analysis:
        state = self.public_state()
        result = self._analyzer.analyze(state)
        if not isinstance(result, Analysis) or type(result.consistent) is not bool:
            raise ValueError("Analyzer must return Analysis")
        if not result.consistent:
            if result.verdicts:
                raise ValueError("Inconsistent analysis must have no verdicts")
            return result
        unresolved = [c.cell for c in state.characters if c.cell not in self._revealed]
        if [c for c, _ in result.verdicts] != unresolved or any(not isinstance(s, Status) for _, s in result.verdicts):
            raise ValueError("Analyzer must classify every unresolved cell in row-major order with Status enums")
        return result

    def hint(self) -> Outcome:
        analysis = self._analysis()
        if not analysis.consistent:
            return Outcome("INCONSISTENT", "The revealed clues and statuses are inconsistent.")
        if self.solved:
            return Outcome("SOLVED", "All characters have been proved.")
        for cell, status in analysis.verdicts:
            if status != Status.UNKNOWN:
                return Outcome("HINT", f"{cell} can be proved {status.value.lower()}.", cell)
        return Outcome("STALLED", "No verdict is currently provable. No card was revealed.")

    def submit_verdict(self, cell: str, status: Status) -> Outcome:
        if not isinstance(status, Status) or status == Status.UNKNOWN:
            raise ValueError("Submit CRIMINAL or INNOCENT")
        if cell not in {c.cell for c in self._puzzle.characters}:
            raise ValueError("Unknown cell")
        if cell in self._revealed:
            return Outcome("ALREADY_REVEALED", "This card is already revealed.", cell)
        analysis = self._analysis()
        if not analysis.consistent:
            return Outcome("INCONSISTENT", "The revealed clues and statuses are inconsistent.")
        return self._apply(cell, status, dict(analysis.verdicts)[cell])

    def _apply(self, cell, status, forced):
        if forced == Status.UNKNOWN:
            return Outcome("NOT_PROVABLE", "Neither verdict is currently forced. Card unchanged.", cell)
        if status != forced:
            return Outcome("CONTRADICTED", "The revealed information proves the opposite verdict.", cell)
        if dict(self._puzzle.solution)[cell] != status:
            return Outcome("ERROR", "Proved verdict conflicts with puzzle data; check the puzzle or analyzer.", cell)
        self._revealed = self._revealed | {cell}
        return Outcome("SOLVED" if self.solved else "ACCEPTED",
                       "All characters have been proved!" if self.solved else f"{cell} proved {status.value.lower()}; clue revealed.", cell)

    def step(self) -> Outcome:
        analysis = self._analysis()
        if not analysis.consistent:
            return Outcome("INCONSISTENT", "The revealed clues and statuses are inconsistent.")
        if self.solved:
            return Outcome("SOLVED", "All characters have been proved.")
        for cell, status in analysis.verdicts:
            if status != Status.UNKNOWN:
                return self._apply(cell, status, status)
        return Outcome("STALLED", "No forced verdict remains; Auto Solve stopped.")
