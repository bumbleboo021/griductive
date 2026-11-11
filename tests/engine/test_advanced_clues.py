"""Exhaustive small-region checks against complete-assignment truth oracles."""
from itertools import product
import pytest
from griductive.domain.models import Status
from griductive.engine.puzzle import parse_clue,region_cells
from griductive.engine.reference import possible
from scripts.validate_levels import compatible


def full_truth(clue,values):
    if clue.kind=='IMPLIES':
        return values[clue.cells[0]]!=(clue.antecedent_status==Status.CRIMINAL) or values[clue.cells[1]]==(clue.consequent_status==Status.CRIMINAL)
    target=clue.target_status==Status.CRIMINAL
    if clue.kind=='COUNT_COMPARE':
        first=sum(values[c]==target for c in clue.cells)
        second=sum(values[c]==target for c in clue.other_cells)
        return {'GT':first>second,'LT':first<second,'EQ':first==second}[clue.operator]
    chosen={c for c in clue.cells if values[c]==target}
    if not chosen:
        return True
    todo=[chosen.pop()]
    while todo:
        a=todo.pop()
        adjacent={b for b in chosen if abs(ord(a[0])-ord(b[0]))+abs(int(a[1:])-int(b[1:]))==1}
        chosen-=adjacent
        todo.extend(adjacent)
    return not chosen


CASES=[dict(id='i',type='IMPLIES',**{'if':dict(cell='B1',status='CRIMINAL'),'then':dict(cell='A1',status='INNOCENT')})]
for target in ('CRIMINAL','INNOCENT'):
    CASES.append(dict(id='c',type='CONNECTED',target_status=target,region=dict(type='cells',cells=['A1','B1','A2','B2'])))
    for operator in ('GT','LT','EQ'):
        CASES.append(dict(id='p',type='COUNT_COMPARE',target_status=target,operator=operator,
                          region=dict(type='row',index=1),other_region=dict(type='column',label='A')))


@pytest.mark.parametrize('raw',CASES)
def test_extended_clues_match_all_partial_completions(raw):
    clue=parse_clue(raw,3)
    cells=clue.referenced_cells
    for values in product((None,False,True),repeat=len(cells)):
        partial={c:v for c,v in zip(cells,values) if v is not None}
        missing=[c for c in cells if c not in partial]
        expected=any(full_truth(clue,partial|dict(zip(missing,completion)))
                     for completion in product((False,True),repeat=len(missing)))
        assert possible(clue,partial)==expected
        assert compatible(clue,partial)==expected


def test_extended_regions():
    assert region_cells(dict(type='common_neighbors',cells=['A1','C1']),3)==('B1','B2')
    assert region_cells(dict(type='direction',cell='B2',direction='above'),3)==('B1',)
    assert len(region_cells(dict(type='boundary'),5))==16
    assert len(region_cells(dict(type='corners'),5))==4
    assert len(region_cells(dict(type='grid'),5))==25
    with pytest.raises(ValueError):
        region_cells(dict(type='direction',cell='A1',direction='above'),3)


def test_condition_preserves_premise_order_and_connectivity_excludes_diagonals():
    clue=parse_clue(CASES[0],3)
    assert clue.cells==('B1','A1')
    connected=parse_clue(dict(id='c',type='CONNECTED',region=dict(type='cells',cells=['A1','B2'])),3)
    assert not possible(connected,{'A1':True,'B2':True})
