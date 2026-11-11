"""Offline semantic validation; does not implement the assessed CNF/DPLL solver."""
import argparse
import json
from collections import Counter
from pathlib import Path
import sys
from time import monotonic
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from griductive.domain.models import Status
from griductive.engine.puzzle import load_puzzle
from griductive.engine.game import GameEngine
from griductive.engine.reference import ReferenceAnalyzer

ROOT = Path(__file__).resolve().parents[1]


def compatible(clue, assignment):
    """Independent direct semantics, pruning partial assignments conservatively."""
    if clue.kind == 'QUOTE':
        return True
    if clue.kind == 'IMPLIES':
        first,second = clue.cells
        if first not in assignment or second not in assignment:
            return True
        return (assignment[first] != (clue.antecedent_status == Status.CRIMINAL) or
                assignment[second] == (clue.consequent_status == Status.CRIMINAL))
    if clue.kind == 'COUNT_COMPARE':
        desired = clue.target_status == Status.CRIMINAL
        known_difference = 0
        low_delta = high_delta = 0
        for cell in clue.referenced_cells:
            weight = (1 if cell in clue.cells else 0)-(1 if cell in clue.other_cells else 0)
            if cell in assignment:
                known_difference += weight*int(assignment[cell] == desired)
            else:
                low_delta += min(0,weight)
                high_delta += max(0,weight)
        if clue.operator == 'GT':
            return known_difference+high_delta>0
        if clue.operator == 'LT':
            return known_difference+low_delta<0
        return known_difference+low_delta<=0<=known_difference+high_delta
    if clue.kind == 'CONNECTED':
        target = clue.target_status == Status.CRIMINAL
        fixed = [c for c in clue.cells if c in assignment and assignment[c] == target]
        if not fixed:
            return True
        candidates = {c for c in clue.cells if c not in assignment or assignment[c] == target}
        component = {fixed[0]}
        while True:
            extensions = {b for a in component for b in candidates-component
                          if abs(ord(a[0])-ord(b[0]))+abs(int(a[1:])-int(b[1:])) == 1}
            if not extensions:
                break
            component.update(extensions)
        return all(c in component for c in fixed)
    values = [assignment[c] for c in clue.cells if c in assignment]
    remaining = len(clue.cells)-len(values)
    count = sum(values)
    if clue.kind == 'FACT':
        return not values or values[0] == (clue.status == Status.CRIMINAL)
    if clue.kind == 'SAME':
        return len(set(values))<=1
    if clue.kind == 'DIFFERENT':
        return remaining>0 or count==1
    if clue.kind == 'EXACTLY':
        return count<=clue.count<=count+remaining
    if clue.kind == 'AT_LEAST':
        return count+remaining>=clue.count
    if clue.kind == 'AT_MOST':
        return count<=clue.count
    if clue.kind in ('ODD','EVEN'):
        return remaining>0 or count%2==int(clue.kind=='ODD')
    raise ValueError(f'Unsupported clue {clue.kind}')


def validate(path, timeout=15):
    started=monotonic()
    puzzle=load_puzzle(path)
    solution={c:s==Status.CRIMINAL for c,s in puzzle.solution}
    for clue in puzzle.clues:
        if not compatible(clue,solution):
            raise ValueError(f'{clue.id} is false under the stored solution')
    # Enumerate at most two full-clue models, independently of public analysis.
    assignment={c:solution[c] for c in puzzle.initially_revealed}
    cells=[c.cell for c in puzzle.characters if c.cell not in assignment]
    models=[]
    def search():
        if monotonic()-started>timeout:
            raise TimeoutError('Uniqueness validation timed out')
        if not all(compatible(clue,assignment) for clue in puzzle.clues):
            return
        cell=next((c for c in cells if c not in assignment),None)
        if cell is None:
            models.append(dict(assignment))
            return
        for value in (False,True):
            assignment[cell]=value
            search()
            if len(models)>=2:
                break
        del assignment[cell]
    search()
    if len(models)!=1 or models[0]!=solution:
        raise ValueError(f'Expected one matching solution; found {len(models)} (search capped at 2)')
    engine=GameEngine(puzzle,ReferenceAnalyzer(timeout=3))
    trace=[]
    while not engine.solved:
        if monotonic()-started>timeout:
            raise TimeoutError('Progressive validation timed out')
        before=engine.public_state()
        result=engine.step()
        if result.code not in ('ACCEPTED','SOLVED'):
            raise ValueError(f'Progressive solve stopped: {result.code}')
        after=engine.public_state()
        trace.append(dict(step=len(trace)+1,cell=result.cell,
                          verdict=dict(after.verdicts)[result.cell].value,
                          active_clues=[c.id for c in before.clues],
                          revealed_clue=next(c.id for c in after.clues if c not in before.clues)))
    resolved = Path(path).resolve()
    report_path = resolved.relative_to(ROOT) if resolved.is_relative_to(ROOT) else resolved
    return dict(path=str(report_path),size=puzzle.size,
                all_clues_true=True,unique=True,progressively_solvable=True,
                initial_reveals=list(puzzle.initially_revealed),steps=len(trace),
                clue_types=dict(Counter(c.kind for c in puzzle.clues)),
                region_types=dict(Counter(c['clue'].get('region',{}).get('type','cells')
                                          for c in json.loads(Path(path).read_text(encoding='utf-8'))['characters'])),
                trace=trace)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('paths',nargs='*',type=Path)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    paths=args.paths or sorted((ROOT/'data/puzzles').glob('*/level_*.json'))
    reports=[]
    for path in paths:
        try:
            report=validate(path.resolve())
        except Exception as exc:
            parser.exit(1,f'FAIL {path}: {exc}\n')
        reports.append(report)
        print(f"PASS {report['path']}: true clues, unique solution, {report['steps']} proved reveals")
    if args.output:
        args.output.write_text(json.dumps(reports,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':
    main()
