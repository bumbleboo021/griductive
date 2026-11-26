"""CLI and application composition; headless checks do not import Pygame."""
import argparse
import importlib
from pathlib import Path
from griductive.engine.game import GameEngine
from griductive.engine.puzzle import load_puzzle
from griductive.engine.reference import ReferenceAnalyzer

ROOT = Path(__file__).resolve().parents[1]


def analyzer_factory(spec):
    if not spec:
        return ReferenceAnalyzer
    module, separator, name = spec.partition(':')
    if not separator:
        raise ValueError('Use --analyzer module:factory (a no-argument class or function)')
    factory = getattr(importlib.import_module(module), name)
    if not callable(factory):
        raise ValueError('Analyzer factory must be callable')
    return factory


def main() -> int:
    parser = argparse.ArgumentParser(description='Griductive game and teammate integration harness')
    parser.add_argument('--puzzle', type=Path, default=None,
                        help='Puzzle JSON to open directly (default: start on Home screen with Stage 1)')
    parser.add_argument('--analyzer', help='Teammate analyzer, e.g. griductive.agent.adapter:Agent')
    parser.add_argument('--headless', action='store_true', help='Progressive solving without Pygame')
    parser.add_argument('--screen', choices=('home', 'game'), default=None,
                        help='Initial UI screen (defaults to home unless --puzzle is passed)')
    args = parser.parse_args()
    puzzle_path = args.puzzle or (ROOT / 'data/puzzles/3x3/level_01.json')
    start_screen = args.screen or ('game' if args.puzzle is not None else 'home')
    try:
        factory = analyzer_factory(args.analyzer)
        puzzle = load_puzzle(puzzle_path)
        if args.headless:
            engine = GameEngine(puzzle, factory())
            for step in range(puzzle.size*puzzle.size+1):
                result = engine.step()
                print(f'{step}: {result.code}: {result.message}')
                if result.code != 'ACCEPTED':
                    return 0 if result.code == 'SOLVED' else 1
            return 1
        import pygame
        from griductive.ui.window import GameWindow
        pygame.init()
        try:
            GameWindow(puzzle_path, factory, ROOT / 'data/puzzles',
                       args.analyzer or 'Reference analyzer | development mode',
                       start_screen=start_screen).run()
        finally:
            pygame.quit()
        return 0
    except (ValueError, OSError, ImportError, AttributeError, TimeoutError) as exc:
        parser.exit(1, f'Error: {exc}\n')


if __name__ == '__main__':
    raise SystemExit(main())
