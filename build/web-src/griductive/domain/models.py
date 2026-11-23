"""Immutable boundary shared by the engine, UI, and teammate analyzers."""
from dataclasses import dataclass
from enum import Enum
from typing import Protocol


class Status(str, Enum):
    CRIMINAL = "CRIMINAL"
    INNOCENT = "INNOCENT"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class Character:
    cell: str
    name: str
    profession: str

    @property
    def origin(self) -> str:
        """Display origin; profession remains available for existing integrations."""
        return self.profession


@dataclass(frozen=True)
class Clue:
    id: str
    kind: str
    cells: tuple[str, ...]
    count: int | None = None
    status: Status | None = None
    region_label: str | None = None
    target_status: Status = Status.CRIMINAL
    other_cells: tuple[str, ...] = ()
    other_region_label: str | None = None
    operator: str = 'GT'
    antecedent_status: Status = Status.CRIMINAL
    consequent_status: Status = Status.INNOCENT

    @property
    def referenced_cells(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys(self.cells+self.other_cells))

    @property
    def text(self) -> str:
        if self.kind == 'QUOTE':
            return 'Just a personal remark.'
        cells = ", ".join(self.cells) or "empty region"
        if self.kind == "FACT":
            if self.region_label and self.region_label.startswith('the cell directly'):
                subject = self.region_label.replace('the cell directly','The person directly',1)
                return f'{subject} is {self.status.value.lower()}.'
            return f"{cells} is {self.status.value.lower()}."
        if self.kind in ("SAME", "DIFFERENT"):
            return f"{cells} have {self.kind.lower()} statuses."
        region = self.region_label or f'[{cells}]'
        noun = self.target_status.value.lower()
        if self.kind == 'IMPLIES':
            return f'If {self.cells[0]} is {self.antecedent_status.value.lower()}, then {self.cells[1]} is {self.consequent_status.value.lower()}.'
        if self.kind == 'CONNECTED':
            return f'All {noun}s in {region} are connected (no diagonals).'
        if self.kind == 'COUNT_COMPARE':
            comparison = {'GT':'more','LT':'fewer','EQ':'the same number of'}[self.operator]
            connector = 'as' if self.operator == 'EQ' else 'than'
            return f'There are {comparison} {noun}s in {region} {connector} in {self.other_region_label}.'
        kind, count = self.kind, self.count
        innocent = self.target_status == Status.INNOCENT
        if innocent:
            if count is not None:
                count = len(self.cells)-count
            kind = {'AT_LEAST':'AT_MOST','AT_MOST':'AT_LEAST'}.get(kind,kind)
            if len(self.cells)%2 and kind in ('ODD','EVEN'):
                kind = 'EVEN' if kind == 'ODD' else 'ODD'
        noun = 'innocent' if innocent else 'criminal'
        preposition = 'among' if "'s neighbors" in region else 'in'
        if kind in ('EVEN','ODD'):
            return f"An {kind.lower()} number of {noun}s {preposition} {region}."
        if kind == 'EXACTLY' and count == len(self.cells) and self.cells:
            if "'s neighbors" in region:
                return f"All of {region} are {noun}."
            return f"Everyone in {region} is {noun}."
        if kind == 'EXACTLY' and count == 0:
            return f"No {noun}s {preposition} {region}."
        return f"{kind.replace('_',' ').capitalize()} {count} {noun if count == 1 else noun+'s'} {preposition} {region}."


@dataclass(frozen=True)
class PublicState:
    size: int
    characters: tuple[Character, ...]
    verdicts: tuple[tuple[str, Status], ...]
    clues: tuple[Clue, ...]


@dataclass(frozen=True)
class Analysis:
    """Verdicts must cover every unresolved cell, in row-major order.

    An inconsistent result must have an empty verdicts tuple.
    UNKNOWN means both statuses remain possible, never a solver timeout.
    """
    consistent: bool
    verdicts: tuple[tuple[str, Status], ...]


class Analyzer(Protocol):
    def analyze(self, state: PublicState) -> Analysis: ...
