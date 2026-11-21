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


def _encode_odd_even(clue, cell_to_var, next_aux):
    if len(clue.cells) == 0:
        if clue.kind == 'ODD':
            return next_aux, [()]
        elif clue.kind == 'EVEN':
            return next_aux, []
        else:
            raise ValueError(f"Unknown kind for ODD/EVEN encoding: {clue.kind}")
    if len(clue.cells) == 1:
        if clue.kind == 'ODD':
            return next_aux, [(_get_cell_var(clue.cells[0], cell_to_var),)]
        elif clue.kind == 'EVEN':
            return next_aux, [(-_get_cell_var(clue.cells[0], cell_to_var),)]
        else:
            raise ValueError(f"Unknown kind for ODD/EVEN encoding: {clue.kind}")
    
    clauses = []

    primary_vars = [_get_cell_var(cell, cell_to_var) for cell in clue.cells]
    m = len(primary_vars)

    acc = primary_vars[0]

    for i in range(1, m - 1):
        x = acc
        y = primary_vars[i]
        z = next_aux
        next_aux += 1
        clauses.extend([(-x, -y, -z), (x, y, -z), (x, -y, z), (-x, y, z)])
        acc = z

    if clue.kind == 'ODD':
        clauses.extend(_different(acc, primary_vars[-1]))
    elif clue.kind == 'EVEN':
        clauses.extend(_same(acc, primary_vars[-1]))
    else:
        raise ValueError(f"Unknown kind for ODD/EVEN encoding: {clue.kind}")

    return next_aux, clauses


def _at_most(literals, k, next_aux):
    if k < 0:
        return next_aux, [()]
    if k == 0:
        return next_aux, [(-lit,) for lit in literals]
    m = len(literals)
    if k >= m:
        return next_aux, []

    clauses = []

    aux_vars = [[next_aux + i * k + j for j in range(k)] for i in range(m - 1)]
    next_aux += (m - 1) * k

    clauses.append((-literals[0], aux_vars[0][0]))
    for j in range(1, k):
        clauses.append((-aux_vars[0][j],))

    for i in range(1, m - 1):
        for j in range(k):
            clauses.append((-aux_vars[i - 1][j], aux_vars[i][j]))
        clauses.append((-literals[i], aux_vars[i][0]))
        for j in range(1, k):
            clauses.append((-aux_vars[i - 1][j - 1], -literals[i], aux_vars[i][j]))
        clauses.append((-aux_vars[i - 1][k - 1], -literals[i]))

    clauses.append((-aux_vars[m - 2][k - 1], -literals[m - 1]))

    return next_aux, clauses

def _encode_at_most(clue, cell_to_var, next_aux):
    if clue.count is None:
        raise ValueError("k must be specified for AT_MOST encoding.")
    primary_vars = [_get_cell_var(cell, cell_to_var) for cell in clue.cells]
    return _at_most(primary_vars, clue.count, next_aux)


def _at_least(literals, k, next_aux):
    return _at_most([-lit for lit in literals], len(literals) - k, next_aux)

def _encode_at_least(clue, cell_to_var, next_aux):
    if clue.count is None:
        raise ValueError("k must be specified for AT_LEAST encoding.")
    primary_vars = [_get_cell_var(cell, cell_to_var) for cell in clue.cells]
    return _at_least(primary_vars, clue.count, next_aux)


def _exactly(literals, k, next_aux):
    next_aux, at_most_clauses = _at_most(literals, k, next_aux)
    next_aux, at_least_clauses = _at_least(literals, k, next_aux)
    return next_aux, at_most_clauses + at_least_clauses

def _encode_exactly(clue, cell_to_var, next_aux):
    if clue.count is None:
        raise ValueError("k must be specified for EXACTLY encoding.")
    primary_vars = [_get_cell_var(cell, cell_to_var) for cell in clue.cells]
    return _exactly(primary_vars, clue.count, next_aux)


def _encode_count_compare(clue, cell_to_var, next_aux):
    L_A = [_fact(cell, clue.target_status, cell_to_var) for cell in clue.cells if cell not in clue.other_cells]
    L_B = [_fact(cell, clue.target_status, cell_to_var) for cell in clue.other_cells if cell not in clue.cells]
    if clue.operator == 'EQ':
        return _exactly(L_A + [-lit for lit in L_B], len(L_B), next_aux)
    elif clue.operator == 'GT':
        return _at_least(L_A + [-lit for lit in L_B], len(L_B) + 1, next_aux)
    elif clue.operator == 'LT':
        return _at_least(L_B + [-lit for lit in L_A], len(L_A) + 1, next_aux)
    else:
        raise ValueError(f"Unknown operator for COUNT_COMPARE encoding: {clue.operator}")


def _encode_connected(clue, cell_to_var, next_aux):
    if len(clue.cells) <= 1:
        return next_aux, []

    clauses = []

    R = clue.cells
    m = len(R)

    t = [_fact(cell, clue.target_status, cell_to_var) for cell in R]
    N_R = []

    for cell in R:
        i, j = int(cell[1:]), ord(cell[0])
        neighbors = []
        for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            neighbor_cell = chr(j + dj) + str(i + di)
            if neighbor_cell in R:
                neighbors.append(R.index(neighbor_cell))
        N_R.append(neighbors)
    
    r = [next_aux + i for i in range(m)]
    next_aux += m

    tmp = []
    for i in range(m):
        clauses.append((-r[i], t[i]))
        for j in range(i):
            clauses.append((-r[i], -t[j]))
        clauses.append(tuple([r[i], -t[i]] + tmp))
        tmp.append(t[i])

    p = [[next_aux + i * m + j for j in range(m)] for i in range(m)]
    next_aux += m * m

    for i in range(m):
        clauses.extend(_same(r[i], p[i][0]))
    
    for d in range(1, m):
        for i in range(m):
            clauses.append((-p[i][d], t[i]))
            clauses.append(tuple([-p[i][d], p[i][d - 1]] + [p[u][d - 1] for u in N_R[i]]))
    
    for i in range(m):
        clauses.append((-t[i], p[i][m - 1]))

    return next_aux, clauses


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
            case 'ODD' | 'EVEN':
                next_aux, clauses = _encode_odd_even(clue, cell_to_var, next_aux)
                raw_clauses.extend(clauses)
            case 'AT_MOST':
                next_aux, clauses = _encode_at_most(clue, cell_to_var, next_aux)
                raw_clauses.extend(clauses)
            case 'AT_LEAST':
                next_aux, clauses = _encode_at_least(clue, cell_to_var, next_aux)
                raw_clauses.extend(clauses)
            case 'EXACTLY':
                next_aux, clauses = _encode_exactly(clue, cell_to_var, next_aux)
                raw_clauses.extend(clauses)
            case 'COUNT_COMPARE':
                next_aux, clauses = _encode_count_compare(clue, cell_to_var, next_aux)
                raw_clauses.extend(clauses)
            case 'CONNECTED':
                next_aux, clauses = _encode_connected(clue, cell_to_var, next_aux)
                raw_clauses.extend(clauses)
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