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


@dataclass(frozen=True)
class Clue:
    id: str
    kind: str
    cells: tuple[str, ...]
    count: int | None = None
    status: Status | None = None

    @property
    def text(self) -> str:
        cells = ", ".join(self.cells) or "empty region"
        if self.kind == "FACT":
            return f"{cells} is {self.status.value.lower()}."
        if self.kind in ("SAME", "DIFFERENT"):
            return f"{cells} have {self.kind.lower()} statuses."
        if self.kind in ("EVEN", "ODD"):
            return f"An {self.kind.lower()} number of criminals in [{cells}]."
        return f"{self.kind.replace('_', ' ').capitalize()} {self.count} criminals in [{cells}]."


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
