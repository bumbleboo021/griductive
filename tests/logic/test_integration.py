from pathlib import Path
import json
import pytest

from griductive.domain.models import PublicState, Status
from griductive.engine.game import GameEngine
from griductive.engine.puzzle import load_puzzle
from griductive.engine.reference import ReferenceAnalyzer
from griductive.logic.encoder import encode


PUZZLE_FILES = sorted(Path("data/puzzles").rglob("*.json"))


def solve_cnf_with_optional_primary(
    clauses: list[list[int]] | tuple[tuple[int, ...], ...],
    fixed_primary: dict[int, bool] | None = None,
) -> bool:
    """
    Bộ kiểm tra SAT cục bộ (Unit Propagation + phân nhánh theo mệnh đề ngắn nhất)
    dùng để xác minh nghiệm của CNF có chứa biến phụ trên các lưới tới 5x5[cite: 4].
    """
    fixed = fixed_primary or {}
    simplified: list[list[int]] = []

    for clause in clauses:
        if len(clause) == 0:
            return False
        new_clause = []
        satisfied = False
        for lit in clause:
            var = abs(lit)
            if var in fixed:
                val = fixed[var]
                if (lit > 0 and val) or (lit < 0 and not val):
                    satisfied = True
                    break
            else:
                new_clause.append(lit)
        if not satisfied:
            if not new_clause:
                return False
            simplified.append(new_clause)

    def dpll(cls_list: list[list[int]]) -> bool:
        # 1. Lan truyền đơn vị (Unit Propagation)
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

        # 2. Chọn biến từ mệnh đề ngắn nhất để tối ưu tốc độ trên lưới 5x5
        shortest_clause = min(cls_list, key=len)
        pivot = abs(shortest_clause[0])

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
            if not conflict and dpll(next_cls):
                return True
        return False

    return dpll(simplified)


def extract_ground_truth_verdicts(puzzle_path: Path) -> dict[str, Status]:
    """Trích xuất đáp án gốc của từng ô trực tiếp từ tệp JSON của màn chơi."""
    data = json.loads(puzzle_path.read_text(encoding="utf-8"))
    result: dict[str, Status] = {}
    for entry in data["characters"]:
        raw_status = entry["status"]
        result[entry["cell"]] = (
            Status[raw_status] if raw_status in Status.__members__ else Status(raw_status)
        )
    return result


def verify_cnf_result_contract(res, expected_size: int):
    """Kiểm tra tính nhất quán của siêu dữ liệu CNFResult theo hợp đồng API[cite: 4, 6]."""
    expected_n = expected_size * expected_size
    assert res.num_primary_vars == expected_n
    assert res.num_aux_vars >= 0
    assert res.total_vars == res.num_primary_vars + res.num_aux_vars
    assert res.num_clauses == len(res.clauses)
    assert res.primary_vars == set(range(1, expected_n + 1))

    for clause in res.clauses:
        for lit in clause:
            assert 1 <= abs(lit) <= res.total_vars


# =====================================================================
# 1. KIỂM TRA ĐỦ SỐ LƯỢNG 13 MÀN CHƠI GỐC
# =====================================================================

def test_all_13_stages_discovered():
    assert len(PUZZLE_FILES) == 13, (
        f"Kỳ vọng 13 tệp màn chơi trong data/puzzles/, nhưng tìm thấy {len(PUZZLE_FILES)}"
    )


# =====================================================================
# 2. KIỂM THỬ TÍCH HỢP TỪNG BƯỚC GIẢI TRÊN TOÀN BỘ 13 MÀN CHƠI[cite: 3, 4, 5]
# =====================================================================

@pytest.mark.parametrize(
    "puzzle_path",
    PUZZLE_FILES,
    ids=[p.relative_to("data/puzzles").as_posix() for p in PUZZLE_FILES],
)
def test_progressive_encode_across_all_stages(puzzle_path: Path):
    puzzle = load_puzzle(str(puzzle_path))
    ground_truth = extract_ground_truth_verdicts(puzzle_path)

    engine = GameEngine(puzzle, ReferenceAnalyzer())
    snapshots: list[PublicState] = [engine.public_state()]

    # Chạy vòng lặp giải tuần tự bằng ReferenceAnalyzer để thu thập toàn bộ các bước mở thẻ[cite: 5]
    max_steps = puzzle.size * puzzle.size + 5
    for _ in range(max_steps):
        outcome = engine.step()
        snapshots.append(engine.public_state())
        code = getattr(outcome, "code", str(outcome))
        if "SOLVED" in str(code):
            break
    else:
        pytest.fail(f"Màn chơi {puzzle_path} không giải xong sau {max_steps} bước.")

    # Kiểm tra bộ mã hóa CNF của bạn tại MỌI bước tiến triển của màn chơi[cite: 4]
    for step_idx, snap in enumerate(snapshots):
        res_1 = encode(snap)
        res_2 = encode(snap)

        # 1. Tính tái lập (Deterministic encoding)[cite: 4]
        assert res_1.clauses == res_2.clauses
        assert res_1.cell_to_var == res_2.cell_to_var
        assert res_1.num_aux_vars == res_2.num_aux_vars

        # 2. Nhất quán biến & mệnh đề[cite: 4, 6]
        verify_cnf_result_contract(res_1, puzzle.size)

        # 3. Đáp án thật của màn chơi luôn thỏa mãn CNF tại bước hiện tại[cite: 4, 5]
        primary_truth = {
            res_1.cell_to_var[cell]: (status == Status.CRIMINAL)
            for cell, status in ground_truth.items()
        }
        assert solve_cnf_with_optional_primary(res_1.clauses, primary_truth) is True, (
            f"CNF tại bước {step_idx} của {puzzle_path.name} đã loại nhầm đáp án đúng!"
        )

    # 4. Kiểm tra tính duy nhất nghiệm khi mở đủ toàn bộ manh mối (bước cuối cùng)[cite: 3, 4]
    # Tạo bản chụp chỉ giữ lại toàn bộ manh mối (bỏ verdicts đã chốt) để ép CNF tự suy ra toàn bàn cờ
    final_snap = snapshots[-1]
    all_clues_only_state = PublicState(
        size=final_snap.size,
        characters=final_snap.characters,
        verdicts=snapshots[0].verdicts,  # Giữ lại các thẻ mở sẵn ban đầu của màn chơi
        clues=final_snap.clues,
    )
    full_clue_cnf = encode(all_clues_only_state)
    verify_cnf_result_contract(full_clue_cnf, puzzle.size)

    # Chặn đáp án đúng trên các biến chính (loại trừ biến phụ) -> phải ra UNSAT[cite: 4]
    blocking_clause = [
        -full_clue_cnf.cell_to_var[cell] if status == Status.CRIMINAL else full_clue_cnf.cell_to_var[cell]
        for cell, status in ground_truth.items()
    ]
    clauses_with_block = [list(c) for c in full_clue_cnf.clauses] + [blocking_clause]
    assert solve_cnf_with_optional_primary(clauses_with_block) is False, (
        f"CNF đủ manh mối của {puzzle_path.name} vẫn còn nghiệm thứ 2 (thiếu ràng buộc)!"
    )


# =====================================================================
# 3. KIỂM TRA TÍNH ỔN ĐỊNH KHI RESTART MÀN CHƠI[cite: 3, 5]
# =====================================================================

def test_encode_after_engine_restart():
    puzzle = load_puzzle("data/puzzles/5x5/level_05.json")
    engine = GameEngine(puzzle, ReferenceAnalyzer())

    initial_cnf = encode(engine.public_state())
    engine.step()
    engine.step()
    engine.restart()
    restarted_cnf = encode(engine.public_state())

    assert initial_cnf.clauses == restarted_cnf.clauses
    assert initial_cnf.num_aux_vars == restarted_cnf.num_aux_vars
    assert initial_cnf.num_clauses == restarted_cnf.num_clauses

def classify_by_cnf(clauses: tuple[tuple[int, ...], ...], primary_vars: set[int]) -> dict[int, Status]:
    """
    Thực hiện suy diễn phản chứng trên CNF của bạn (giống hệt cơ chế của Person 4)[cite: 4]:
    - Thử thêm [-v] -> UNSAT => CRIMINAL
    - Thử thêm [+v] -> UNSAT => INNOCENT
    - Cả hai đều SAT => UNKNOWN
    """
    result: dict[int, Status] = {}
    for var in sorted(primary_vars):
        can_be_criminal = solve_cnf_with_optional_primary(clauses, {var: True})
        can_be_innocent = solve_cnf_with_optional_primary(clauses, {var: False})

        if not can_be_criminal and not can_be_innocent:
            raise AssertionError(f"KB bị mâu thuẫn (UNSAT) tại biến {var}!")
        elif not can_be_innocent:
            result[var] = Status.CRIMINAL
        elif not can_be_criminal:
            result[var] = Status.INNOCENT
        else:
            result[var] = Status.UNKNOWN
    return result


@pytest.mark.parametrize(
    "puzzle_path",
    PUZZLE_FILES,
    ids=[p.relative_to("data/puzzles").as_posix() for p in PUZZLE_FILES],
)
def test_differential_against_reference_analyzer(puzzle_path: Path):
    """
    Đối chiếu từng nước đi giữa CNF của bạn và ReferenceAnalyzer trên toàn bộ 13 màn chơi.
    Nếu 100% khớp nhau ở mọi bước, bộ mã hóa CNF của bạn đã chuẩn xác tuyệt đối.
    """
    puzzle = load_puzzle(str(puzzle_path))
    ref_analyzer = ReferenceAnalyzer()
    engine = GameEngine(puzzle, ref_analyzer)

    while True:
        snap = engine.public_state()
        ref_analysis = ref_analyzer.analyze(snap)
        assert ref_analysis.consistent is True

        cnf_res = encode(snap)
        cnf_verdicts = classify_by_cnf(cnf_res.clauses, cnf_res.primary_vars)

        # So sánh từng ô chưa mở giữa ReferenceAnalyzer và CNF của bạn
        for cell, expected_status in ref_analysis.verdicts:
            var_id = cnf_res.cell_to_var[cell]
            actual_status = cnf_verdicts[var_id]
            assert actual_status == expected_status, (
                f"[{puzzle_path.name}] Sai lệch suy diễn tại ô {cell}: "
                f"CNF={actual_status} != ReferenceAnalyzer={expected_status}"
            )

        outcome = engine.step()
        if "SOLVED" in str(getattr(outcome, "code", outcome)):
            break