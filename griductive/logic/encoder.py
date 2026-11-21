from dataclasses import dataclass

from ..domain.models import PublicState



@dataclass(frozen=True)
class CNFResult:
    """Represents the result of encoding a problem into CNF (Conjunctive Normal Form).
    
    Attributes:
        clauses: A list of clauses, where each clause is a list of integers.
        cell_to_var: A dictionary mapping cell coordinates to variable numbers.
        var_to_cell: A dictionary mapping variable numbers to cell coordinates.
        primary_vars: A set of primary variable numbers.
        num_primary_vars: The number of primary variables.
        num_aux_vars: The number of auxiliary variables.
        num_clauses: The number of clauses.
        total_vars: The total number of variables (primary + auxiliary).
    """
    clauses: tuple[tuple[int,...],...]
    cell_to_var: dict[str, int]
    var_to_cell: dict[int, str]
    num_primary_vars: int
    num_aux_vars: int

    @property
    def primary_vars(self) -> set[int]:
        """Returns the set of primary variable numbers in the CNF result."""
        return set(range(1, self.num_primary_vars + 1))

    @property
    def num_clauses(self) -> int:
        """Returns the number of clauses in the CNF result."""
        return len(self.clauses)

    @property
    def total_vars(self) -> int:
        """Returns the total number of variables in the CNF result."""
        return self.num_primary_vars + self.num_aux_vars



def _encode_cell(size: int) -> (dict[str, int], dict[int, str]):
    ord_A = ord('A')
    cell_to_var = {}
    var_to_cell = {}
    for i in range(size):
        for j in range(size):
            cell = chr(ord_A + j) + str(i + 1)
            var = i * size + j + 1
            cell_to_var[cell] = var
            var_to_cell[var] = cell
    return cell_to_var, var_to_cell


def _get_cell_var(cell: str, cell_to_var: dict[str, int]) -> int:
    if cell not in cell_to_var:
        raise ValueError(f"Cell {cell} is not valid.")
    return cell_to_var[cell]


def _fact(cell: str, status: str, cell_to_var: dict[str, int]) -> int:
    if status == 'INNOCENT':
        return -_get_cell_var(cell, cell_to_var)
    elif status == 'CRIMINAL':
        return _get_cell_var(cell, cell_to_var)
    else:
        raise ValueError(f"Unknown status: {status}")

def _encode_fact(clue, cell_to_var):
    if len(clue.cells) != 1:
        raise ValueError("FACT clue must have exactly one cell.")
    return [(_fact(clue.cells[0], clue.status, cell_to_var),)]


def _same(var1, var2):
    return [(-var1, var2), (var1, -var2)]

def _encode_same(clue, cell_to_var):
    if len(clue.cells) != 2:
        raise ValueError("SAME clue must have exactly two cells.")
    return _same(_get_cell_var(clue.cells[0], cell_to_var), _get_cell_var(clue.cells[1], cell_to_var))


def _different(var1, var2):
    return [(-var1, -var2), (var1, var2)]

def _encode_different(clue, cell_to_var):
    if len(clue.cells) != 2:
        raise ValueError("DIFFERENT clue must have exactly two cells.")
    return _different(_get_cell_var(clue.cells[0], cell_to_var), _get_cell_var(clue.cells[1], cell_to_var))


def _encode_implies(clue, cell_to_var):
    if len(clue.cells) != 2:
        raise ValueError("IMPLIES clue must have exactly two cells.")
    lit_1 = _fact(clue.cells[0], clue.antecedent_status, cell_to_var)
    lit_2 = _fact(clue.cells[1], clue.consequent_status, cell_to_var)
    return [(-lit_1, lit_2)]


def encode(state: PublicState) -> CNFResult:
    """Encodes the given public state into CNF format.
    
    Args:
        state: The public state to encode.
        
    Returns:
        A CNFResult object containing the encoded clauses and variable mappings.
    """
    cell_to_var, var_to_cell = _encode_cell(state.size)

    num_primary_vars = state.size * state.size
    next_aux = num_primary_vars + 1
    raw_clauses = []

    for (cell, status) in state.verdicts:
        var = _get_cell_var(cell, cell_to_var)
        if status == 'INNOCENT':
            raw_clauses.append((-var,))
        elif status == 'CRIMINAL':
            raw_clauses.append((var,))
        else:
            raise ValueError(f"Unknown status: {status}")

    for clue in state.clues:
        match clue.kind:
            case 'QUOTE':
                continue
            case 'FACT':
                raw_clauses.extend(_encode_fact(clue, cell_to_var))
            case 'SAME':
                raw_clauses.extend(_encode_same(clue, cell_to_var))
            case 'DIFFERENT':
                raw_clauses.extend(_encode_different(clue, cell_to_var))
            case 'IMPLIES':
                raw_clauses.extend(_encode_implies(clue, cell_to_var))
            case _:
                raise NotImplementedError(f"Clue kind '{clue.kind}' is not implemented yet.")

    return CNFResult(
        clauses = tuple(raw_clauses),
        cell_to_var = cell_to_var,
        var_to_cell = var_to_cell,
        num_primary_vars = num_primary_vars,
        num_aux_vars = next_aux - 1 - num_primary_vars,
    )

if __name__ == "__main__":
    print("Hello from griductive.logic.encoder!")