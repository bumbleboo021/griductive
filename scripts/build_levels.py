"""Rebuild six original project levels from reproducible seeds."""
import json
import random
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from griductive.engine.puzzle import cell_ids, region_cells

ROOT = Path(__file__).resolve().parents[1]


def build(n, variant, seed=None):
    seed = n*100+variant if seed is None else seed
    rng = random.Random(seed)
    ids = cell_ids(n)
    solution = {c: bool(rng.getrandbits(1)) for c in ids}
    # A gentle, geometry-based opening; subsequent regions mix known/unknown cells.
    for c in ids[:n]:
        solution[c] = False
    regions = []
    for i in range(1,n+1):
        regions.append(dict(type='row',index=i))
        regions.append(dict(type='column',label=chr(64+i)))
    for c in ids:
        regions.append(dict(type='neighbors',cell=c))
        for i in range(1,n+1):
            regions.append(dict(type='intersection',regions=[dict(type='neighbors',cell=c),dict(type='row',index=i)]))
    regions = [(r,region_cells(r,n)) for r in regions]
    regions = [(r,c) for r,c in regions if len(c)>=2]
    known = {'A1'}
    frontier = ['A1']
    clues = {}
    plan = []
    while len(known)<len(ids):
        owner = frontier.pop(0)
        choices = []
        for raw,cells in regions:
            unknown = [c for c in cells if c not in known]
            if unknown and len({solution[c] for c in unknown})==1:
                # Exact regional counts saturate the remaining budget.
                choices.append((raw,cells,unknown))
        if owner == 'A1':
            raw = dict(type='row',index=1)
            cells = region_cells(raw,n)
            unknown = [c for c in cells if c not in known]
        elif choices:
            # Variant 2 favors narrow overlaps and longer dependency chains.
            if variant == 2:
                choices.sort(key=lambda x:(len(x[2]),rng.random()))
                raw,cells,unknown = choices[0]
            else:
                raw,cells,unknown = rng.choice(choices)
        else:
            target = rng.choice([c for c in ids if c not in known])
            anchor = rng.choice(sorted(known))
            raw = dict(type='cells',cells=[anchor,target])
            cells = region_cells(raw,n)
            unknown = [target]
        count = sum(solution[c] for c in cells)
        kind = 'EXACTLY'
        if owner != 'A1' and len(unknown)==1 and count%2 and rng.random()<.55:
            kind='ODD'
        elif owner != 'A1' and all(solution[c] for c in unknown) and rng.random()<.4:
            kind='AT_LEAST'
        clue = dict(id=f'clue-{owner}',type=kind,region=raw)
        if kind!='ODD': clue['count']=count
        clues[owner]=clue
        plan.append(dict(owner=owner,forces=unknown))
        known.update(unknown)
        frontier.extend(unknown)
    # Remaining cards still receive true original-style count/parity clues.
    for owner in ids:
        if owner not in clues:
            raw,cells=rng.choice(regions)
            count=sum(solution[c] for c in cells)
            kind='ODD' if count%2 and rng.random()<.5 else 'EXACTLY'
            clues[owner]=dict(id=f'clue-{owner}',type=kind,region=raw)
            if kind!='ODD': clues[owner]['count']=count
    cast=[]
    for path in (ROOT/'assets/images/Character Icons').glob('*.png'):
        name,origin,*_= [x.strip() for x in path.stem.split('\u00b7')]
        cast.append((name,origin))
    cast.sort(key=lambda x:x[0].casefold())
    titles={1:'Quiet Rows',2:'Crossed Testimonies'}
    return dict(name=f'{n}x{n} - {titles[variant]}',title=f'{n}x{n} - {titles[variant]}',size=n,initially_revealed=['A1'],
        metadata=dict(author='Project team with AI assistance',seed=n*100+variant,
                      source='Original project level; not an imported official puzzle',
                      design='Regional counts, overlap deductions and odd parity',construction_plan=plan),
        characters=[dict(cell=c,name=cast[i][0],origin=cast[i][1],
                         status='CRIMINAL' if solution[c] else 'INNOCENT',clue=clues[c])
                    for i,c in enumerate(ids)])


if __name__=='__main__':
    for n in (3,4,5):
        for v in (1,2):
            path=ROOT/f'data/puzzles/{n}x{n}/level_{v:02}.json'
            path.write_text(json.dumps(build(n,v),indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
            print(path.relative_to(ROOT))
    from scripts.polish_levels import polish
    for path in sorted((ROOT/'data/puzzles').glob('*/level_*.json')):
        if int(path.stem[-2:]) <= 2:
            polish(path)
