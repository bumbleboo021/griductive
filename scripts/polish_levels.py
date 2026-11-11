"""Prefer natural innocent/criminal wording and replace safely redundant clues."""
import copy
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.validate_levels import ROOT,validate


def polish(path):
    raw=json.loads(path.read_text(encoding='utf-8'))
    # Express selected counts in terms of innocents, preserving their exact logic.
    from griductive.engine.puzzle import region_cells
    for i,card in enumerate(raw['characters']):
        clue=card['clue']
        if clue['type']=='EXACTLY' and i%2==0 and clue.get('target_status','CRIMINAL')=='CRIMINAL':
            clue['count']=len(region_cells(clue['region'],raw['size']))-clue['count']
            clue['target_status']='INNOCENT'
    temp=ROOT/'.cache/prune-candidate.json'
    removed=[]
    # Hidden cards first, then initial cards. Each accepted removal is revalidated.
    order=sorted(range(len(raw['characters'])),key=lambda i:raw['characters'][i]['cell'] in raw['initially_revealed'])
    for i in order:
        old=raw['characters'][i]['clue']
        if old['type']=='QUOTE':
            continue
        raw['characters'][i]['clue']=dict(id=old['id'],type='QUOTE')
        temp.write_text(json.dumps(raw,ensure_ascii=False),encoding='utf-8')
        try:
            validate(temp,timeout=3)
        except (ValueError,TimeoutError):
            raw['characters'][i]['clue']=old
        else:
            removed.append(raw['characters'][i]['cell'])
    metadata=raw.setdefault('metadata',{})
    if 'construction_plan' in metadata:
        metadata['pre_pruning_construction_plan']=metadata.pop('construction_plan')
    metadata['quote_cells']=[c['cell'] for c in raw['characters'] if c['clue']['type']=='QUOTE']
    path.write_text(json.dumps(raw,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    validate(path)
    print(f'{path.relative_to(ROOT)}: {len(metadata["quote_cells"])} quote cards',flush=True)


if __name__=='__main__':
    for path in sorted((ROOT/'data/puzzles').glob('*/level_*.json')):
        polish(path)
