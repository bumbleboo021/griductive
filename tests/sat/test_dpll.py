"""Bộ kiểm thử đơn vị và đối chiếu bảng chân trị cho bộ giải DPLL SAT."""
import itertools
import random

from griductive.sat.dpll import SatResult, solve


def _is_model_valid(
    clauses: list[list[int]] | tuple[tuple[int, ...], ...],
    assumptions: list[int] | tuple[int, ...],
    model: dict[int, bool],
) -> bool:
    for lit in assumptions:
        val = model[abs(lit)]
        if (lit > 0 and not val) or (lit < 0 and val):
            return False
    for clause in clauses:
        if not any((model[abs(lit)] if lit > 0 else not model[abs(lit)]) for lit in clause):
            return False
    return True


def _truth_table_is_sat(
    clauses: list[tuple[int, ...]],
    total_vars: int,
    assumptions: tuple[int, ...] = (),
) -> bool:
    for bits in itertools.product((False, True), repeat=total_vars):
        model = {idx + 1: bit for idx, bit in enumerate(bits)}
        if _is_model_valid(clauses, assumptions, model):
            return True
    return False


def _pigeonhole_cnf(pigeons: int, holes: int) -> tuple[int, list[tuple[int, ...]]]:
    """Sinh công thức UNSAT bài toán chuồng bồ câu PHP(pigeons, holes) khi pigeons > holes."""
    def var(p: int, h: int) -> int:
        return p * holes + h + 1

    clauses: list[tuple[int, ...]] = []
    # Mỗi con chim phải ở trong ít nhất một chuồng.
    for p in range(pigeons):
        clauses.append(tuple(var(p, h) for h in range(holes)))
    # Không có hai con chim nào nằm chung một chuồng.
    for h in range(holes):
        for p1 in range(pigeons):
            for p2 in range(p1 + 1, pigeons):
                clauses.append((-var(p1, h), -var(p2, h)))
    return pigeons * holes, clauses


def test_edge_cases_empty_and_contradictory_units():
    # Công thức rỗng -> SAT ngay, điền False cho toàn bộ biến tự do.
    res_empty_kb = solve(clauses=[], total_vars=3)
    assert isinstance(res_empty_kb, SatResult)
    assert res_empty_kb.is_sat is True
    assert res_empty_kb.is_timeout is False
    assert res_empty_kb.model == {1: False, 2: False, 3: False}
    assert res_empty_kb.decisions == 0
    assert res_empty_kb.backtracks == 0

    # Có mệnh đề rỗng bên trong công thức -> UNSAT ngay.
    res_empty_clause = solve(clauses=[[], [1]], total_vars=1)
    assert res_empty_clause.is_sat is False
    assert res_empty_clause.is_timeout is False
    assert res_empty_clause.model is None
    assert res_empty_clause.decisions == 0

    # Hai mệnh đề đơn vị mâu thuẫn nhau -> UNSAT ngay trong pha lan truyền đơn vị.
    res_conflict_units = solve(clauses=[[1], [-1]], total_vars=1)
    assert res_conflict_units.is_sat is False
    assert res_conflict_units.is_timeout is False
    assert res_conflict_units.model is None
    assert res_conflict_units.decisions == 0


def test_duplicate_literals_and_tautology():
    clauses = [[1, -1, 2], [2, 2]]
    res = solve(clauses=clauses, total_vars=3)
    assert res.is_sat is True
    assert res.is_timeout is False
    assert res.model is not None
    assert set(res.model.keys()) == {1, 2, 3}
    assert res.model[2] is True
    assert _is_model_valid(clauses, (), res.model)


def test_unit_propagation_chain_no_decisions():
    clauses = [[1], [-1, 2], [-2, 3], [-3, -4]]
    res = solve(clauses=clauses, total_vars=4)
    assert res.is_sat is True
    assert res.model == {1: True, 2: True, 3: True, 4: False}
    assert res.decisions == 0
    assert res.propagations == 4
    assert res.backtracks == 0


def test_deterministic_branching_tries_true_before_false():
    res = solve(clauses=[[1, 2]], total_vars=2)
    assert res.is_sat is True
    assert res.model == {1: True, 2: False}
    assert res.decisions == 1
    assert res.backtracks == 0


def test_assumptions_isolation_and_entailment():
    # Ví dụ suy diễn trong tài liệu Project 2 Mục 3.4: KB = (A v B) ^ (-A v B).
    clauses = [[1, 2], [-1, 2]]
    snapshot = [list(c) for c in clauses]

    base = solve(clauses=clauses, total_vars=2, assumptions=())
    assert base.is_sat is True

    # Giả sử B vô tội (-2) -> UNSAT => bắt buộc B phải là tội phạm.
    assume_not_b = solve(clauses=clauses, total_vars=2, assumptions=(-2,))
    assert assume_not_b.is_sat is False
    assert assume_not_b.is_timeout is False
    assert assume_not_b.model is None

    # Giả sử A là tội phạm (1) và vô tội (-1) -> cả hai đều SAT => A vẫn là UNKNOWN.
    assume_a = solve(clauses=clauses, total_vars=2, assumptions=(1,))
    assume_not_a = solve(clauses=clauses, total_vars=2, assumptions=(-1,))
    assert assume_a.is_sat is True and assume_a.model is not None and assume_a.model[1] is True
    assert assume_not_a.is_sat is True and assume_not_a.model is not None and assume_not_a.model[1] is False

    # Hai giả định tự mâu thuẫn nhau.
    both = solve(clauses=clauses, total_vars=2, assumptions=(1, -1))
    assert both.is_sat is False
    assert both.is_timeout is False
    assert both.model is None

    # Công thức gốc không bị thay đổi và gọi lại vẫn cho kết quả giống hệt.
    assert clauses == snapshot
    base_again = solve(clauses=clauses, total_vars=2, assumptions=())
    assert base_again.is_sat is True
    assert base_again.model == base.model


def test_auxiliary_variables_complete_model():
    # Mã hóa Tseitin cho XOR: x3 <-> (x1 xor x2), kèm x3=True và x1=True; biến x4 tự do.
    clauses = (
        (-1, -2, -3),
        (1, 2, -3),
        (1, -2, 3),
        (-1, 2, 3),
        (3,),
        (1,),
    )
    res = solve(clauses=clauses, total_vars=4)
    assert res.is_sat is True
    assert res.model is not None
    assert set(res.model.keys()) == {1, 2, 3, 4}
    assert res.model[1] is True
    assert res.model[2] is False
    assert res.model[3] is True


def test_pigeonhole_unsat_metrics():
    total_vars, clauses = _pigeonhole_cnf(4, 3)
    res = solve(clauses=clauses, total_vars=total_vars)
    assert res.is_sat is False
    assert res.is_timeout is False
    assert res.model is None
    assert res.decisions > 0
    assert res.backtracks > 0
    assert res.propagations > 0
    assert res.runtime >= 0.0


def test_timeout_separated_from_unsat():
    res_zero = solve(clauses=[[1, 2]], total_vars=2, timeout_seconds=0.0)
    assert res_zero.is_timeout is True
    assert res_zero.is_sat is False
    assert res_zero.model is None

    total_vars, clauses = _pigeonhole_cnf(7, 6)
    res_hard = solve(clauses=clauses, total_vars=total_vars, timeout_seconds=0.02)
    assert res_hard.is_timeout is True
    assert res_hard.is_sat is False
    assert res_hard.model is None
    assert res_hard.runtime < 0.5


def test_truth_table_oracle_differential():
    rng = random.Random(20261123)
    for num_vars in range(1, 6):
        for _ in range(35):
            num_clauses = rng.randint(0, num_vars * 4)
            clauses: list[tuple[int, ...]] = []
            for _ in range(num_clauses):
                width = rng.randint(1, min(3, num_vars))
                picked = rng.sample(range(1, num_vars + 1), width)
                clauses.append(tuple(v if rng.choice((True, False)) else -v for v in picked))

            num_assump = rng.randint(0, min(2, num_vars))
            assump_vars = rng.sample(range(1, num_vars + 1), num_assump)
            assumptions = tuple(v if rng.choice((True, False)) else -v for v in assump_vars)

            expected_sat = _truth_table_is_sat(clauses, num_vars, assumptions)
            for heuristic in ("smallest", "jw"):
                res = solve(
                    clauses=clauses,
                    total_vars=num_vars,
                    assumptions=assumptions,
                    heuristic=heuristic,
                )

                assert res.is_sat is expected_sat
                assert res.is_timeout is False
                if expected_sat:
                    assert res.model is not None
                    assert set(res.model.keys()) == set(range(1, num_vars + 1))
                    assert _is_model_valid(clauses, assumptions, res.model)
                else:
                    assert res.model is None

                # Kiểm tra tính xác định khi gọi lặp lại cùng một đầu vào.
                res2 = solve(
                    clauses=clauses,
                    total_vars=num_vars,
                    assumptions=assumptions,
                    heuristic=heuristic,
                )
                assert res2.is_sat is res.is_sat
                assert res2.model == res.model
                assert res2.decisions == res.decisions
                assert res2.propagations == res.propagations
                assert res2.backtracks == res.backtracks


def test_jw_heuristic_branching_and_validation():
    import pytest

    # x2 xuất hiện 3 lần ở cực tính âm (-2) -> J(-2)=0.75 > J(+1)=0.25.
    # JW phải chọn biến 2 trước và thử False trước -> cả 3 mệnh đề SAT ngay sau 1 decision.
    clauses = [[-2, 1], [-2, 3], [-2, 4]]
    res_smallest = solve(clauses=clauses, total_vars=4, heuristic="smallest")
    res_jw = solve(clauses=clauses, total_vars=4, heuristic="jw")
    assert res_smallest.is_sat is True and res_smallest.decisions == 2
    assert res_jw.is_sat is True
    assert res_jw.model is not None
    assert _is_model_valid(clauses, (), res_jw.model)
    assert res_jw.model[2] is False
    assert res_jw.decisions == 1
    assert res_jw.backtracks == 0

    # So sánh với PHP(4,3): cả smallest và jw đều phải kết luận UNSAT.
    total_vars, php_clauses = _pigeonhole_cnf(4, 3)
    php_jw = solve(clauses=php_clauses, total_vars=total_vars, heuristic="jw")
    assert php_jw.is_sat is False
    assert php_jw.is_timeout is False
    assert php_jw.model is None

    # Tham số heuristic không hợp lệ phải báo ValueError rõ ràng.
    with pytest.raises(ValueError):
        solve(clauses=[[1, 2]], total_vars=2, heuristic="unknown_strategy")
