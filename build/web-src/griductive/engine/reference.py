"""Temporary semantic backtracking analyzer, NOT the assessed CNF/DPLL agent.

Uses public data only. Replace via --analyzer module:factory. Timeout raises;
it never turns an incomplete search into a verdict or UNKNOWN.
"""
from time import monotonic
from griductive.domain.models import Analysis, PublicState, Status
from griductive.engine.advanced_clues import advanced_possible


def possible(clue, values):
    if clue.kind in ('COUNT_COMPARE','CONNECTED','IMPLIES'):
        return advanced_possible(clue,values)
    if clue.kind == 'QUOTE':
        return True
    known = [values[c] for c in clue.cells if c in values]
    missing = len(clue.cells) - len(known)
    total = sum(known)
    if clue.kind == "FACT":
        return not known or known[0] == (clue.status == Status.CRIMINAL)
    if clue.kind == "SAME":
        return len(set(known)) <= 1
    if clue.kind == "DIFFERENT":
        return missing > 0 or total == 1
    if clue.kind == "EXACTLY":
        return total <= clue.count <= total + missing
    if clue.kind == "AT_LEAST":
        return total + missing >= clue.count
    if clue.kind == "AT_MOST":
        return total <= clue.count
    if clue.kind in ("EVEN", "ODD"):
        return missing > 0 or total % 2 == (clue.kind == "ODD")
    raise ValueError(f"Unsupported clue: {clue.kind}")


class ReferenceAnalyzer:
    def __init__(self, timeout=3.0):
        self.timeout = timeout

    def analyze(self, state: PublicState) -> Analysis:
        steps = self.analyze_steps(state)
        while True:
            try:
                next(steps)
            except StopIteration as finished:
                return finished.value

    def analyze_steps(self, state: PublicState):
        """Yield regularly so a browser can render during semantic search."""
        deadline = monotonic() + self.timeout
        visits = 0
        fixed = {c: s == Status.CRIMINAL for c, s in state.verdicts}
        cells = [c.cell for c in state.characters if c.cell not in fixed]

        def satisfiable(extra):
            values = dict(fixed)
            values.update(extra)

            def visit():
                nonlocal visits
                visits += 1
                if visits % 128 == 0:
                    yield
                if monotonic() > deadline:
                    raise TimeoutError("Reference analyzer timed out; connect the team's DPLL agent.")
                if not all(possible(clue, values) for clue in state.clues):
                    return False
                cell = next((c for c in cells if c not in values), None)
                if cell is None:
                    return True
                for value in (False, True):
                    values[cell] = value
                    if (yield from visit()):
                        del values[cell]
                        return True
                del values[cell]
                return False
            return (yield from visit())

        if not (yield from satisfiable({})):
            return Analysis(False, ())
        verdicts = []
        for cell in cells:
            innocent = yield from satisfiable({cell: False})
            criminal = yield from satisfiable({cell: True})
            status = Status.UNKNOWN if innocent and criminal else (
                Status.CRIMINAL if criminal else Status.INNOCENT)
            verdicts.append((cell, status))
        return Analysis(True, tuple(verdicts))
