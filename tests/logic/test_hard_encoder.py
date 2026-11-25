import itertools
import pytest

from griductive.domain.models import Character, Clue, PublicState, Status
from griductive.logic.encoder import encode


def make_3x3_state(
    verdicts: tuple[tuple[str, Status], ...] = (),
    clues: tuple[Clue, ...] = (),
) -> PublicState:
    """Tạo bàn cờ 3x3 chuẩn theo thứ tự đọc sách (row-major): A1..C3 -> biến 1..9[cite: 5, 6]."""
    cells = ["A1", "B1", "C1", "A2", "B2", "C2", "A3", "B3", "C3"]
    characters = tuple(
        Character(cell=c, name=f"Char_{i}", profession="Villager")
        for i, c in enumerate(cells)
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
    cách gán nào cho các biến phụ để thỏa mãn toàn bộ CNF hay không.
    """
    # Rút gọn mệnh đề dựa trên các biến đã biết giá trị
    simplified: list[list[int]] = []
    for clause in clauses:
        if len(clause) == 0:
            return False  # Mệnh đề rỗng -> UNSAT ngay lập tức
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
                return False  # Mọi literal đều sai -> xung đột
            simplified.append(new_clause)

    def backtrack(cls_list: list[list[int]]) -> bool:
        # Lan truyền đơn vị (Unit Propagation) trên các biến phụ
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

        # Rẽ nhánh trên biến phụ đầu tiên còn lại
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
    """Sinh toàn bộ 2^N tổ hợp chân trị cho N biến chính."""
    for bits in itertools.product([False, True], repeat=num_vars):
        yield {i + 1: bit for i, bit in enumerate(bits)}


def assert_stats_consistent(res):
    """Kiểm tra tính nhất quán của siêu dữ liệu biến và mệnh đề trả về[cite: 4, 6]."""
    assert res.num_primary_vars == 9
    assert res.num_aux_vars >= 0
    assert res.total_vars == res.num_primary_vars + res.num_aux_vars
    assert res.num_clauses == len(res.clauses)
    assert res.primary_vars == set(range(1, 10))
    # Đảm bảo mọi biến xuất hiện trong clauses đều nằm trong [1, total_vars][cite: 6]
    for clause in res.clauses:
        for lit in clause:
            assert 1 <= abs(lit) <= res.total_vars


# =====================================================================
# 1. KIỂM TRA VÉT CẠN EXACTLY, AT_LEAST, AT_MOST (BAO GỒM BIÊN & CỰC TRỊ)
# =====================================================================

@pytest.mark.parametrize(
    "region, var_ids",
    [
        ((), ()),                                           # Vùng rỗng (0 ô)
        (("B2",), (5,)),                                    # Vùng 1 ô
        (("A1", "B1", "C1"), (1, 2, 3)),                    # Vùng 3 ô (1 hàng)
        (("A1", "B1", "A2", "B2", "C2"), (1, 2, 4, 5, 6)),  # Vùng 5 ô
    ],
)
@pytest.mark.parametrize("kind", ["EXACTLY", "AT_LEAST", "AT_MOST"])
@pytest.mark.parametrize("count", [-1, 0, 1, 2, 3, 5, 6])
def test_cardinality_exhaustive(region, var_ids, kind, count):
    clue = Clue(id="card_test", kind=kind, cells=region, count=count)
    res = encode(make_3x3_state(clues=(clue,)))
    assert_stats_consistent(res)

    for assign in all_assignments(9):
        criminal_count = sum(1 for vid in var_ids if assign[vid] is True)
        if kind == "EXACTLY":
            expected = criminal_count == count
        elif kind == "AT_LEAST":
            expected = criminal_count >= count
        else:
            expected = criminal_count <= count

        actual = is_cnf_sat_under_primary(res.clauses, assign)
        assert actual == expected, (
            f"Sai lệch tại kind={kind}, region={region}, count={count}, "
            f"criminal_count={criminal_count}: CNF={actual} != Semantic={expected}"
        )


# =====================================================================
# 2. KIỂM TRA VÉT CẠN ODD & EVEN (VÙNG RỖNG, 1 Ô, NHIỀU Ô)
# =====================================================================

@pytest.mark.parametrize(
    "region, var_ids",
    [
        ((), ()),                                           # Vùng rỗng (0 tội phạm -> chẵn)[cite: 4]
        (("C3",), (9,)),                                    # Vùng 1 ô
        (("A1", "C3"), (1, 9)),                             # Vùng 2 ô
        (("A1", "B1", "C1"), (1, 2, 3)),                    # Vùng 3 ô
        (("A1", "B1", "C1", "A2", "B2"), (1, 2, 3, 4, 5)),  # Vùng 5 ô
    ],
)
@pytest.mark.parametrize("kind", ["ODD", "EVEN"])
def test_parity_exhaustive(region, var_ids, kind):
    clue = Clue(id="parity_test", kind=kind, cells=region)
    res = encode(make_3x3_state(clues=(clue,)))
    assert_stats_consistent(res)

    for assign in all_assignments(9):
        criminal_count = sum(1 for vid in var_ids if assign[vid] is True)
        expected = (criminal_count % 2 == 1) if kind == "ODD" else (criminal_count % 2 == 0)

        actual = is_cnf_sat_under_primary(res.clauses, assign)
        assert actual == expected, (
            f"Sai lệch tại kind={kind}, region={region}, "
            f"criminal_count={criminal_count}: CNF={actual} != Semantic={expected}"
        )


# =====================================================================
# 3. KIỂM TRA KHÔNG ĐẢO NGƯỢC LẠI KHI target_status LÀ INNOCENT
# =====================================================================

def test_innocent_target_already_normalized_by_loader():
    """
    Loader đã quy đổi sẵn '1 innocent trong 3 ô' thành 'EXACTLY 2 criminals',
    nhưng vẫn giữ target_status=INNOCENT để UI hiển thị câu chữ[cite: 3, 4, 5].
    Encoder KHÔNG được phép đảo ngược lại lần nữa[cite: 3, 4, 5].
    """
    clue = Clue(
        id="norm_test",
        kind="EXACTLY",
        cells=("A1", "B1", "C1"),
        count=2,
        target_status=Status.INNOCENT,
    )
    res = encode(make_3x3_state(clues=(clue,)))
    assert_stats_consistent(res)

    for assign in all_assignments(9):
        # Phải ép đúng 2 criminals (tức là 1 innocent), không phải 2 innocents[cite: 4, 5]
        expected = sum(1 for vid in (1, 2, 3) if assign[vid]) == 2
        assert is_cnf_sat_under_primary(res.clauses, assign) == expected


# =====================================================================
# 4. KIỂM TRA KẾT HỢP NHIỀU RÀNG BUỘC DÙNG BIẾN PHỤ CÙNG LÚC (KHÔNG XUNG ĐỘT ID)
# =====================================================================

def test_multiple_aux_clues_do_not_collide():
    """Đảm bảo hai manh mối liên tiếp cấp phát ID biến phụ tách biệt, không đè lên nhau[cite: 4]."""
    c1 = Clue(id="m1", kind="EXACTLY", cells=("A1", "B1", "C1"), count=2)
    c2 = Clue(id="m2", kind="ODD", cells=("A1", "A2", "A3"))
    c3 = Clue(id="m3", kind="AT_MOST", cells=("B1", "B2", "B3", "C3"), count=1)

    res = encode(make_3x3_state(clues=(c1, c2, c3)))
    assert_stats_consistent(res)
    assert res.num_aux_vars > 0

    for assign in all_assignments(9):
        cond1 = sum(1 for v in (1, 2, 3) if assign[v]) == 2
        cond2 = (sum(1 for v in (1, 4, 7) if assign[v]) % 2) == 1
        cond3 = sum(1 for v in (2, 5, 8, 9) if assign[v]) <= 1
        expected = cond1 and cond2 and cond3

        assert is_cnf_sat_under_primary(res.clauses, assign) == expected


# =====================================================================
# 5. KIỂM TRA ĐẦU VÀO KHÔNG HỢP LỆ[cite: 4]
# =====================================================================

@pytest.mark.parametrize("kind", ["EXACTLY", "AT_LEAST", "AT_MOST"])
def test_cardinality_missing_count_raises(kind):
    clue = Clue(id="bad_card", kind=kind, cells=("A1", "B1"), count=None)
    with pytest.raises(ValueError):
        encode(make_3x3_state(clues=(clue,)))