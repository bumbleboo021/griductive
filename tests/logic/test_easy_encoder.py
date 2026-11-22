import itertools
import pytest

from griductive.domain.models import Character, Clue, PublicState, Status
from griductive.logic.encoder import encode


def make_3x3_state(
    verdicts: tuple[tuple[str, Status], ...] = (),
    clues: tuple[Clue, ...] = (),
) -> PublicState:
    """Tạo bàn cờ 3x3 chuẩn theo thứ tự đọc sách (row-major): A1..C3 -> biến 1..9."""
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


def eval_cnf(clauses: list[list[int]] | tuple[tuple[int, ...], ...], assignment: dict[int, bool]) -> bool:
    """Đánh giá công thức CNF với một bộ gán chân trị cho trước (True = Criminal, False = Innocent)."""
    for clause in clauses:
        # Một clause đúng nếu có ít nhất 1 literal đúng
        clause_satisfied = False
        for lit in clause:
            var = abs(lit)
            val = assignment[var]
            if (lit > 0 and val) or (lit < 0 and not val):
                clause_satisfied = True
                break
        if not clause_satisfied:
            return False
    return True


def all_assignments(num_vars: int):
    """Sinh toàn bộ 2^N tổ hợp chân trị cho N biến chính."""
    for bits in itertools.product([False, True], repeat=num_vars):
        yield {i + 1: bit for i, bit in enumerate(bits)}


# =====================================================================
# 1. KIỂM TRA ÁNH XẠ BIẾN & TRẠNG THÁI RỖNG
# =====================================================================

def test_empty_state_and_variable_mapping():
    state = make_3x3_state()
    res = encode(state)

    assert res.num_primary_vars == 9
    assert res.num_aux_vars == 0
    assert res.total_vars == 9
    assert res.num_clauses == 0
    assert len(res.clauses) == 0
    assert res.primary_vars == {1, 2, 3, 4, 5, 6, 7, 8, 9}

    # Kiểm tra thứ tự row-major (A1=1, B1=2, C1=3, A2=4, ..., C3=9)
    assert res.cell_to_var["A1"] == 1
    assert res.cell_to_var["C1"] == 3
    assert res.cell_to_var["A2"] == 4
    assert res.cell_to_var["C3"] == 9
    assert res.var_to_cell[1] == "A1"
    assert res.var_to_cell[9] == "C3"


# =====================================================================
# 2. KIỂM TRA VERDICTS & QUOTE
# =====================================================================

def test_public_verdicts_and_quote():
    verdicts = (
        ("A1", Status.CRIMINAL),  # +1
        ("B2", Status.INNOCENT),  # -5
    )
    quote_clue = Clue(id="q1", kind="QUOTE", cells=())
    state = make_3x3_state(verdicts=verdicts, clues=(quote_clue,))
    res = encode(state)

    assert res.num_aux_vars == 0
    # QUOTE không tạo thêm mệnh đề nào, chỉ có 2 unit clauses từ verdicts
    assert res.num_clauses == 2

    for assign in all_assignments(9):
        expected = (assign[1] is True) and (assign[5] is False)
        assert eval_cnf(res.clauses, assign) == expected


# =====================================================================
# 3. KIỂM TRA FACT
# =====================================================================

@pytest.mark.parametrize(
    "cell, var_id, status, expected_bool",
    [
        ("A1", 1, Status.CRIMINAL, True),
        ("C3", 9, Status.INNOCENT, False),
    ],
)
def test_fact_clue(cell, var_id, status, expected_bool):
    clue = Clue(id="f1", kind="FACT", cells=(cell,), status=status)
    res = encode(make_3x3_state(clues=(clue,)))

    assert res.num_clauses == 1
    assert res.num_aux_vars == 0

    for assign in all_assignments(9):
        expected = assign[var_id] is expected_bool
        assert eval_cnf(res.clauses, assign) == expected


# =====================================================================
# 4. KIỂM TRA SAME & DIFFERENT (ĐỐI CHIẾU BẢNG CHÂN TRỊ VÉT CẠN)
# =====================================================================

def test_same_clue_exhaustive():
    # A1 (var 1) và C2 (var 6) cùng trạng thái
    clue = Clue(id="s1", kind="SAME", cells=("A1", "C2"))
    res = encode(make_3x3_state(clues=(clue,)))

    assert res.num_aux_vars == 0
    for assign in all_assignments(9):
        expected = assign[1] == assign[6]
        assert eval_cnf(res.clauses, assign) == expected


def test_different_clue_exhaustive():
    # B1 (var 2) và A3 (var 7) khác trạng thái
    clue = Clue(id="d1", kind="DIFFERENT", cells=("B1", "A3"))
    res = encode(make_3x3_state(clues=(clue,)))

    assert res.num_aux_vars == 0
    for assign in all_assignments(9):
        expected = assign[2] != assign[7]
        assert eval_cnf(res.clauses, assign) == expected


# =====================================================================
# 5. KIỂM TRA IMPLIES (ĐỦ 4 TỔ HỢP TRẠNG THÁI & TÍNH BẤT ĐỐI XỨNG)
# =====================================================================

@pytest.mark.parametrize(
    "ant_status, ant_bool, cons_status, cons_bool",
    [
        (Status.CRIMINAL, True, Status.CRIMINAL, True),
        (Status.CRIMINAL, True, Status.INNOCENT, False),
        (Status.INNOCENT, False, Status.CRIMINAL, True),
        (Status.INNOCENT, False, Status.INNOCENT, False),
    ],
)
def test_implies_all_combinations(ant_status, ant_bool, cons_status, cons_bool):
    # A1 (var 1) là tiền đề -> B1 (var 2) là kết luận
    clue = Clue(
        id="imp1",
        kind="IMPLIES",
        cells=("A1", "B1"),
        antecedent_status=ant_status,
        consequent_status=cons_status,
    )
    res = encode(make_3x3_state(clues=(clue,)))

    assert res.num_clauses == 1
    assert res.num_aux_vars == 0

    for assign in all_assignments(9):
        premise = assign[1] is ant_bool
        conclusion = assign[2] is cons_bool
        # P => Q tương đương (not P) or Q
        expected = (not premise) or conclusion
        assert eval_cnf(res.clauses, assign) == expected


# =====================================================================
# 6. KIỂM TRA ĐẦU VÀO KHÔNG HỢP LỆ (DEFENSIVE CHECKS)
# =====================================================================

def test_invalid_inputs_raise_error():
    # FACT thiếu status
    with pytest.raises(ValueError):
        encode(make_3x3_state(clues=(Clue(id="bad1", kind="FACT", cells=("A1",), status=None),)))

    # SAME không đủ 2 ô
    with pytest.raises(ValueError):
        encode(make_3x3_state(clues=(Clue(id="bad2", kind="SAME", cells=("A1",)),)))

    # IMPLIES thiếu trạng thái vế sau
    with pytest.raises(ValueError):
        encode(
            make_3x3_state(
                clues=(
                    Clue(
                        id="bad3",
                        kind="IMPLIES",
                        cells=("A1", "B1"),
                        antecedent_status=Status.CRIMINAL,
                        consequent_status=None,
                    ),
                )
            )
        )

    # Loại clue lạ chưa hỗ trợ phải báo lỗi
    with pytest.raises((ValueError, NotImplementedError)):
        encode(make_3x3_state(clues=(Clue(id="bad4", kind="UNKNOWN_TEMPLATE", cells=("A1",)),)))