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
        deadline = monotonic() + self.timeout
        fixed = {c: s == Status.CRIMINAL for c, s in state.verdicts}
        cells = [c.cell for c in state.characters if c.cell not in fixed]

        def satisfiable(extra):
            values = dict(fixed)
            values.update(extra)

            def visit():
                if monotonic() > deadline:
                    raise TimeoutError("Reference analyzer timed out; connect the team's DPLL agent.")
                if not all(possible(clue, values) for clue in state.clues):
                    return False
                cell = next((c for c in cells if c not in values), None)
                if cell is None:
                    return True
                for value in (False, True):
                    values[cell] = value
                    if visit():
                        del values[cell]
                        return True
                del values[cell]
                return False
            return visit()

        if not satisfiable({}):
            return Analysis(False, ())
        verdicts = []
        for cell in cells:
            innocent = satisfiable({cell: False})
            criminal = satisfiable({cell: True})
            status = Status.UNKNOWN if innocent and criminal else (
                Status.CRIMINAL if criminal else Status.INNOCENT)
            verdicts.append((cell, status))
        return Analysis(True, tuple(verdicts))
