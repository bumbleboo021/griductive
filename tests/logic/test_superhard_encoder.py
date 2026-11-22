from collections import deque
import itertools
import pytest

from griductive.domain.models import Character, Clue, PublicState, Status
from griductive.logic.encoder import encode


CELLS_3X3 = ["A1", "B1", "C1", "A2", "B2", "C2", "A3", "B3", "C3"]
CELL_TO_VAR_3X3 = {cell: idx + 1 for idx, cell in enumerate(CELLS_3X3)}
CELL_TO_COORD_3X3 = {
    cell: (idx // 3, idx % 3) for idx, cell in enumerate(CELLS_3X3)
}


def make_3x3_state(
    verdicts: tuple[tuple[str, Status], ...] = (),
    clues: tuple[Clue, ...] = (),
) -> PublicState:
    """Tạo bàn cờ 3x3 chuẩn theo thứ tự đọc sách (row-major): A1..C3 -> biến 1..9[cite: 5, 6]."""
    characters = tuple(
        Character(cell=c, name=f"Char_{i}", profession="Villager")
        for i, c in enumerate(CELLS_3X3)
    )
    return PublicState(
        size=3,
        characters=characters,
        verdicts=verdicts,
        clues=clues,
    )


def is_cnf_sat_under_primary(
    clauses: list[list[int]] | tuple[tuple[int, ...], ...],
    primary_assign: dict[int, bool],
) -> bool:
    """
    Cố định giá trị các biến chính (primary_assign) và kiểm tra xem có tồn tại
    cách gán nào cho các biến phụ để thỏa mãn toàn bộ CNF hay không[cite: 4].
    """
    simplified: list[list[int]] = []
    for clause in clauses:
        if len(clause) == 0:
            return False
        new_clause = []
        satisfied = False
        for lit in clause:
            var = abs(lit)
            if var in primary_assign:
                val = primary_assign[var]
                if (lit > 0 and val) or (lit < 0 and not val):
                    satisfied = True
                    break
            else:
                new_clause.append(lit)
        if not satisfied:
            if not new_clause:
                return False
            simplified.append(new_clause)

    def backtrack(cls_list: list[list[int]]) -> bool:
        while True:
            unit_lit = None
            for c in cls_list:
                if len(c) == 0:
                    return False
                if len(c) == 1:
                    unit_lit = c[0]
                    break
            if unit_lit is None:
                break
            next_cls = []
            for c in cls_list:
                if unit_lit in c:
                    continue
                if -unit_lit in c:
                    reduced = [x for x in c if x != -unit_lit]
                    if not reduced:
                        return False
                    next_cls.append(reduced)
                else:
                    next_cls.append(c)
            cls_list = next_cls

        if not cls_list:
            return True

        pivot = abs(cls_list[0][0])
        for branch_lit in (pivot, -pivot):
            next_cls = []
            conflict = False
            for c in cls_list:
                if branch_lit in c:
                    continue
                if -branch_lit in c:
                    reduced = [x for x in c if x != -branch_lit]
                    if not reduced:
                        conflict = True
                        break
                    next_cls.append(reduced)
                else:
                    next_cls.append(c)
            if not conflict and backtrack(next_cls):
                return True
        return False

    return backtrack(simplified)


def all_assignments(num_vars: int):
    for bits in itertools.product([False, True], repeat=num_vars):
        yield {i + 1: bit for i, bit in enumerate(bits)}


def assert_stats_consistent(res):
    assert res.num_primary_vars == 9
    assert res.num_aux_vars >= 0
    assert res.total_vars == res.num_primary_vars + res.num_aux_vars
    assert res.num_clauses == len(res.clauses)
    assert res.primary_vars == set(range(1, 10))
    for clause in res.clauses:
        for lit in clause:
            assert 1 <= abs(lit) <= res.total_vars


# =====================================================================
# BỘ ĐÁNH GIÁ NGỮ NGHĨA ĐỘC LẬP (INDEPENDENT SEMANTIC ORACLES)[cite: 4]
# =====================================================================

def semantic_count_compare(
    assign: dict[int, bool],
    cells: tuple[str, ...],
    other_cells: tuple[str, ...],
    operator: str,
    target_status: Status,
) -> bool:
    want_criminal = target_status == Status.CRIMINAL
    c1 = sum(1 for c in cells if assign[CELL_TO_VAR_3X3[c]] is want_criminal)
    c2 = sum(1 for c in other_cells if assign[CELL_TO_VAR_3X3[c]] is want_criminal)
    if operator == "GT":
        return c1 > c2
    if operator == "LT":
        return c1 < c2
    if operator == "EQ":
        return c1 == c2
    raise ValueError(f"Unknown operator: {operator}")


def semantic_connected(
    assign: dict[int, bool],
    cells: tuple[str, ...],
    target_status: Status,
) -> bool:
    want_criminal = target_status == Status.CRIMINAL
    active_cells = [
        c for c in cells if assign[CELL_TO_VAR_3X3[c]] is want_criminal
    ]
    # Tập rỗng hoặc 1 phần tử luôn thỏa mãn tính liên thông[cite: 3, 4, 5]
    if len(active_cells) <= 1:
        return True

    active_set = set(active_cells)
    visited = {active_cells[0]}
    queue = deque([active_cells[0]])

    while queue:
        curr = queue.popleft()
        r1, c1 = CELL_TO_COORD_3X3[curr]
        for nxt in active_set:
            if nxt in visited:
                continue
            r2, c2 = CELL_TO_COORD_3X3[nxt]
            # Chỉ xét 4 hướng vuông góc (khoảng cách Manhattan == 1)[cite: 3, 4, 5]
            if abs(r1 - r2) + abs(c1 - c2) == 1:
                visited.add(nxt)
                queue.append(nxt)

    return len(visited) == len(active_set)


# =====================================================================
# 1. KIỂM TRA VÉT CẠN COUNT_COMPARE (BAO GỒM GIAO NHAU & INNOCENT)
# =====================================================================

@pytest.mark.parametrize(
    "r1, r2",
    [
        ((), ()),                                                   # Hai vùng rỗng
        (("A1", "B1"), ()),                                         # Một vùng rỗng
        (("A1", "B1"), ("A2", "B2", "C2")),                         # Hai vùng rời nhau
        (("A1", "B1", "C1"), ("A1", "A2", "A3")),                   # Giao nhau tại A1 (cancellation)[cite: 4]
        (("A1", "B1", "A2", "B2"), ("B1", "C1", "B2", "C2")),       # Giao nhau 2 ô B1, B2[cite: 4]
        (("A1", "B2", "C3"), ("A1", "B2", "C3")),                   # Trùng khít hoàn toàn (tự triệt tiêu hết)
    ],
)
@pytest.mark.parametrize("operator", ["GT", "LT", "EQ"])
@pytest.mark.parametrize("target_status", [Status.CRIMINAL, Status.INNOCENT])
def test_count_compare_exhaustive(r1, r2, operator, target_status):
    clue = Clue(
        id="cmp_test",
        kind="COUNT_COMPARE",
        cells=r1,
        other_cells=r2,
        operator=operator,
        target_status=target_status,
    )
    res = encode(make_3x3_state(clues=(clue,)))
    assert_stats_consistent(res)

    for assign in all_assignments(9):
        expected = semantic_count_compare(assign, r1, r2, operator, target_status)
        actual = is_cnf_sat_under_primary(res.clauses, assign)
        assert actual == expected, (
            f"Sai lệch COUNT_COMPARE: r1={r1}, r2={r2}, op={operator}, "
            f"target={target_status}: CNF={actual} != Semantic={expected}"
        )


# =====================================================================
# 2. KIỂM TRA VÉT CẠN CONNECTED (CHÉO, RỖNG, SINGLETON, VÙNG CHỮ U)
# =====================================================================

@pytest.mark.parametrize(
    "region",
    [
        (),                                                                 # Vùng rỗng[cite: 4]
        ("B2",),                                                            # Vùng 1 ô[cite: 4]
        ("A1", "B2"),                                                       # Chỉ có 2 ô chéo nhau (diagonal-only)[cite: 4]
        ("A1", "B1", "A2", "B2"),                                           # Khối vuông 2x2 (có cả chéo lẫn kề)
        ("A1", "B1", "C1", "A2", "C2", "A3", "B3", "C3"),                   # Vành ngoài bỏ B2 (kiểm tra đường vòng)[cite: 3, 5]
        ("A1", "B1", "C1", "A2", "B2", "C2", "A3", "B3", "C3"),             # Toàn bộ lưới 3x3
    ],
)
@pytest.mark.parametrize("target_status", [Status.CRIMINAL, Status.INNOCENT])
def test_connected_exhaustive(region, target_status):
    clue = Clue(
        id="conn_test",
        kind="CONNECTED",
        cells=region,
        target_status=target_status,
    )
    res = encode(make_3x3_state(clues=(clue,)))
    assert_stats_consistent(res)

    for assign in all_assignments(9):
        expected = semantic_connected(assign, region, target_status)
        actual = is_cnf_sat_under_primary(res.clauses, assign)
        assert actual == expected, (
            f"Sai lệch CONNECTED: region={region}, target={target_status}, "
            f"assign={assign}: CNF={actual} != Semantic={expected}"
        )


# =====================================================================
# 3. KIỂM TRA CÁC TÌNH HUỐNG BIÊN CỤ THỂ CỦA CONNECTED
# =====================================================================

def test_connected_specific_edge_cases():
    """Xác minh tường minh các ca rỗng, singleton, tiếp xúc chéo và cầu nối ngoài vùng."""
    region = ("A1", "B1", "C1", "A2", "C2", "A3", "B3", "C3")  # Bỏ ô trung tâm B2
    clue = Clue(
        id="conn_edge",
        kind="CONNECTED",
        cells=region,
        target_status=Status.CRIMINAL,
    )
    res = encode(make_3x3_state(clues=(clue,)))

    base_innocent = {i: False for i in range(1, 10)}

    # 1. Tập rỗng (0 tội phạm) -> Thỏa mãn
    assert is_cnf_sat_under_primary(res.clauses, base_innocent) is True

    # 2. Singleton (1 tội phạm tại A1) -> Thỏa mãn
    assert is_cnf_sat_under_primary(res.clauses, base_innocent | {1: True}) is True

    # 3. Không liền kề (A1 và C2 cách nhau) -> Sai
    assert is_cnf_sat_under_primary(res.clauses, base_innocent | {1: True, 6: True}) is False

    # 4. B1 (2) và B3 (8) là tội phạm, B2 (5) nằm NGOÀI vùng -> Không liên thông trong vùng
    assert is_cnf_sat_under_primary(res.clauses, base_innocent | {2: True, 5: True, 8: True}) is False

    # 5. B1 (2) và B3 (8) nối vòng qua A1 (1), A2 (4), A3 (7) bên trong vùng -> Thỏa mãn
    assert is_cnf_sat_under_primary(res.clauses, base_innocent | {2: True, 1: True, 4: True, 7: True, 8: True}) is True


# =====================================================================
# 4. KIỂM TRA KẾT HỢP TOÀN BỘ 8 LOẠI MANH MỐI & ĐẦU VÀO LỖI[cite: 4]
# =====================================================================

def test_combined_all_clue_templates_no_collision():
    """Đảm bảo khi trộn lẫn tất cả các loại manh mối phức tạp, ID biến phụ không đè lên nhau[cite: 4]."""
    clues = (
        Clue(id="c1", kind="COUNT_COMPARE", cells=("A1", "B1"), other_cells=("B1", "C1"), operator="GT", target_status=Status.CRIMINAL),
        Clue(id="c2", kind="CONNECTED", cells=("A1", "B1", "A2", "B2"), target_status=Status.INNOCENT),
        Clue(id="c3", kind="EXACTLY", cells=("A3", "B3", "C3"), count=1),
        Clue(id="c4", kind="ODD", cells=("C1", "C2", "C3")),
    )
    res = encode(make_3x3_state(clues=clues))
    assert_stats_consistent(res)

    for assign in all_assignments(9):
        ok1 = semantic_count_compare(assign, ("A1", "B1"), ("B1", "C1"), "GT", Status.CRIMINAL)
        ok2 = semantic_connected(assign, ("A1", "B1", "A2", "B2"), Status.INNOCENT)
        ok3 = sum(1 for v in (7, 8, 9) if assign[v]) == 1
        ok4 = (sum(1 for v in (3, 6, 9) if assign[v]) % 2) == 1
        assert is_cnf_sat_under_primary(res.clauses, assign) == (ok1 and ok2 and ok3 and ok4)


def test_stage4_invalid_inputs():
    with pytest.raises(ValueError):
        encode(make_3x3_state(clues=(
            Clue(id="bad_op", kind="COUNT_COMPARE", cells=("A1",), other_cells=("B1",), operator="INVALID", target_status=Status.CRIMINAL),
        )))

    with pytest.raises(ValueError):
        encode(make_3x3_state(clues=(
            Clue(id="bad_cmp_target", kind="COUNT_COMPARE", cells=("A1",), other_cells=("B1",), operator="EQ", target_status=None),
        )))

    with pytest.raises(ValueError):
        encode(make_3x3_state(clues=(
            Clue(id="bad_conn_target", kind="CONNECTED", cells=("A1", "B1"), target_status=None),
        )))