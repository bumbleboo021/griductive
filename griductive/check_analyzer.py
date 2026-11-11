"""Small public-state integration checks, not the final experiment suite."""
import argparse
from dataclasses import replace
from griductive.app import ROOT, analyzer_factory
from griductive.domain.models import Clue, Status
from griductive.engine.game import GameEngine
from griductive.engine.puzzle import load_puzzle
from griductive.engine.reference import ReferenceAnalyzer


def check(factory):
    checks = 0
    for size in (3, 4, 5):
        puzzle = load_puzzle(ROOT/f'data/puzzles/{size}x{size}/level_01.json')
        engine = GameEngine(puzzle, factory())
        oracle = ReferenceAnalyzer()
        while not engine.solved:
            state = engine.public_state()
            actual = engine._analysis()  # Also validate the integration boundary.
            expected = oracle.analyze(state)
            if actual != expected:
                raise AssertionError(f'{size}x{size}, reveal {len(state.clues)}: {actual} != {expected}')
            checks += 1
            outcome = engine.step()
            if outcome.code not in ('ACCEPTED', 'SOLVED'):
                raise AssertionError(outcome)
    puzzle = load_puzzle(ROOT/'data/puzzles/3x3/level_01.json')
    base = GameEngine(puzzle, ReferenceAnalyzer()).public_state()
    cases = [(), (Clue('bad', 'FACT', ('A1',), status=Status.CRIMINAL),)]
    for kind in ('SAME', 'DIFFERENT'):
        cases.append((Clue('binary', kind, ('A1','B1')),))
    for kind in ('EXACTLY', 'AT_LEAST', 'AT_MOST'):
        for count in range(3):
            cases.append((Clue('count', kind, ('A1','B1'), count=count),))
    for kind in ('EVEN', 'ODD'):
        cases.append((Clue('parity', kind, ('A1','B1')),))
    analyzer = factory()
    for clues in cases:
        state = replace(base, clues=clues)
        actual, expected = analyzer.analyze(state), ReferenceAnalyzer().analyze(state)
        if actual != expected:
            raise AssertionError(f'{clues}: {actual} != {expected}')
        checks += 1
    return checks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--analyzer', help='module:factory; default is the reference analyzer')
    args = parser.parse_args()
    try:
        count = check(analyzer_factory(args.analyzer))
    except Exception as exc:
        parser.exit(1, f'FAIL: {type(exc).__name__}: {exc}\n')
    print(f'PASS: {count} public-state checks, including progressive reveals on all board sizes.')


if __name__ == '__main__':
    main()
