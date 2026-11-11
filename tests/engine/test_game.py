from dataclasses import FrozenInstanceError, replace
import json
from pathlib import Path
import pytest
from griductive.domain.models import Analysis, Clue, Status
from griductive.engine.game import GameEngine
from griductive.engine.puzzle import load_puzzle, region_cells
from griductive.engine.reference import ReferenceAnalyzer

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def puzzle():
    return load_puzzle(ROOT / 'tests/fixtures/chain_3.json')


def test_public_snapshot_and_reveal(puzzle):
    engine = GameEngine(puzzle, ReferenceAnalyzer())
    before = engine.public_state()
    assert len(before.clues) == len(before.verdicts) == 1
    assert not hasattr(before, 'solution')
    assert not hasattr(before.characters[1], 'status')
    with pytest.raises(FrozenInstanceError):
        before.size = 5
    assert engine.submit_verdict('B1', Status.CRIMINAL).code == 'ACCEPTED'
    after = engine.public_state()
    assert len(after.clues) == len(after.verdicts) == 2
    assert len(before.clues) == 1
    engine.restart()
    assert engine.public_state() == before


@pytest.mark.parametrize(('cell', 'status', 'code'), [
    ('C1', Status.INNOCENT, 'NOT_PROVABLE'),
    ('B1', Status.INNOCENT, 'CONTRADICTED'),
    ('A1', Status.INNOCENT, 'ALREADY_REVEALED'),
])
def test_rejected_verdict_does_not_mutate(puzzle, cell, status, code):
    engine = GameEngine(puzzle, ReferenceAnalyzer())
    before = engine.public_state()
    assert engine.submit_verdict(cell, status).code == code
    assert engine.public_state() == before


def test_hint_does_not_reveal_or_use_hidden_data(puzzle):
    engine = GameEngine(puzzle, ReferenceAnalyzer())
    before = engine.public_state()
    changed = replace(puzzle, solution=puzzle.solution[:1] + tuple(
        (c, Status.INNOCENT) for c, _ in puzzle.solution[1:]),
        clues=puzzle.clues[:1] + tuple(Clue(c.id, 'FACT', ('A1',), status=Status.CRIMINAL)
                                      for c in puzzle.clues[1:]))
    other = GameEngine(changed, ReferenceAnalyzer())
    assert other.public_state() == before
    assert engine.hint() == other.hint()
    assert engine.hint().cell == 'B1'
    assert engine.public_state() == before


@pytest.mark.parametrize('size', [3, 4, 5])
def test_tutorial_solves_in_order(size):
    puzzle = load_puzzle(ROOT / f'tests/fixtures/chain_{size}.json')
    engine = GameEngine(puzzle, ReferenceAnalyzer())
    for char in puzzle.characters[1:]:
        result = engine.step()
        assert result.cell == char.cell
        assert result.code in ('ACCEPTED', 'SOLVED')
    assert engine.solved
    assert engine.step().code == 'SOLVED'


def test_stalled_and_inconsistent(puzzle):
    engine = GameEngine(replace(puzzle, initially_revealed=()), ReferenceAnalyzer())
    assert engine.step().code == 'STALLED'
    bad = replace(puzzle, clues=(Clue('bad', 'FACT', ('A1',), status=Status.CRIMINAL),)+puzzle.clues[1:])
    engine = GameEngine(bad, ReferenceAnalyzer())
    before = engine.public_state()
    assert engine.hint().code == 'INCONSISTENT'
    assert engine.submit_verdict('B1', Status.CRIMINAL).code == 'INCONSISTENT'
    assert engine.step().code == 'INCONSISTENT'
    assert engine.public_state() == before


def test_bad_analyzer_contract_is_rejected(puzzle):
    class Bad:
        def analyze(self, public):
            return Analysis(True, ())
    engine = GameEngine(puzzle, Bad())
    with pytest.raises(ValueError, match='every unresolved'):
        engine.step()
    assert len(engine.public_state().clues) == 1


def test_solver_exception_does_not_mutate(puzzle):
    class Slow:
        def analyze(self, public):
            raise TimeoutError('deadline')
    engine = GameEngine(puzzle, Slow())
    before = engine.public_state()
    with pytest.raises(TimeoutError):
        engine.step()
    assert engine.public_state() == before


@pytest.mark.parametrize('mutation', ['duplicate', 'bad_count', 'unknown', 'bad_initial', 'duplicate_clue', 'unsorted'])
def test_bad_files_rejected(tmp_path, mutation):
    raw = json.loads((ROOT / 'tests/fixtures/chain_3.json').read_text())
    if mutation == 'duplicate':
        raw['characters'][1]['cell'] = 'A1'
    elif mutation == 'bad_count':
        raw['characters'][0]['clue'] = dict(id='bad', type='EXACTLY', cells=['A1'], count=True)
    elif mutation == 'unknown':
        raw['characters'][0]['status'] = 'UNKNOWN'
    elif mutation == 'bad_initial':
        raw['initially_revealed'] = ['Z9']
    elif mutation == 'duplicate_clue':
        raw['characters'][1]['clue']['id'] = 'clue-A1'
    else:
        raw['characters'][0]['name'] = 'Zoe'
    path = tmp_path / 'bad.json'
    path.write_text(json.dumps(raw))
    with pytest.raises(ValueError):
        load_puzzle(path)


def test_regions():
    assert region_cells(dict(type='neighbors', cell='A1'), 3) == ('B1','A2','B2')
    assert len(region_cells(dict(type='neighbors', cell='B2'), 3)) == 8
    assert region_cells(dict(type='intersection', regions=[dict(type='row',index=2),dict(type='column',label='B')]),3) == ('B2',)
    with pytest.raises(ValueError):
        region_cells(dict(type='cells', cells=['A1','A1']), 3)


def test_stage_name_field_overrides_legacy_title(tmp_path):
    raw=json.loads((ROOT/'tests/fixtures/chain_3.json').read_text())
    raw['name']='A named stage'
    raw.pop('title',None)
    path=tmp_path/'stage.json'
    path.write_text(json.dumps(raw),encoding='utf-8')
    assert load_puzzle(path).title=='A named stage'
