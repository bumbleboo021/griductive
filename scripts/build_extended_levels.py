"""Construct seven extra stages with all six requested clue families."""
import itertools
import json
import random
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.build_levels import build, ROOT, stage_name
from griductive.engine.puzzle import cell_ids,region_cells
from scripts.validate_levels import validate


def direction_to(target,known,size):
    for anchor in sorted(known):
        for direction in ('above','below','left','right'):
            raw=dict(type='direction',cell=anchor,direction=direction)
            try:
                if region_cells(raw,size)==(target,):
                    return raw
            except ValueError:
                pass
    return dict(type='cells',cells=[target])


def make(size,number,seed):
    raw=build(size,1,seed=seed)
    rng=random.Random(seed)
    ids=cell_ids(size)
    solution={card['cell']:card['status']=='CRIMINAL' for card in raw['characters']}
    last=f'{chr(64+size)}1'
    known={'A1',last}
    frontier=['A1',last]
    regions=[dict(type='grid'),dict(type='boundary'),dict(type='corners')]
    for i in range(1,size+1):
        regions.extend([dict(type='row',index=i),dict(type='column',label=chr(64+i))])
    for cell in ids:
        regions.append(dict(type='neighbors',cell=cell))
        for i in range(1,size+1):
            regions.append(dict(type='intersection',regions=[dict(type='neighbors',cell=cell),dict(type='row',index=i)]))
    for first,second in itertools.combinations(ids,2):
        regions.append(dict(type='common_neighbors',cells=[first,second]))
    expanded=[(r,region_cells(r,size)) for r in regions]
    expanded=[(r,cells) for r,cells in expanded if len(cells)>=2]
    clues={}
    schedule=['CONNECTED','FACT','COUNT_COMPARE','IMPLIES','EVEN','EXACTLY','ODD']
    extras=itertools.cycle(['SAME','AT_LEAST','DIFFERENT','COUNT_COMPARE','AT_MOST','ODD','EXACTLY'])
    step=0
    while len(known)<len(ids):
        owner=frontier.pop(0)
        kind=schedule[step] if step<len(schedule) else next(extras)
        unknown=[cell for cell in ids if cell not in known]
        target=rng.choice(unknown)
        new=[target]
        if kind=='CONNECTED':
            clue=dict(type=kind,target_status='INNOCENT',region=dict(type='row',index=1))
            new=[c for c in ids[:size] if c not in known]
        elif kind=='FACT':
            clue=dict(type=kind,status='CRIMINAL' if solution[target] else 'INNOCENT',region=direction_to(target,known,size))
        elif kind=='COUNT_COMPARE':
            choices=[]
            for left,left_cells in expanded:
                remaining=[c for c in left_cells if c not in known]
                if len(remaining)!=1 or left['type']!='neighbors':
                    continue
                base=sum(solution[c] for c in left_cells if c in known)
                for right,right_cells in expanded:
                    if not set(right_cells)<=known:
                        continue
                    right_count=sum(solution[c] for c in right_cells)
                    if right_count==base:
                        choices.append((left,right,remaining,'GT' if solution[remaining[0]] else 'EQ'))
                    elif right_count==base+1 and not solution[remaining[0]]:
                        choices.append((left,right,remaining,'LT'))
            if choices:
                left,right,new,operator=rng.choice(choices)
                clue=dict(type=kind,region=left,other_region=right,operator=operator)
            else:
                clue=dict(type=kind,region=direction_to(target,known,size),other_region=dict(type='row',index=1),operator='GT' if solution[target] else 'EQ')
        elif kind=='IMPLIES':
            anchor=rng.choice(sorted(known))
            clue=dict(type=kind,**{'if':dict(cell=anchor,status='CRIMINAL' if solution[anchor] else 'INNOCENT'),
                                 'then':dict(cell=target,status='CRIMINAL' if solution[target] else 'INNOCENT')})
        elif kind in ('SAME','DIFFERENT'):
            anchors=[c for c in known if (solution[c]==solution[target])==(kind=='SAME')]
            if not anchors:
                kind='SAME' if kind=='DIFFERENT' else 'DIFFERENT'
                anchors=list(known)
            clue=dict(type=kind,cells=[rng.choice(sorted(anchors)),target])
        else:
            candidates=[]
            for region,cells in expanded:
                remaining=[c for c in cells if c not in known]
                if len(remaining)!=1:
                    continue
                count=sum(solution[c] for c in cells)
                if kind=='ODD' and count%2!=1:
                    continue
                if kind=='EVEN' and (count%2!=0 or region['type']!='common_neighbors'):
                    continue
                if kind=='AT_LEAST' and not solution[remaining[0]]:
                    continue
                if kind=='AT_MOST' and solution[remaining[0]]:
                    continue
                candidates.append((region,cells,remaining,count))
            if not candidates:
                raise ValueError('Retry seed for geometry/parity coverage')
            region,cells,new,count=rng.choice(candidates)
            # Final count can refer to the entire grid or a named origin group.
            if len(unknown)==1:
                kind='EXACTLY'
                if size==5 and number==5:
                    origin=next(c['origin'] for c in raw['characters'] if c['cell']==new[0])
                    cells=tuple(c['cell'] for c in raw['characters'] if c['origin']==origin)
                    region=dict(type='group',label=f'characters from {origin}',cells=list(cells))
                    raw['fixed_cast']=True
                else:
                    region=dict(type='boundary') if new[0] in region_cells(dict(type='boundary'),size) else dict(type='grid')
                    cells=region_cells(region,size)
                count=sum(solution[c] for c in cells)
            clue=dict(type=kind,region=region)
            if kind in ('EXACTLY','AT_LEAST','AT_MOST'):
                clue['count']=count
                if step%2 and kind=='EXACTLY':
                    clue['target_status']='INNOCENT'
                    clue['count']=len(cells)-count
        clues[owner]=dict(id=f'clue-{owner}',**clue)
        known.update(new)
        frontier.extend(new)
        step+=1
    for card in raw['characters']:
        card['clue']=clues.get(card['cell'],dict(id='clue-'+card['cell'],type='QUOTE'))
    raw['name']=raw['title']=stage_name(size, number)
    raw['initially_revealed']=['A1',last]
    raw['metadata']=dict(seed=seed,author='Project team with AI assistance',
        design='Connectivity opening, direct spatial identity, comparisons, implication, shared-neighbor parity and regional budgets',
        quote_cells=[c['cell'] for c in raw['characters'] if c['clue']['type']=='QUOTE'])
    return raw


def generate():
    temporary=ROOT/'.cache/extended-stage.json'
    temporary.parent.mkdir(exist_ok=True)
    for size,numbers in ((3,(3,4)),(4,(3,4)),(5,(3,4,5))):
        for number in numbers:
            for attempt in range(200):
                seed=size*10000+number*100+attempt
                try:
                    raw=make(size,number,seed)
                    temporary.write_text(json.dumps(raw,ensure_ascii=False),encoding='utf-8')
                    validate(temporary,timeout=10)
                except (ValueError,TimeoutError):
                    continue
                path=ROOT/f'data/puzzles/{size}x{size}/level_{number:02}.json'
                path.write_text(json.dumps(raw,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
                from scripts.polish_levels import polish
                polish(path)
                print(f'Created {path.relative_to(ROOT)} (seed {seed})',flush=True)
                break
            else:
                raise RuntimeError(f'Could not generate validated {size}x{size} stage {number}')


if __name__=='__main__':
    generate()
