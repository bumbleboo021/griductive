"""Partial semantic checks for the development analyzer's extended clues."""
from griductive.domain.models import Status


def advanced_possible(clue, values):
    if clue.kind == 'IMPLIES':
        first,second = clue.cells
        premise = clue.antecedent_status == Status.CRIMINAL
        conclusion = clue.consequent_status == Status.CRIMINAL
        return not (first in values and values[first] == premise and
                    second in values and values[second] != conclusion)
    if clue.kind == 'COUNT_COMPARE':
        target = clue.target_status == Status.CRIMINAL
        weights = {cell:int(cell in clue.cells)-int(cell in clue.other_cells)
                   for cell in clue.referenced_cells}
        base = sum(weight for cell,weight in weights.items() if cell in values and values[cell] == target)
        lower = base+sum(min(0,weight) for cell,weight in weights.items() if cell not in values)
        upper = base+sum(max(0,weight) for cell,weight in weights.items() if cell not in values)
        return {'GT':upper>0,'LT':lower<0,'EQ':lower<=0<=upper}[clue.operator]
    if clue.kind == 'CONNECTED':
        target = clue.target_status == Status.CRIMINAL
        required = {cell for cell in clue.cells if cell in values and values[cell] == target}
        if len(required)<2:
            return True
        allowed = {cell for cell in clue.cells if cell not in values or values[cell] == target}
        reached = {next(iter(required))}
        pending = list(reached)
        while pending:
            cell = pending.pop()
            adjacent = {other for other in allowed-reached
                        if abs(ord(other[0])-ord(cell[0]))+abs(int(other[1:])-int(cell[1:])) == 1}
            reached.update(adjacent)
            pending.extend(adjacent)
        return required <= reached
    raise ValueError(f'Unsupported extended clue {clue.kind}')
