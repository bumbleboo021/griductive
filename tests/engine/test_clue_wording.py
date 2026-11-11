from itertools import product
import pytest
from griductive.engine.puzzle import parse_clue, region_cells
from griductive.engine.reference import possible


def test_regions_are_described_instead_of_enumerated():
    clue=parse_clue(dict(id='r',type='EXACTLY',count=1,target_status='INNOCENT',region=dict(type='column',label='A')),3)
    assert clue.text=='Exactly 1 innocent in column A.'
    assert clue.count==2  # Canonical criminal count for existing encoders.
    assert 'A1' not in clue.text


def test_neighbors_in_multiple_rows():
    region=dict(type='intersection',regions=[dict(type='neighbors',cell='B2'),dict(type='rows',indices=[1,2])])
    cells=region_cells(region,3)
    assert cells==('A1','B1','C1','A2','C2')
    clue=parse_clue(dict(id='n',type='EXACTLY',count=len(cells),target_status='INNOCENT',region=region),3)
    assert clue.text=="All of B2's neighbors in rows 1, 2 are innocent."


@pytest.mark.parametrize('kind',['EXACTLY','AT_LEAST','AT_MOST','ODD','EVEN'])
def test_innocent_counts_keep_their_semantics(kind):
    raw=dict(id='t',type=kind,target_status='INNOCENT',region=dict(type='row',index=1))
    if kind not in ('ODD','EVEN'):
        raw['count']=1
    clue=parse_clue(raw,3)
    for bits in product((False,True),repeat=3):
        count=3-sum(bits)
        expected={'EXACTLY':count==1,'AT_LEAST':count>=1,'AT_MOST':count<=1,'ODD':count%2==1,'EVEN':count%2==0}[kind]
        assert possible(clue,dict(zip(clue.cells,bits)))==expected


def test_quote_has_no_constraint_or_hidden_reference():
    clue=parse_clue(dict(id='q',type='QUOTE'),3)
    assert clue.cells==()
    assert possible(clue,{})
