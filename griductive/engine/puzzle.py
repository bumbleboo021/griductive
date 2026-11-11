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


def cell_ids(size: int) -> tuple[str, ...]:
    return tuple(f"{chr(65+c)}{r+1}" for r in range(size) for c in range(size))


def region_cells(region: dict, size: int) -> tuple[str, ...]:
    if not isinstance(region, dict):
        raise ValueError("Region must be an object")
    ids = cell_ids(size)
    kind = region.get("type")
    if kind == "row":
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
    elif kind == "cells":
        cells = region.get("cells")
        if not isinstance(cells, list) or any(not isinstance(x, str) for x in cells):
            raise ValueError("Explicit region needs a list of cell IDs")
    else:
        raise ValueError(f"Unsupported region: {kind}")
    if len(set(cells)) != len(cells) or any(x not in ids for x in cells):
        raise ValueError("Region contains duplicate or invalid cells")
    return tuple(x for x in ids if x in cells)


def parse_clue(raw: dict, size: int) -> Clue:
    if not isinstance(raw, dict) or not isinstance(raw.get("id"), str) or not raw["id"].strip():
        raise ValueError("Each clue needs a nonempty string ID")
    kind = raw.get("type")
    if kind not in ("FACT", "SAME", "DIFFERENT", "EXACTLY", "AT_LEAST", "AT_MOST", "EVEN", "ODD"):
        raise ValueError(f"Unsupported clue type: {kind}")
    cells = region_cells(raw.get("region", {"type": "cells", "cells": raw.get("cells")}), size)
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
    return Clue(raw["id"], kind, cells, count, status)


def load_puzzle(path: str | Path) -> Puzzle:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or type(raw.get("size")) is not int or raw["size"] not in (3, 4, 5):
        raise ValueError("Puzzle size must be 3, 4, or 5")
    size = raw["size"]
    title = raw.get("title")
    if not isinstance(title, str) or not title.strip():
        raise ValueError("Puzzle title is required")
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
        for key in ("name", "profession"):
            if not isinstance(card.get(key), str) or not card[key].strip():
                raise ValueError(f"{cell}: {key} is required")
        status = Status(card.get("status"))
        if status == Status.UNKNOWN:
            raise ValueError("Hidden solution cannot contain UNKNOWN")
        characters.append(Character(cell, card["name"], card["profession"]))
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
    return Puzzle(title, size, tuple(characters), tuple(solution), tuple(clues), tuple(initial))
