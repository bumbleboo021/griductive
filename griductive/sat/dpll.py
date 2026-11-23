"""Bộ giải SAT theo thuật toán DPLL (Davis-Putnam-Logemann-Loveland)."""
from dataclasses import dataclass
import time


class _SolveTimeout(Exception):
    """Ngoại lệ nội bộ dùng để ngắt đệ quy ngay khi quá thời gian."""
    pass


@dataclass(frozen = True)
class SatResult:
    """Kết quả và các chỉ số đo lường trả về từ hàm solve()."""
    is_sat: bool
    model: dict[int, bool] | None
    is_timeout: bool
    decisions: int
    propagations: int
    backtracks: int
    runtime: float


VALID_HEURISTICS = ("smallest", "jw")


def _unassigned_literals(
    clause: list[int] | tuple[int, ...],
    assignment: dict[int, bool],
) -> list[int] | None:
    """Trả về None nếu mệnh đề đã SAT, ngược lại trả về danh sách literal chưa gán không trùng."""
    unassigned: list[int] = []
    for lit in clause:
        var = abs(lit)
        want = (lit > 0)
        if var in assignment:
            if assignment[var] == want:
                # Chỉ cần một literal đúng là cả mệnh đề OR được thỏa mãn.
                return None
        else:
            # Lọc trùng literal để tránh nhận nhầm clause lặp như [1, 1] thành OPEN.
            if lit not in unassigned:
                unassigned.append(lit)
    return unassigned


def _inspect_clause(clause: list[int] | tuple[int, ...], assignment: dict[int, bool]):
    """Kiểm tra trạng thái hiện tại của một mệnh đề: SAT, CONFLICT, UNIT hoặc OPEN."""
    unassigned = _unassigned_literals(clause, assignment)
    if unassigned is None:
        return ("SAT", None)

    if len(unassigned) == 0:
        return ("CONFLICT", None)

    elif len(unassigned) == 1:
        return ("UNIT", unassigned[0])
    else:
        return ("OPEN", None)


def _select_branch_smallest(
    clauses: list[list[int]] | tuple[tuple[int, ...], ...],
    assignment: dict[int, bool],
) -> tuple[int, bool] | None:
    """Chọn biến chưa gán có ID nhỏ nhất trong các mệnh đề chưa SAT, thử True trước."""

    best_var = None
    for clause in clauses:
        unassigned = _unassigned_literals(clause, assignment)
        if unassigned:
            for lit in unassigned:
                var = abs(lit)
                if best_var is None or var < best_var:
                    best_var = var

    if best_var is None:
        return None
    return (best_var, True)


def _select_branch_jw(
    clauses: list[list[int]] | tuple[tuple[int, ...], ...],
    assignment: dict[int, bool],
) -> tuple[int, bool] | None:
    """Chọn theo Two-Sided Jeroslow-Wang động: J(l) = sum(2^-|C'|)."""
    pos_scores: dict[int, float] = {}
    neg_scores: dict[int, float] = {}

    for clause in clauses:
        unassigned = _unassigned_literals(clause, assignment)
        if not unassigned:
            continue
        weight = 2.0 ** (-len(unassigned))
        for lit in unassigned:
            var = abs(lit)
            if lit > 0:
                pos_scores[var] = pos_scores.get(var, 0.0) + weight
            else:
                neg_scores[var] = neg_scores.get(var, 0.0) + weight

    all_vars = set(pos_scores) | set(neg_scores)
    if not all_vars:
        return None

    # Ưu tiên tổng trọng số J(+v) + J(-v) lớn nhất; hòa thì lấy var ID nhỏ nhất để tất định.
    best_var = max(
        all_vars,
        key=lambda v: (pos_scores.get(v, 0.0) + neg_scores.get(v, 0.0), -v),
    )
    first_val = pos_scores.get(best_var, 0.0) >= neg_scores.get(best_var, 0.0)
    return (best_var, first_val)


_BRANCH_SELECTORS = {
    "smallest": _select_branch_smallest,
    "jw": _select_branch_jw,
}


def solve(
        clauses: list[list[int]] | tuple[tuple[int,...],...],
        total_vars: int,
        assumptions: list[int] | tuple[int, ...] = (),
        timeout_seconds: float | None = None,
        heuristic: str = "smallest",
        ) -> SatResult:
    
    if heuristic not in _BRANCH_SELECTORS:
        raise ValueError(
            f"Heuristic không được hỗ trợ: {heuristic!r}. "
            f"Các giá trị hợp lệ: {', '.join(VALID_HEURISTICS)}"
        )
    select_branch = _BRANCH_SELECTORS[heuristic]

    start = time.perf_counter()
    deadline = None if timeout_seconds is None else start + timeout_seconds
    assignment: dict[int, bool] = {}
    decisions = 0 
    propagations = 0
    backtracks = 0

    # Nạp các giả định tạm thời trước khi lan truyền; báo UNSAT ngay nếu tự mâu thuẫn.
    for lit in assumptions:
        var = abs(lit)
        want = (lit > 0)
        if var in assignment and assignment[var] != want:
            return SatResult(
                is_sat=False,
                model=None,
                is_timeout=False,
                decisions=decisions,
                propagations=propagations,
                backtracks=backtracks,
                runtime=time.perf_counter() - start,
            )
        
        assignment[var] = want

    def _check_timeout() -> None:
        if deadline is not None and time.perf_counter() >= deadline:
            raise _SolveTimeout()


    def _unit_propagate(curr_assignment: dict[int, bool]) -> bool:
        """Lan truyền các mệnh đề đơn vị theo hiệu ứng dây chuyền; trả False nếu gặp xung đột."""
        nonlocal propagations
        while True:
            _check_timeout()
            changed = False
            for clause in clauses:
                status, unit_lit = _inspect_clause(clause, curr_assignment)
                if status == "CONFLICT": return False
                if status == "UNIT": 
                    curr_assignment[abs(unit_lit)] = (unit_lit > 0)
                    propagations+=1
                    changed = True
            if not changed:
                return True


    def _dpll(curr_assignment: dict[int, bool]) -> dict[int, bool] | None:
        """Tìm một phép gán thỏa mãn bằng lan truyền đơn vị, rẽ nhánh xác định và quay lui."""
        nonlocal decisions, backtracks
        _check_timeout()

        if not _unit_propagate(curr_assignment):
            return None

        # Chọn theo heuristic đã cấu hình.
        branch = select_branch(clauses, curr_assignment)
        if branch is None:
            return curr_assignment

        best_var, first_val = branch
        decisions += 1

        # Thử nhánh ưu tiên trước; dùng bản sao để nhánh quay lui không bị dính vết của nhánh trước.
        try_first = curr_assignment.copy()
        try_first[best_var] = first_val
        res = _dpll(try_first)
        if res is not None:
            return res

        # Nhánh đầu thất bại thì quay lui và thử giá trị còn lại.
        backtracks += 1
        try_second = curr_assignment.copy()
        try_second[best_var] = not first_val
        res = _dpll(try_second)
        if res is not None:
            return res

        return None

    try:
        model = _dpll(assignment)
    except _SolveTimeout:
        return SatResult(
            is_sat=False,
            model=None,
            is_timeout=True,
            decisions=decisions,
            propagations=propagations,
            backtracks=backtracks,
            runtime=time.perf_counter() - start,
        )
    if model is None:
        return SatResult(
            is_sat=False,
            model=None,
            is_timeout=False,
            decisions=decisions,
            propagations=propagations,
            backtracks=backtracks,
            runtime=time.perf_counter() - start,
        )
    # Điền giá trị mặc định False cho các biến tự do để model luôn đầy đủ từ 1..total_vars.
    for v in range(1, total_vars + 1):
        if v not in model:
            model[v] = False
    return SatResult(
        is_sat=True,
        model=model,
        is_timeout=False,
        decisions=decisions,
        propagations=propagations,
        backtracks=backtracks,
        runtime=time.perf_counter() - start,
    )

    