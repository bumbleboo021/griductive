"""Regression checks for the six original levels and offline validator."""
import json
from pathlib import Path
import pytest
from scripts.validate_levels import validate

ROOT=Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(('size','variant'),[(n,v) for n in (3,4,5) for v in range(1,6 if n==5 else 5)])
def test_original_levels(size,variant):
    result=validate(ROOT/f'data/puzzles/{size}x{size}/level_{variant:02}.json')
    assert result['unique'] and result['all_clues_true'] and result['progressively_solvable']
    assert result['steps']==size*size-len(result['initial_reveals'])
    if variant<=2:
        assert 'FACT' not in result['clue_types']
    else:
        assert {'CONNECTED','COUNT_COMPARE','IMPLIES','EXACTLY'}<=result['clue_types'].keys()
        assert {'ODD','EVEN'} & result['clue_types'].keys()


@pytest.mark.parametrize('problem',['false','ambiguous','stalled'])
def test_validator_rejects_bad_levels(tmp_path,problem):
    raw=json.loads((ROOT/'tests/fixtures/chain_3.json').read_text())
    for card in raw['characters']:
        if problem=='stalled':
            card['clue']=dict(id='clue-'+card['cell'],type='FACT',cells=[card['cell']],status=card['status'])
        else:
            card['clue']=dict(id='clue-'+card['cell'],type='AT_LEAST',count=0,region=dict(type='row',index=1))
    if problem=='false':
        raw['characters'][0]['clue']=dict(id='false',type='FACT',cells=['A1'],status='CRIMINAL')
    path=tmp_path/'bad.json'
    path.write_text(json.dumps(raw),encoding='utf-8')
    expected={'false':'false under','ambiguous':'Expected one','stalled':'STALLED'}[problem]
    with pytest.raises(ValueError,match=expected):
        validate(path)


def test_origin_group_stage_keeps_its_cast():
    from griductive.engine.puzzle import load_puzzle
    from griductive.ui.assets import Artwork
    puzzle=load_puzzle(ROOT/'data/puzzles/5x5/level_05.json')
    assert puzzle.fixed_cast
    assert Artwork().cast_puzzle(puzzle) is puzzle
    raw=json.loads((ROOT/'data/puzzles/5x5/level_05.json').read_text())
    groups=[c['clue']['region'] for c in raw['characters'] if c['clue'].get('region',{}).get('type')=='group']
    assert groups
    liyue={c.cell for c in puzzle.characters if c.origin=='Liyue'}
    assert set(groups[0]['cells'])==liyue
