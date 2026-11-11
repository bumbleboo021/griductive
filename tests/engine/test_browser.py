"""Browser search preserves public deductions and yields during CPU work."""
import asyncio
from pathlib import Path
import pytest
from griductive.engine.browser import BrowserAnalyzer
from griductive.engine.game import GameEngine
from griductive.engine.puzzle import load_puzzle
from griductive.engine.reference import ReferenceAnalyzer

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize('path', sorted((ROOT/'data/puzzles').rglob('*.json')),
                         ids=lambda path: f'{path.parent.name}/{path.stem}')
def test_browser_solves_each_stage_using_public_snapshots(path):
    async def run():
        analyzer = BrowserAnalyzer()
        engine = GameEngine(load_puzzle(path), analyzer)
        while not engine.solved:
            state = engine.public_state()
            await engine.prepare_analysis()
            assert analyzer.analyze(state) == ReferenceAnalyzer().analyze(state)
            assert engine.step().code in ('ACCEPTED', 'SOLVED')
        engine.restart()
        await engine.prepare_analysis()
        assert engine.step().code == 'ACCEPTED'
    asyncio.run(run())


def test_browser_analysis_yields_and_rejects_unprepared_state():
    async def run():
        analyzer = BrowserAnalyzer()
        engine = GameEngine(load_puzzle(ROOT/'data/puzzles/5x5/level_01.json'), analyzer)
        with pytest.raises(RuntimeError, match='prepared'):
            analyzer.analyze(engine.public_state())
        task = asyncio.create_task(engine.prepare_analysis())
        await asyncio.sleep(0)
        assert not task.done()
        await task
        assert analyzer.analyze(engine.public_state()).consistent
    asyncio.run(run())
