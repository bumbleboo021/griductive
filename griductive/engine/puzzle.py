"""Strict puzzle loading. Private puzzle objects are never sent to analyzers."""
import json
from dataclasses import dataclass
from pathlib import Path

from griductive.domain.models import Character, Clue, Status


@dataclass(frozen=True)
class Puzzle:
    title: str
    size: int
    characters: tuple[Character, ...]
    solution: tuple[tuple[str, Status], ...]
    clues: tuple[Clue, ...]
    initially_revealed: tuple[str, ...]
    fixed_cast: bool = False


def cell_ids(size: int) -> tuple[str, ...]:
    return tuple(f"{chr(65+c)}{r+1}" for r in range(size) for c in range(size))


def region_cells(region: dict, size: int) -> tuple[str, ...]:
    if not isinstance(region, dict):
        raise ValueError("Region must be an object")
    ids = cell_ids(size)
    kind = region.get("type")
    if kind == 'grid':
        cells = list(ids)
    elif kind in ('boundary','corners'):
        cells = [c for c in ids if (c[0] in ('A',chr(64+size)) and int(c[1:]) in (1,size))
                 or (kind == 'boundary' and (c[0] in ('A',chr(64+size)) or int(c[1:]) in (1,size)))]
    elif kind == 'common_neighbors':
        centers = region.get('cells')
        if not isinstance(centers,list) or len(centers)!=2 or centers[0]==centers[1]:
            raise ValueError('Common neighbors requires two distinct cells')
        first = set(region_cells(dict(type='neighbors',cell=centers[0]),size))
        second = set(region_cells(dict(type='neighbors',cell=centers[1]),size))
        cells = [c for c in ids if c in first & second and c not in centers]
    elif kind == 'direction':
        center = region.get('cell')
        direction = region.get('direction')
        offsets = {'above':(0,-1),'below':(0,1),'left':(-1,0),'right':(1,0)}
        if center not in ids or direction not in offsets:
            raise ValueError('Invalid directional region')
        dx,dy = offsets[direction]
        candidate = f'{chr(ord(center[0])+dx)}{int(center[1:])+dy}'
        if candidate not in ids:
            raise ValueError('Directional region goes outside board')
        cells = [candidate]
    elif kind in ('rows', 'columns'):
        key = 'indices' if kind == 'rows' else 'labels'
        items = region.get(key)
        if not isinstance(items,list) or not items or len(set(items)) != len(items):
            raise ValueError('Provide distinct row indices or column labels')
        selected = set()
        for item in items:
            selected.update(region_cells(dict(type='row',index=item) if kind=='rows' else dict(type='column',label=item),size))
        cells = [c for c in ids if c in selected]
    elif kind == "row":
        index = region.get("index")
        if type(index) is not int or not 1 <= index <= size:
            raise ValueError("Invalid row index")
        cells = [x for x in ids if int(x[1:]) == index]
    elif kind == "column":
        label = region.get("label")
        if label not in [chr(65+c) for c in range(size)]:
            raise ValueError("Invalid column label")
        cells = [x for x in ids if x[0] == label]
    elif kind == "neighbors":
        center = region.get("cell")
        if center not in ids:
            raise ValueError("Invalid neighbor center")
        cells = [x for x in ids if x != center and
                 abs(ord(x[0])-ord(center[0])) <= 1 and
                 abs(int(x[1:])-int(center[1:])) <= 1]
    elif kind == "intersection":
        parts = region.get("regions")
        if not isinstance(parts, list) or len(parts) < 2:
            raise ValueError("Intersection needs at least two regions")
        selected = set(ids)
        for part in parts:
            selected.intersection_update(region_cells(part, size))
        cells = [x for x in ids if x in selected]
    elif kind in ('cells','group'):
        if kind == 'group' and (not isinstance(region.get('label'),str) or not region['label'].strip()):
            raise ValueError('Named group needs a label')
        cells = region.get("cells")
        if not isinstance(cells, list) or any(not isinstance(x, str) for x in cells):
            raise ValueError("Explicit region needs a list of cell IDs")
    else:
        raise ValueError(f"Unsupported region: {kind}")
    if len(set(cells)) != len(cells) or any(x not in ids for x in cells):
        raise ValueError("Region contains duplicate or invalid cells")
    return tuple(x for x in ids if x in cells)


def describe_region(region):
    kind = region['type']
    if kind == 'grid':
        return 'the entire grid'
    if kind == 'boundary':
        return 'the boundary (including corners)'
    if kind == 'corners':
        return 'the four corners'
    if kind == 'common_neighbors':
        return f"the shared neighbors of {region['cells'][0]} and {region['cells'][1]}"
    if kind == 'direction':
        return f"the cell directly {region['direction']} {region['cell']}"
    if kind == 'group':
        return region['label']
    if kind == 'row':
        return f"row {region['index']}"
    if kind == 'column':
        return f"column {region['label']}"
    if kind == 'rows':
        return 'rows '+', '.join(map(str,region['indices']))
    if kind == 'columns':
        return 'columns '+', '.join(region['labels'])
    if kind == 'neighbors':
        return f"{region['cell']}'s neighbors"
    if kind == 'intersection':
        parts = region['regions']
        neighbors = [r for r in parts if r['type']=='neighbors']
        if len(neighbors)==1:
            rest = [describe_region(r) for r in parts if r is not neighbors[0]]
            return describe_region(neighbors[0])+' in '+' and '.join(rest)
        return 'the intersection of '+' and '.join(describe_region(r) for r in parts)
    return ', '.join(region['cells']) or 'the empty region'


def parse_clue(raw: dict, size: int) -> Clue:
    if not isinstance(raw, dict) or not isinstance(raw.get("id"), str) or not raw["id"].strip():
        raise ValueError("Each clue needs a nonempty string ID")
    kind = raw.get("type")
    if kind == 'QUOTE':
        return Clue(raw['id'], 'QUOTE', ())
    if kind == 'IMPLIES':
        literals = [raw.get('if'),raw.get('then')]
        if any(not isinstance(item,dict) or item.get('cell') not in cell_ids(size) for item in literals):
            raise ValueError('Conditional requires valid if and then cells')
        statuses = [Status(item.get('status')) for item in literals]
        if Status.UNKNOWN in statuses:
            raise ValueError('Conditional statuses cannot be UNKNOWN')
        return Clue(raw['id'],kind,tuple(item['cell'] for item in literals),
                    antecedent_status=statuses[0],consequent_status=statuses[1])
    if kind in ('COUNT_COMPARE','CONNECTED'):
        region = raw.get('region')
        cells = region_cells(region,size)
        target = Status(raw.get('target_status','CRIMINAL'))
        if target == Status.UNKNOWN:
            raise ValueError('Target cannot be UNKNOWN')
        if kind == 'CONNECTED':
            return Clue(raw['id'],kind,cells,region_label=describe_region(region),target_status=target)
        other = raw.get('other_region')
        other_cells = region_cells(other,size)
        operator = raw.get('operator','GT')
        if operator not in ('GT','LT','EQ'):
            raise ValueError('Comparison operator must be GT, LT or EQ')
        return Clue(raw['id'],kind,cells,region_label=describe_region(region),target_status=target,
                    other_cells=other_cells,other_region_label=describe_region(other),operator=operator)
    if kind not in ("FACT", "SAME", "DIFFERENT", "EXACTLY", "AT_LEAST", "AT_MOST", "EVEN", "ODD"):
        raise ValueError(f"Unsupported clue type: {kind}")
    region = raw.get("region", {"type": "cells", "cells": raw.get("cells")})
    cells = region_cells(region, size)
    count, status = None, None
    if kind in ("FACT", "SAME", "DIFFERENT"):
        if len(cells) != (1 if kind == "FACT" else 2):
            raise ValueError(f"Wrong number of cells for {kind}")
        if kind == "FACT":
            status = Status(raw.get("status"))
            if status == Status.UNKNOWN:
                raise ValueError("FACT cannot be UNKNOWN")
    elif kind in ("EXACTLY", "AT_LEAST", "AT_MOST"):
        count = raw.get("count")
        if type(count) is not int or not 0 <= count <= len(cells):
            raise ValueError("Count must be an integer within the region size")
    target = Status(raw.get('target_status','CRIMINAL'))
    if target == Status.UNKNOWN:
        raise ValueError('Count target cannot be UNKNOWN')
    if target == Status.INNOCENT:
        if kind in ('EXACTLY','AT_LEAST','AT_MOST'):
            count = len(cells)-count
            kind = {'AT_LEAST':'AT_MOST','AT_MOST':'AT_LEAST'}.get(kind,kind)
        elif kind in ('ODD','EVEN') and len(cells)%2:
            kind = 'EVEN' if kind=='ODD' else 'ODD'
    return Clue(raw["id"], kind, cells, count, status, describe_region(region), target)


def load_puzzle(path: str | Path) -> Puzzle:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or type(raw.get("size")) is not int or raw["size"] not in (3, 4, 5):
        raise ValueError("Puzzle size must be 3, 4, or 5")
    size = raw["size"]
    title = raw.get("name", raw.get("title"))
    if not isinstance(title, str) or not title.strip():
        raise ValueError("Puzzle name is required (legacy title is also accepted)")
    cards = raw.get("characters")
    if not isinstance(cards, list) or len(cards) != size*size:
        raise ValueError("Provide exactly one character per cell")
    if any(not isinstance(x, dict) or not isinstance(x.get("cell"), str) for x in cards):
        raise ValueError("Each character needs a cell ID")
    by_id = {x["cell"]: x for x in cards}
    if len(by_id) != len(cards) or set(by_id) != set(cell_ids(size)):
        raise ValueError("Duplicate, missing, or invalid character cells")
    characters, solution, clues = [], [], []
    for cell in cell_ids(size):
        card = by_id[cell]
        origin = card.get("origin", card.get("profession"))
        if not isinstance(origin, str) or not origin.strip():
            raise ValueError(f"{cell}: origin (or legacy profession) is required")
        for key in ("name",):
            if not isinstance(card.get(key), str) or not card[key].strip():
                raise ValueError(f"{cell}: {key} is required")
        status = Status(card.get("status"))
        if status == Status.UNKNOWN:
            raise ValueError("Hidden solution cannot contain UNKNOWN")
        characters.append(Character(cell, card["name"], origin))
        solution.append((cell, status))
        clues.append(parse_clue(card.get("clue"), size))
    names = [x.name.casefold() for x in characters]
    if names != sorted(names) or len(set(names)) != len(names):
        raise ValueError("Names must be unique and alphabetical in row-major order")
    if len({x.id for x in clues}) != len(clues):
        raise ValueError("Clue IDs must be unique")
    initial = raw.get("initially_revealed")
    if not isinstance(initial, list) or any(not isinstance(x, str) or x not in by_id for x in initial):
        raise ValueError("initially_revealed must list valid cell IDs")
    if len(set(initial)) != len(initial):
        raise ValueError("Duplicate initial reveals")
    fixed_cast = raw.get('fixed_cast',False)
    if type(fixed_cast) is not bool:
        raise ValueError('fixed_cast must be boolean')
    return Puzzle(title, size, tuple(characters), tuple(solution), tuple(clues), tuple(initial),fixed_cast)
