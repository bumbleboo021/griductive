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


def _inspect_clause(clause: list[int] | tuple[int, ...], assignment: dict[int, bool]):
    """Kiểm tra trạng thái hiện tại của một mệnh đề: SAT, CONFLICT, UNIT hoặc OPEN."""
    unassigned = []
    for lit in clause:
        var = abs(lit)
        want = (lit > 0)
        if var in assignment:
            if assignment[var] == want:
                # Chỉ cần một literal đúng là cả mệnh đề OR được thỏa mãn.
                return ("SAT", None)
            else: continue

        else:
            # Lọc trùng literal để tránh nhận nhầm clause lặp như [1, 1] thành OPEN.
            if lit not in unassigned:
                unassigned.append(lit)

    if len(unassigned) == 0:
        return ("CONFLICT", None)

    elif len(unassigned) == 1:
        return ("UNIT", unassigned[0])
    else:
        return ("OPEN", None)




def solve(
        clauses: list[list[int]] | tuple[tuple[int,...],...],
        total_vars: int,
        assumptions: list[int] | tuple[int, ...] = (),
        timeout_seconds: float | None = None
        ) -> SatResult:
    """Giải công thức CNF bằng DPLL kèm các giả định tạm thời không làm biến đổi KB."""

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

        # Chọn biến chưa gán có ID nhỏ nhất trong các mệnh đề chưa thỏa mãn.
        best_var = None
        for clause in clauses:
            status, _ = _inspect_clause(clause, curr_assignment)
            if status != "SAT":
                for lit in clause:
                    var = abs(lit)
                    if var not in curr_assignment:
                        if best_var is None or var < best_var:
                            best_var = var
        
        if best_var is None:
            return curr_assignment

        decisions+=1

        # Thử gán True trước; dùng bản sao để nhánh quay lui không bị dính vết của nhánh trước.
        try_true = curr_assignment.copy()
        try_true[best_var] = True
        res = _dpll(try_true)
        if res is not None:
            return res

        # Nhánh True thất bại thì quay lui và thử gán False.
        backtracks+=1
        try_false = curr_assignment.copy()
        try_false[best_var] = False
        res = _dpll(try_false)
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

    